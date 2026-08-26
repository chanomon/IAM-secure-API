from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.db_models import User, Permission
from core.security import decode_token
import jwt

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependencia para obtener el usuario actual (Autenticación)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar que sea un token de acceso (no refresh)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

# Dependencia para Autorización (RBAC) - OWASP A01
def require_permission(required_permission_name: str):
    """
    Factory que retorna una dependencia que verifica si el usuario tiene un permiso específico.
    Ejemplo: require_permission("users:read")
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Buscar el permiso en la BD
        perm = db.query(Permission).filter(Permission.name == required_permission_name).first()
        if not perm:
            raise HTTPException(status_code=500, detail="Permission not defined in system")
        
        # Verificar si el usuario tiene un rol que contenga este permiso
        has_permission = False
        for role in current_user.roles:
            if perm in role.permissions:
                has_permission = True
                break
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User lacks permission: {required_permission_name}"
            )
        return current_user
    
    return permission_checker
