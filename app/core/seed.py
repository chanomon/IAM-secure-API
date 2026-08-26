from core.database import SessionLocal
from models.db_models import Permission, Role

def init_permissions():
    db = SessionLocal()
    
    # Crear permisos base
    perms = [
        {"name": "users:read", "resource": "users", "action": "read"},
        {"name": "users:write", "resource": "users", "action": "write"},
        {"name": "users:delete", "resource": "users", "action": "delete"},
        {"name": "roles:read", "resource": "roles", "action": "read"},
    ]
    
    for p in perms:
        exists = db.query(Permission).filter(Permission.name == p["name"]).first()
        if not exists:
            new_perm = Permission(**p)
            db.add(new_perm)
    
    # Crear rol "Admin" y asignarle todos los permisos
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if not admin_role:
        admin_role = Role(name="Admin", description="Super admin")
        db.add(admin_role)
        db.flush()
        
        all_perms = db.query(Permission).all()
        admin_role.permissions = all_perms
        
    db.commit()
    db.close()
    print("✅ Permisos y roles iniciales creados.")
