from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import json

from ..database import get_db
from ..models import Metric, Node
from ..security import get_current_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def list_metrics(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    node_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(Metric).order_by(Metric.timestamp.desc())
    if node_id:
        query = query.filter(Metric.node_id == node_id)
    return query.offset(offset).limit(limit).all()


@router.get("/latest")
async def latest_metrics(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    nodes = db.query(Node).all()
    result = []
    for node in nodes:
        latest = (
            db.query(Metric)
            .filter(Metric.node_id == node.id)
            .order_by(Metric.timestamp.desc())
            .first()
        )
        result.append({"node": node, "latest_metric": latest})
    return result


@router.get("/node/{node_id}")
async def node_metrics(
    node_id: int,
    minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(minutes=minutes)
    return (
        db.query(Metric)
        .filter(
            Metric.node_id == node_id,
            Metric.timestamp >= since
        )
        .order_by(Metric.timestamp.asc())
        .all()
    )


@router.get("/node/{node_id}/stats")
async def node_stats(
    node_id: int,
    minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(minutes=minutes)
    stats = db.query(
        func.avg(Metric.cpu_percent).label("cpu_avg"),
        func.min(Metric.cpu_percent).label("cpu_min"),
        func.max(Metric.cpu_percent).label("cpu_max"),
        func.avg(Metric.memory_percent).label("memory_avg"),
        func.min(Metric.memory_percent).label("memory_min"),
        func.max(Metric.memory_percent).label("memory_max"),
        func.avg(Metric.disk_percent).label("disk_avg"),
        func.count(Metric.id).label("total_records"),
    ).filter(
        Metric.node_id == node_id,
        Metric.timestamp >= since
    ).first()

    return {
        "node_id": node_id,
        "cpu_avg": round(stats.cpu_avg or 0, 2),
        "cpu_min": round(stats.cpu_min or 0, 2),
        "cpu_max": round(stats.cpu_max or 0, 2),
        "memory_avg": round(stats.memory_avg or 0, 2),
        "memory_min": round(stats.memory_min or 0, 2),
        "memory_max": round(stats.memory_max or 0, 2),
        "disk_avg": round(stats.disk_avg or 0, 2),
        "total_records": stats.total_records or 0,
    }


@router.get("/live")
async def live_metrics(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    async def event_stream():
        while True:
            nodes = db.query(Node).all()
            data = []
            for node in nodes:
                latest = (
                    db.query(Metric)
                    .filter(Metric.node_id == node.id)
                    .order_by(Metric.timestamp.desc())
                    .first()
                )
                if latest:
                    data.append({
                        "node_id": node.id,
                        "node_name": node.name,
                        "cpu_percent": latest.cpu_percent,
                        "memory_percent": latest.memory_percent,
                        "disk_percent": latest.disk_percent,
                        "timestamp": latest.timestamp.isoformat(),
                    })
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )