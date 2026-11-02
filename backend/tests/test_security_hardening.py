import pytest

from app.security import PasswordPolicyError, validate_password_strength


def test_password_policy_accepts_strong_password():
    validate_password_strength("Secure!Pass2026")


@pytest.mark.parametrize(
    "password",
    [
        "password123",
        "short",
        "NoDigit!!aa",
        "NoSymbol1234",
        "noupper!1234",
        "NOLOWER!1234",
        "A" * 73,
    ],
)
def test_password_policy_rejects_weak_or_overlong_passwords(password):
    with pytest.raises(PasswordPolicyError):
        validate_password_strength(password)
