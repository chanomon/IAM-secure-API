from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Tablas asociativas
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # Audit JSON: Guardamos metadatos del usuario (ej: last_login, device_info)
    metadata_json = Column(JSON, default=dict)
    
    roles = relationship('Role', secondary=user_roles, back_populates='users')

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Ej: "read_users"
    resource = Column(String, nullable=False)           # Ej: "users"
    action = Column(String, nullable=False)             # Ej: "read"
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
