from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db
from ..models import Node
from ..schemas import NodeCreate
from ..security import get_current_user, require_role

router = APIRouter(prefix="/nodes", tags=["nodes"])

@router.get("/")
async def list_nodes(db=Depends(get_db), user=Depends(get_current_user)):
    return db.query(Node).all()

@router.post("/")
async def create_node(payload: NodeCreate, db=Depends(get_db),
                      user=Depends(require_role("operator"))):
    node = Node(**payload.dict())
    db.add(node); db.commit(); db.refresh(node)
    return node

@router.delete("/{node_id}")
async def delete_node(node_id: int, db=Depends(get_db),
                      user=Depends(require_role("admin"))):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node: raise HTTPException(status_code=404, detail="Node introuvable")
    db.delete(node); db.commit()
    return {"deleted": node_id}