from fastapi import Depends
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    # decode_token raises HTTPException directly on failure
    return decode_token(token)


def get_onboarding_claims(token: str = Depends(oauth2_scheme)) -> OnboardingClaims:
    # decode_onboarding_claims raises HTTPException directly on failure
    return decode_onboarding_claims(token)


def get_onboarding_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    # decode_onboarding_token raises HTTPException directly on failure
    return decode_onboarding_token(token)
