import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException

# Coordinate these values with the auth developer
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "PLACEHOLDER_REPLACE_WITH_AUTH_DEV_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# The JWT payload field that holds the user's UUID.
USER_ID_CLAIM = "sub"

ONBOARDING_TOKEN_TYPE = "onboarding"
ONBOARDING_TOKEN_EXPIRE_MINUTES = 15


def decode_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    raw_id = payload.get(USER_ID_CLAIM)
    if raw_id is None:
        raise HTTPException(
            status_code=401,
            detail=f"Token missing '{USER_ID_CLAIM}' claim",
        )

    try:
        return UUID(str(raw_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Token contains invalid user ID")


def create_onboarding_token(user_id: UUID, phone_number: str, country_code: str) -> str:
    payload = {
        "sub": str(user_id),
        "phone_number": phone_number,
        "country_code": country_code,
        "token_type": ONBOARDING_TOKEN_TYPE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ONBOARDING_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@dataclass
class OnboardingClaims:
    user_id: UUID
    phone_number: str
    country_code: str


def decode_onboarding_token(token: str) -> UUID:
    """Validate onboarding token and return just the user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Onboarding token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid onboarding token")

    if payload.get("token_type") != ONBOARDING_TOKEN_TYPE:
        raise HTTPException(
            status_code=401,
            detail="Invalid token type — onboarding token required",
        )

    raw_id = payload.get(USER_ID_CLAIM)
    if raw_id is None:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

    try:
        return UUID(str(raw_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Token contains invalid user ID")


def decode_onboarding_claims(token: str) -> OnboardingClaims:
    """Validate onboarding token and return full claims (user_id + phone + country)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Onboarding token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid onboarding token")

    if payload.get("token_type") != ONBOARDING_TOKEN_TYPE:
        raise HTTPException(
            status_code=401,
            detail="Invalid token type — onboarding token required",
        )

    raw_id = payload.get(USER_ID_CLAIM)
    if raw_id is None:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

    try:
        user_id = UUID(str(raw_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Token contains invalid user ID")

    return OnboardingClaims(
        user_id=user_id,
        phone_number=payload.get("phone_number", ""),
        country_code=payload.get("country_code", ""),
    )
