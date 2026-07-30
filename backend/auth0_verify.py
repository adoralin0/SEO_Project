"""Verify Auth0 ID tokens via JWKS."""

from functools import lru_cache

import jwt
from flask import current_app
from jwt import PyJWKClient


class Auth0Error(Exception):
    pass


@lru_cache(maxsize=1)
def _jwks_client(domain: str) -> PyJWKClient:
    return PyJWKClient(f"https://{domain}/.well-known/jwks.json")


def auth0_configured() -> bool:
    return bool(
        current_app.config.get("AUTH0_DOMAIN")
        and current_app.config.get("AUTH0_CLIENT_ID")
    )


def verify_auth0_id_token(token: str) -> dict:
    domain = current_app.config.get("AUTH0_DOMAIN") or ""
    client_id = current_app.config.get("AUTH0_CLIENT_ID") or ""
    if not domain or not client_id:
        raise Auth0Error("Auth0 is not configured on the server.")

    try:
        signing_key = _jwks_client(domain).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=f"https://{domain}/",
        )
    except jwt.PyJWTError as exc:
        raise Auth0Error(f"Invalid Auth0 token: {exc}") from exc

    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise Auth0Error("Auth0 token is missing an email claim. Enable email scope.")
    if payload.get("email_verified") is False:
        raise Auth0Error("Email is not verified with the identity provider.")

    return payload
