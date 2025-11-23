from __future__ import annotations

from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.role_permission import role_permission_table
from app.models.user_role import user_role_table


class Role(Base):
    __tablename__ = "roles"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    users: List["User"] = relationship(
        "User",
        secondary=user_role_table,
        back_populates="roles",
    )
    permissions: List["Permission"] = relationship(
        "Permission",
        secondary=role_permission_table,
        back_populates="roles",
    )

