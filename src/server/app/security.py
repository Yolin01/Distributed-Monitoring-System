from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(plain):
    return pwd_context.hash(plain)

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)

def create_refresh_token(username: str):
    """Crée un refresh token valable 7 jours"""
    to_encode = {"sub": username, "type": "refresh"}
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)

async def get_current_user(token=Depends(oauth2_scheme)):
    exc = HTTPException(status_code=401, detail="Token invalide",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, [settings.ALGORITHM])
        if not payload.get("sub") or payload.get("type") != "access":
            raise exc
        return {"sub": payload["sub"], "role": payload.get("role", "viewer")}
    except JWTError:
        raise exc

def require_role(required_role: str):
    ROLES = {"viewer": 0, "operator": 1, "admin": 2}
    async def checker(user=Depends(get_current_user)):
        if ROLES.get(user["role"], -1) < ROLES.get(required_role, 99):
            raise HTTPException(status_code=403, detail="Permissions insuffisantes")
        return user
    return checker