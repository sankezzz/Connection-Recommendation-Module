import httpx
from fastapi import APIRouter, HTTPException

from app.modules.auth.schemas import OnboardingTokenResponse, SendOTPRequest, VerifyOTPRequest
from app.modules.auth.service import send_otp, verify_otp_and_issue_token
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
def verify_otp_api(payload: VerifyOTPRequest):
    try:
        token = verify_otp_and_issue_token(
            payload.phone_number,
            payload.country_code,
            payload.otp_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to reach SMS gateway")
    return ok(
        OnboardingTokenResponse(onboarding_token=token),
        "OTP verified. Use the onboarding token to complete registration.",
    )
