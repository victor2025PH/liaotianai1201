from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User


def get_user_by_email(db: Session, *, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_superuser: bool = False,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_role(db: Session, *, name: str, description: Optional[str] = None) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name, description=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def assign_role_to_user(db: Session, *, user: User, role: Role) -> None:
    if role not in user.roles:
        user.roles.append(role)
        db.add(user)
        db.commit()
        db.refresh(user)


def get_user_by_id(db: Session, *, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def update_user(
    db: Session,
    *,
    user: User,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
) -> User:
    if email is not None:
        user.email = email
    if full_name is not None:
        user.full_name = full_name
    if is_active is not None:
        user.is_active = is_active
    if is_superuser is not None:
        user.is_superuser = is_superuser
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_password(db: Session, *, user: User, new_password: str) -> User:
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, *, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
