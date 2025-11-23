from __future__ import annotations

from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.role_permission import role_permission_table


class Permission(Base):
    __tablename__ = "permissions"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(128), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    roles: List["Role"] = relationship(
        "Role",
        secondary=role_permission_table,
        back_populates="permissions",
    )

