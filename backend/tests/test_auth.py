import pytest

import auth


def test_password_hash_round_trip_and_salt():
    first = auth.hash_password("Correct horse battery 42!")
    second = auth.hash_password("Correct horse battery 42!")
    assert first != second
    assert auth.verify_password("Correct horse battery 42!", first)
    assert not auth.verify_password("wrong password", first)


def test_password_policy_rejects_short_password():
    with pytest.raises(ValueError, match="12 characters"):
        auth.hash_password("short")


def test_access_token_requires_configured_secret(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: type("Settings", (), {"jwt_secret_key": "too-short", "jwt_access_token_minutes": 30})(),
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth.create_access_token("admin")


def test_role_allowlist_rejects_unknown_role():
    with pytest.raises(ValueError, match="role allowlist"):
        auth.require_roles("superuser")


def test_access_token_contains_subject_and_expiration(monkeypatch):
    import jwt

    secret = "test-secret-value-with-at-least-32-characters"
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: type("Settings", (), {"jwt_secret_key": secret, "jwt_access_token_minutes": 30})(),
    )
    token = auth.create_access_token("demo-user")
    claims = jwt.decode(token, secret, algorithms=["HS256"])
    assert claims["sub"] == "demo-user"
    assert claims["exp"] > claims["iat"]


def test_access_token_rejects_placeholder_secret(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "jwt_secret_key": "REPLACE_WITH_UNIQUE_RANDOM_SECRET",
                "jwt_access_token_minutes": 30,
            },
        )(),
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth.create_access_token("admin")
