"""
gen_token.py — generate an onboarding JWT for local testing.

The real onboarding token comes from POST /auth/verify-otp.
Use this script to skip OTP when testing profile endpoints directly.

Usage:
    python scripts/gen_token.py

Paste the printed token into Swagger UI Authorize box or as:
    Authorization: Bearer <token>
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security.jwt_handler import create_onboarding_token

# Edit these as you like — phone/country_code end up in the token payload
USER_ID      = uuid.uuid4()
PHONE_NUMBER = "9876543210"
COUNTRY_CODE = "+91"


def main():
    token = create_onboarding_token(
        user_id=USER_ID,
        phone_number=PHONE_NUMBER,
        country_code=COUNTRY_CODE,
    )

    print("\n" + "=" * 60)
    print("USER_ID (encoded in the token — links user + profile):")
    print(f"  {USER_ID}")
    print("=" * 60)
    print("\nONBOARDING TOKEN:")
    print(f"\n  {token}\n")
    print("Use this token for:")
    print("  POST /profile/user   (create user row)")
    print("  POST /profile/       (create profile)")
    print()
    print("For GET /profile/me, PATCH, DELETE — use the real access token")
    print("from the auth developer (not yet implemented in this module).\n")
    print("Swagger UI:")
    print("  1. Open http://localhost:8000/docs")
    print("  2. Click Authorize (top right)")
    print("  3. Paste token → Authorize\n")


if __name__ == "__main__":
    main()
