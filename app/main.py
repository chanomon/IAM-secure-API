from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine, Base
from models import db_models, schemas
from core.security import hash_password  # <-- Importar el hash
from api.deps import get_db, require_permission
from api.v1.endpoints import auth  # <-- Importar auth

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IAM-Secure API", version="1.0.0")

# Registrar rutas de autenticación
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# --- Endpoint CREAR USUARIO (con hash real) ---
@app.post("/api/v1/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verificar duplicado
    db_user = db.query(db_models.User).filter(db_models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Crear usuario con contraseña hasheada (OWASP A02)
    hashed = hash_password(user_in.password)
    new_user = db_models.User(email=user_in.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Endpoint LISTAR USUARIOS (Protegido por RBAC) ---
@app.get("/api/v1/users", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(require_permission("users:read"))  # OWASP A01
):
    """
    Solo usuarios con el permiso 'users:read' pueden ver la lista.
    """
    users = db.query(db_models.User).all()
    return users
