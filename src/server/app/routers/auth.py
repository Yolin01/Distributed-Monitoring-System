from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from ..database import get_db
from ..models import User
from ..security import verify_password, create_access_token, create_refresh_token
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(form=Depends(OAuth2PasswordRequestForm), db=Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    access  = create_access_token({"sub": user.username, "role": user.role})
    refresh = create_refresh_token(user.username)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.post("/refresh")
async def refresh(refresh_token: str, db=Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, [settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token invalide")
        user = db.query(User).filter(User.username == payload["sub"]).first()
        return {"access_token": create_access_token({"sub": user.username, "role": user.role}),
                "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expiré")