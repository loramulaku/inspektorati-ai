"""Unit tests for the Pydantic schemas in app.schemas.users (input validation)."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.users import LoginIn, UserCreate, UserOut, UserUpdate


def valid_user(**changes):
    data = {
        "emri": "Agim",
        "mbiemri": "Berisha",
        "email": "agim@example.com",
        "password": "Sekret!123",
        "role": "inspektor",
    }
    data.update(changes)
    return data


def test_valid_user_create():
    user = UserCreate(**valid_user(sektori_id=2, telefoni="044 123 456"))
    assert user.role == "inspektor"
    assert user.sektori_id == 2


def test_email_is_lowercased():
    assert UserCreate(**valid_user(email="Agim@Example.COM")).email == "agim@example.com"
    assert LoginIn(email="Admin@Vushtrri.rks-gov.net", password="x").email == "admin@vushtrri.rks-gov.net"
    assert UserUpdate(email="Ri@Example.com").email == "ri@example.com"


def test_names_are_trimmed_and_cannot_be_empty():
    assert UserCreate(**valid_user(emri="  Agim  ")).emri == "Agim"
    with pytest.raises(ValidationError):
        UserCreate(**valid_user(emri="   "))


@pytest.mark.parametrize("email", ["jo-email", "a@", "@example.com"])
def test_invalid_email_is_rejected(email):
    with pytest.raises(ValidationError):
        UserCreate(**valid_user(email=email))


def test_unknown_role_is_rejected():
    with pytest.raises(ValidationError):
        UserCreate(**valid_user(role="qytetar"))


def test_password_needs_at_least_8_characters():
    with pytest.raises(ValidationError, match="të paktën 8 karaktere"):
        UserCreate(**valid_user(password="Shkurt1"))
    assert UserCreate(**valid_user(password="Tetë8888")).password == "Tetë8888"


def test_password_over_72_bytes_is_rejected_even_if_under_72_characters():
    # "ë" takes 2 bytes in UTF-8: 37 characters = 74 bytes, over bcrypt's limit
    with pytest.raises(ValidationError, match="72 bajte"):
        UserCreate(**valid_user(password="ë" * 37))
    assert UserCreate(**valid_user(password="ë" * 36)).password == "ë" * 36


def test_update_only_contains_fields_that_were_sent():
    update = UserUpdate(emri="Ri", sektori_id=None)
    assert update.model_dump(exclude_unset=True) == {"emri": "Ri", "sektori_id": None}


def test_user_out_never_exposes_the_password_hash():
    row = SimpleNamespace(
        id=1, emri="Arta", mbiemri="Krasniqi", email="a@example.com", role="admin",
        sektori_id=None, telefoni=None, aktiv=True, created_at=None, password_hash="$2b$secret",
    )
    data = UserOut.model_validate(row).model_dump()
    assert "password_hash" not in data
    assert data["role"] == "admin"
