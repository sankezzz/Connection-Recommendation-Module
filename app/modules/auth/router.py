import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.modules.auth.schemas import SendOTPRequest, VerifyOTPRequest, VerifyOTPResponse
from app.modules.auth.service import send_otp, verify_otp_and_issue_token
from app.modules.profile.models import User
from app.shared.utils.response import ok

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/send-otp", status_code=200)
def send_otp_api(payload: SendOTPRequest):
    try:
        send_otp(payload.phone_number, payload.country_code)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to reach SMS gateway")
    return ok(message="OTP sent successfully")


@router.post("/verify-otp", status_code=200)
def verify_otp_api(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    try:
        onboarding_token = verify_otp_and_issue_token(
            payload.phone_number,
            payload.country_code,
            payload.otp_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to reach SMS gateway")

    # Check if this phone number already has a profile with an access token
    existing_user = db.query(User).filter(
        User.country_code == payload.country_code,
        User.phone_number == payload.phone_number,
    ).first()

    is_new_user = existing_user is None or existing_user.access_token is None
    access_token = None if is_new_user else existing_user.access_token

    message = (
        "OTP verified. Use the onboarding token to complete registration."
        if is_new_user
        else "Welcome back. Use the access token to continue."
    )

    return ok(
        VerifyOTPResponse(
            is_new_user=is_new_user,
            onboarding_token=onboarding_token,
            access_token=access_token,
        ),
        message,
    )
