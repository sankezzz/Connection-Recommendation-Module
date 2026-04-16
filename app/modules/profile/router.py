from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.dependencies import get_db, get_current_user_id, get_onboarding_user_id, get_onboarding_claims
from app.core.security.jwt_handler import OnboardingClaims
from app.modules.profile.schemas import (
    ProfileCreate,
    ProfileUpdate,
    UserCreate,
    VerifyProfileRequest,
)
from app.modules.profile.service import (
    create_user,
    create_profile,
    get_my_profile,
    get_profile_by_id,
    delete_profile,
    update_profile,
    submit_verification,
    ProfileConflictError,
    ProfileNotFoundError,
    ProfileValidationError,
    UserConflictError,
)
from app.shared.utils.response import ok

router = APIRouter(prefix="/profile", tags=["Profile"])


# ---------------------------------------------------------------------------
# Step 1 — create user row (called right after OTP verification)
# ---------------------------------------------------------------------------

@router.post("/user", status_code=201)
def create_user_api(
    db: Session = Depends(get_db),
    claims: OnboardingClaims = Depends(get_onboarding_claims),
):
    payload = UserCreate(phone_number=claims.phone_number, country_code=claims.country_code)
    try:
        result = create_user(db, claims.user_id, payload)
        return ok(result, "User created successfully")
    except UserConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ---------------------------------------------------------------------------
# Step 2 — create profile (screens 3 + 4 + 5 combined)
# ---------------------------------------------------------------------------

@router.post("/")
def create_profile_api(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_onboarding_user_id),
):
    try:
        result = create_profile(db, current_user_id, payload)
        return ok(result, "Profile created successfully")
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProfileConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ProfileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Step 3 — verification (screen 6, optional)
# ---------------------------------------------------------------------------

@router.post("/verify")
def verify_profile_api(
    payload: VerifyProfileRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    try:
        result = submit_verification(db, current_user_id, payload)
        return ok(result, "Documents submitted for verification")
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProfileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# My profile
# ---------------------------------------------------------------------------

@router.get("/me")
def get_my_profile_api(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    try:
        result = get_my_profile(db, current_user_id)
        return ok(result, "Profile fetched successfully")
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/")
def update_profile_api(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    try:
        result = update_profile(db, current_user_id, payload)
        return ok(result, "Profile updated successfully")
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProfileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/")
def delete_profile_api(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    try:
        delete_profile(db, current_user_id)
        return ok(message="Profile deleted successfully")
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Public profile view (keep below /me and /verify to avoid path clashes)
# ---------------------------------------------------------------------------

@router.get("/{profile_id}")
def get_profile_api(
    profile_id: int,
    db: Session = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    try:
        result = get_profile_by_id(db, profile_id)
        return ok(result, "Profile fetched successfully")
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
