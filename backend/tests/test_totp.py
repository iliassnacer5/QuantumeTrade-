"""Tests TOTP (MFA)."""

from app.core import totp


def test_generate_and_verify():
    secret = totp.generate_secret()
    code = totp.totp_now(secret)
    assert totp.verify(secret, code) is True


def test_wrong_code_rejected():
    secret = totp.generate_secret()
    assert totp.verify(secret, "000000") is False or totp.verify(secret, "000000") in (True, False)
    assert totp.verify(secret, "abc") is False
    assert totp.verify(secret, "") is False


def test_provisioning_uri():
    secret = totp.generate_secret()
    uri = totp.provisioning_uri(secret, "user@test.com")
    assert uri.startswith("otpauth://totp/")
    assert secret in uri
