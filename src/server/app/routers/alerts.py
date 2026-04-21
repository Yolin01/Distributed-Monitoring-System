from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Alert
from ..security import get_current_user, require_role

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
async def list_alerts(db=Depends(get_db), user=Depends(get_current_user)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(50).all()

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int,
                       db=Depends(get_db),
                       user=Depends(require_role("admin"))):
    # suppression : admin uniquement
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    db.delete(alert)
    db.commit()
    return {"deleted": alert_id}