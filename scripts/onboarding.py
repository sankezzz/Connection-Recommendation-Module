"""
Interactive onboarding script — walks through the full new-user flow:

  1. POST /auth/send-otp        → OTP sent to phone (dev: printed to server console)
  2. POST /auth/verify-otp      → returns onboarding JWT
  3. POST /profile/user         → creates User row
  4. POST /profile/             → creates Profile (role + basic details + location)
  5. POST /profile/verify       → optional: submit identity / business docs

Reference data (fixed IDs, matches DB seed):
  Roles       — 1=Trader  2=Broker  3=Exporter
  Commodities — 1=Rice    2=Cotton  3=Sugar
  Interests   — 1=Connections  2=Leads  3=News

Prerequisites:
  1. alembic upgrade head        (creates tables + seeds lookup data)
  2. uvicorn main:app --reload   (server on localhost:8000)

Run from project root:
  python scripts/onboarding.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Fixed reference data — IDs match the seeded lookup tables
# ---------------------------------------------------------------------------

ROLES = {
    "Trader":   1,
    "Broker":   2,
    "Exporter": 3,
}

COMMODITIES = {
    "Rice":   1,
    "Cotton": 2,
    "Sugar":  3,
}

INTERESTS = {
    "Connections": 1,
    "Leads":       2,
    "News":        3,
}

LOCATIONS = {
    "Mumbai":    (19.0760, 72.8777),
    "Nagpur":    (21.1458, 79.0882),
    "Vizag":     (17.6868, 83.2185),
    "Hyderabad": (17.3850, 78.4867),
    "Pune":      (18.5204, 73.8567),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hit(method: str, url: str, token: str | None = None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return getattr(httpx, method.lower())(f"{BASE}{url}", headers=headers, timeout=10, **kwargs)


def _check(label: str, r: httpx.Response, expect: int = 200) -> dict:
    passed = r.status_code == expect
    status = "OK" if passed else "FAIL"
    print(f"  [{status}] {label}  HTTP {r.status_code}")
    if not passed:
        try:
            print(f"         {r.json()}")
        except Exception:
            print(f"         {r.text[:300]}")
        sys.exit(1)
    return r.json()


def _prompt(question: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"  {question}{suffix}: ").strip()
    if not value and default is not None:
        return default
    if not value:
        print(f"  ERROR: {question} is required.")
        sys.exit(1)
    return value


def _choose(label: str, options: dict[str, int]) -> int:
    """Show a numbered menu; return the int ID the user chose."""
    names = list(options.keys())
    print(f"\n  {label}:")
    for i, name in enumerate(names, 1):
        print(f"    {i}. {name}")
    raw = _prompt(f"Enter number (1-{len(names)})")
    try:
        idx = int(raw) - 1
        if not (0 <= idx < len(names)):
            raise ValueError
    except ValueError:
        print("  ERROR: Invalid choice.")
        sys.exit(1)
    return options[names[idx]]


def _choose_many(label: str, options: dict[str, int]) -> list[int]:
    """Show a numbered menu; allow comma-separated multi-select. Returns list of int IDs."""
    names = list(options.keys())
    print(f"\n  {label} (comma-separated numbers):")
    for i, name in enumerate(names, 1):
        print(f"    {i}. {name}")
    raw = _prompt("Enter numbers (e.g. 1,3)")
    try:
        indices = [int(x.strip()) - 1 for x in raw.split(",")]
        if any(not (0 <= i < len(names)) for i in indices):
            raise ValueError
    except ValueError:
        print("  ERROR: Invalid selection.")
        sys.exit(1)
    return [options[names[i]] for i in indices]


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def step_send_otp(country_code: str, phone_number: str) -> None:
    print("\n[1/5] Sending OTP...")
    _check(
        f"POST /auth/send-otp  {country_code} {phone_number}",
        _hit("POST", "/auth/send-otp", json={
            "country_code": country_code,
            "phone_number": phone_number,
        }),
        expect=200,
    )
    print("  OTP sent. Check your phone (or server console in DEV_MODE).")


def step_verify_otp(country_code: str, phone_number: str) -> str:
    print("\n[2/5] Verifying OTP...")
    otp_code = _prompt("Enter the OTP you received")
    body = _check(
        "POST /auth/verify-otp",
        _hit("POST", "/auth/verify-otp", json={
            "country_code": country_code,
            "phone_number": phone_number,
            "otp_code": otp_code,
        }),
        expect=200,
    )
    token = body["data"]["onboarding_token"]
    print("  Onboarding token received.")
    return token


def step_create_user(token: str) -> None:
    print("\n[3/5] Creating user record...")
    _check(
        "POST /profile/user",
        _hit("POST", "/profile/user", token=token),
        expect=201,
    )
    print("  User created.")


def step_create_profile(token: str) -> dict:
    print("\n[4/5] Creating profile...")

    # Screen 3 — Select role
    role_id = _choose("Select your role", ROLES)

    # Screen 4 — Basic details
    name         = _prompt("Full name")
    commodity_ids = _choose_many("Select commodities you trade", COMMODITIES)
    qty_min      = float(_prompt("Minimum quantity (MT)", "100"))
    qty_max      = float(_prompt("Maximum quantity (MT)", "1000"))
    interest_ids  = _choose_many("What are you looking for?", INTERESTS)

    # Screen 5 — Profile setup
    business_name = _prompt("Business / Firm name (optional, Enter to skip)", "") or None
    loc_name      = _choose("Business location", {loc: loc for loc in LOCATIONS})
    latitude, longitude = LOCATIONS[loc_name]

    body = _check(
        "POST /profile/",
        _hit("POST", "/profile/", token=token, json={
            "role_id":      role_id,
            "name":         name,
            "commodities":  commodity_ids,
            "quantity_min": qty_min,
            "quantity_max": qty_max,
            "interests":    interest_ids,
            "business_name": business_name,
            "latitude":     latitude,
            "longitude":    longitude,
        }),
        expect=200,
    )
    return body["data"]


def step_verify_profile(token: str) -> None:
    """Screen 6 — optional verification docs."""
    print("\n[5/5] Profile verification (optional)")
    skip = _prompt("Submit verification documents? (y/N)", "N").lower()
    if skip != "y":
        print("  Skipped.")
        return

    IDENTITY_TYPES = {"PAN Card": "pan_card", "Aadhaar Card": "aadhaar_card"}
    BUSINESS_TYPES = {"GST Certificate": "gst_certificate", "Trade License": "trade_license"}

    payload: dict = {}

    do_identity = _prompt("Add identity proof (PAN / Aadhaar)? (y/N)", "N").lower()
    if do_identity == "y":
        id_type   = _choose("Identity document type", IDENTITY_TYPES)
        id_number = _prompt("Enter document number")
        payload["identity_proof"] = {"document_type": id_type, "document_number": id_number}

    do_business = _prompt("Add business proof (GST / Trade License)? (y/N)", "N").lower()
    if do_business == "y":
        biz_type   = _choose("Business document type", BUSINESS_TYPES)
        biz_number = _prompt("Enter document number")
        payload["business_proof"] = {"document_type": biz_type, "document_number": biz_number}

    if not payload:
        print("  Nothing submitted.")
        return

    _check(
        "POST /profile/verify",
        _hit("POST", "/profile/verify", token=token, json=payload),
        expect=200,
    )
    print("  Documents submitted for verification.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Vanijyaa — New User Onboarding")
    print("=" * 60)

    print("\nEnter your phone number:")
    country_code  = _prompt("Country code", "+91")
    phone_number  = _prompt("Phone number (digits only)")

    step_send_otp(country_code, phone_number)
    token   = step_verify_otp(country_code, phone_number)
    step_create_user(token)
    profile = step_create_profile(token)
    step_verify_profile(token)

    print()
    print("=" * 60)
    print("  Onboarding complete!")
    print("=" * 60)
    print(f"  Profile ID : {profile['id']}")
    print(f"  Name       : {profile['name']}")
    print()


if __name__ == "__main__":
    main()
