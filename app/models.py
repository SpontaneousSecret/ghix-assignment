from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    User model for authentication and authorization.
    Supports JWT-based authentication with bcrypt password hashing.
    """
    __tablename__ = 'users'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication Fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    relocation_plans: Mapped[List["RelocationPlan"]] = relationship(
        "RelocationPlan",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="RelocationPlan.generated_at.desc()"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding password_hash)."""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class RelocationPlan(db.Model):
    """
    RelocationPlan model for storing career relocation plan submissions.
    Each submission creates a NEW row (full history tracking).
    Stores both the generated plan and data confidence flags as JSON strings.
    """
    __tablename__ = 'relocation_plans'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Input Parameters
    origin: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    salary_expectation: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default='USD')
    timeline_months: Mapped[int] = mapped_column(Integer, nullable=False)
    work_auth_constraint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Generated Plan Data
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Stores JSON string with structure:
    # {
    #   "eligibility": {...},
    #   "timeline": {...},
    #   "salary_analysis": {...},
    #   "narrative": "...",
    #   "warnings": [...]
    # }

    data_confidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Stores JSON string with structure:
    # {
    #   "salary_data_available": true/false,
    #   "timeline_data_available": true/false,
    #   "visa_data_available": true/false,
    #   "overall_confidence": "high"/"medium"/"low"
    # }

    # Timestamp
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="relocation_plans")

    # Composite index for common queries
    __table_args__ = (
        Index('idx_user_destination_generated', 'user_id', 'destination', 'generated_at'),
        Index('idx_user_generated', 'user_id', 'generated_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<RelocationPlan(id={self.id}, user_id={self.user_id}, "
            f"origin='{self.origin}', destination='{self.destination}', "
            f"generated_at='{self.generated_at}')>"
        )

    def to_dict(self, include_plan: bool = True) -> dict:
        """
        Convert relocation plan to dictionary.

        Args:
            include_plan: If True, includes full plan_json and data_confidence_json

        Returns:
            Dictionary representation of the relocation plan
        """
        import json

        base_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'origin': self.origin,
            'destination': self.destination,
            'target_role': self.target_role,
            'salary_expectation': self.salary_expectation,
            'currency': self.currency,
            'timeline_months': self.timeline_months,
            'work_auth_constraint': self.work_auth_constraint,
            'generated_at': self.generated_at.isoformat()
        }

        if include_plan:
            base_dict['plan'] = json.loads(self.plan_json)
            base_dict['data_confidence'] = json.loads(self.data_confidence_json)

        return base_dict

    def to_summary_dict(self) -> dict:
        """Convert to summary dictionary (without full plan JSON)."""
        return self.to_dict(include_plan=False)
