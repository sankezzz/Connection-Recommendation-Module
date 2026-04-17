from typing import Optional
from pydantic import BaseModel


class SendOTPRequest(BaseModel):
    phone_number: str
    country_code: str  # e.g. "+91"


class VerifyOTPRequest(BaseModel):
    phone_number: str
    country_code: str
    otp_code: str


class OnboardingTokenResponse(BaseModel):
    onboarding_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds


class VerifyOTPResponse(BaseModel):
    is_new_user: bool
    onboarding_token: str        # always present — needed if new user
    access_token: Optional[str]  # present only for returning users
    token_type: str = "bearer"
