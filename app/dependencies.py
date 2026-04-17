from typing import Optional

from fastapi import Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database.session import SessionLocal
from app.core.security.jwt_handler import (
    OnboardingClaims,
    decode_token,
    decode_onboarding_token,
    decode_onboarding_claims,
)

# auto_error=False so missing token doesn't immediately raise 401 —
# the dependency functions below handle the fallback to query params.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(
    token: Optional[str] = Depends(oauth2_scheme),
    user_id: Optional[UUID] = Query(default=None, description="[DEV] user UUID, used when no bearer token is provided"),
) -> UUID:
    if token:
        return decode_token(token)
    if user_id:
        return user_id
    raise HTTPException(status_code=401, detail="Not authenticated — provide a bearer token or ?user_id=<uuid>")


def get_onboarding_claims(
    token: Optional[str] = Depends(oauth2_scheme),
    user_id: Optional[UUID] = Query(default=None, description="[DEV] user UUID"),
    phone_number: Optional[str] = Query(default=None, description="[DEV] phone number"),
    country_code: Optional[str] = Query(default=None, description="[DEV] country code"),
) -> OnboardingClaims:
    if token:
        return decode_onboarding_claims(token)
    if user_id and phone_number and country_code:
        return OnboardingClaims(user_id=user_id, phone_number=phone_number, country_code=country_code)
    raise HTTPException(status_code=401, detail="Not authenticated — provide a bearer token or ?user_id=&phone_number=&country_code=")


def get_onboarding_user_id(
    token: Optional[str] = Depends(oauth2_scheme),
    user_id: Optional[UUID] = Query(default=None, description="[DEV] user UUID, used when no bearer token is provided"),
) -> UUID:
    if token:
        return decode_onboarding_token(token)
    if user_id:
        return user_id
    raise HTTPException(status_code=401, detail="Not authenticated — provide a bearer token or ?user_id=<uuid>")
