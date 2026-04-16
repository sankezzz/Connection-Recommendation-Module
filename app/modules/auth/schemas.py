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
