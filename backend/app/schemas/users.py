"""Pydantic schemas for staff users and authentication.

They validate what the API receives and shape what it sends back
(password hashes are never included in responses).
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator

Role = Literal["inspektor", "drejtor", "admin"]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)]


def _check_password(value):
    # bcrypt only uses the first 72 bytes of a password, so longer ones are refused.
    if len(value) < 8:
        raise ValueError("Fjalëkalimi duhet të ketë të paktën 8 karaktere")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Fjalëkalimi është shumë i gjatë (maksimumi 72 bajte)")
    return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emri: str
    mbiemri: str
    email: str
    role: Role
    sektori_id: int | None
    telefoni: str | None
    aktiv: bool
    created_at: datetime | None


class UserCreate(BaseModel):
    """A new staff user, created by an admin (there is no self-registration)."""

    emri: Name
    mbiemri: Name
    email: EmailStr
    password: str
    role: Role
    sektori_id: int | None = None
    telefoni: Phone | None = None

    check_password = field_validator("password")(_check_password)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value):
        return value.lower()


class UserUpdate(BaseModel):
    emri: Name | None = None
    mbiemri: Name | None = None
    email: EmailStr | None = None
    role: Role | None = None
    sektori_id: int | None = None
    telefoni: Phone | None = None
    aktiv: bool | None = None

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value):
        return value.lower() if value else value


class LoginIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value):
        return value.lower()


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Sektor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emri: str
