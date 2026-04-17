"""
End-to-end flow: onboarding → profile creation → post creation & interactions.

Steps:
  1. POST /auth/send-otp         → OTP to phone (dev: printed to server console)
  2. POST /auth/verify-otp       → onboarding JWT (contains user_id as 'sub')
  3. POST /profile/user          → create User row
  4. POST /profile/              → create Profile
  5. POST /profile/verify        → optional verification docs
  6. POST /posts/                → create post
  7. POST /posts/{id}/like       → like it
  8. POST /posts/{id}/comments   → comment on it
  9. GET  /posts/                → see it in feed
 10. DELETE /posts/{id}          → cleanup

Reference data (matches DB seed):
  Roles       — 1=Trader  2=Broker  3=Exporter
  Commodities — 1=Rice    2=Cotton  3=Sugar
  Interests   — 1=Connections  2=Leads  3=News
  Categories  — 1=Market Update  2=Knowledge  3=Discussion  4=Deal/Requirement  5=Other

Prerequisites:
  1. alembic upgrade head
  2. uvicorn main:app --reload

Run:
  python scripts/e2e_flow.py
  python scripts/e2e_flow.py --base http://localhost:8000
"""

import sys
import os
import argparse
import base64
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "http://localhost:8000"

ROLES = {"Trader": 1, "Broker": 2, "Exporter": 3}
COMMODITIES = {"Rice": 1, "Cotton": 2, "Sugar": 3}
INTERESTS = {"Connections": 1, "Leads": 2, "News": 3}
LOCATIONS = {
    "Mumbai":    (19.0760, 72.8777),
    "Nagpur":    (21.1458, 79.0882),
    "Vizag":     (17.6868, 83.2185),
    "Hyderabad": (17.3850, 78.4867),
    "Pune":      (18.5204, 73.8567),
}
CATEGORIES = {
    "Market Update":    1,
    "Knowledge":        2,
    "Discussion":       3,
    "Deal/Requirement": 4,
    "Other":            5,
}

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hit(method: str, path: str, **kwargs) -> httpx.Response:
    return getattr(httpx, method.lower())(f"{BASE}{path}", timeout=10, **kwargs)


def _check(label: str, r: httpx.Response, expect: int) -> dict:
    ok = r.status_code == expect
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}  ->  HTTP {r.status_code}")
    if not ok:
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


def _choose(label: str, options: dict[str, any]) -> any:
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


def _choose_many(label: str, options: dict[str, any]) -> list:
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


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without signature verification (safe for local use)."""
    try:
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception as e:
        print(f"  ERROR: Could not decode JWT: {e}")
        sys.exit(1)


def _section(title: str) -> None:
    print(f"\n{'-' * 58}")
    print(f"  {title}")
    print(f"{'-' * 58}")


# ---------------------------------------------------------------------------
# Auth steps
# ---------------------------------------------------------------------------

def step_send_otp(country_code: str, phone_number: str) -> None:
    _section("Step 1 — Send OTP")
    _check(
        f"POST /auth/send-otp  ({country_code} {phone_number})",
        _hit("POST", "/auth/send-otp", json={
            "country_code": country_code,
            "phone_number": phone_number,
        }),
        expect=200,
    )
    print("  OTP sent. Check your phone (or server console in DEV_MODE).")


def step_verify_otp(country_code: str, phone_number: str) -> tuple[str, str]:
    """Returns (onboarding_token, user_id_str)."""
    _section("Step 2 — Verify OTP")
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
    claims = _decode_jwt_payload(token)
    user_id = claims["sub"]
    print(f"  Token received.  user_id={user_id}")
    return token, user_id


# ---------------------------------------------------------------------------
# Profile steps
# ---------------------------------------------------------------------------

def step_create_user(user_id: str, phone_number: str, country_code: str) -> None:
    _section("Step 3 — Create user record")
    _check(
        "POST /profile/user",
        _hit("POST", "/profile/user", params={
            "user_id":      user_id,
            "phone_number": phone_number,
            "country_code": country_code,
        }),
        expect=201,
    )
    print("  User row created.")


def step_create_profile(user_id: str) -> dict:
    _section("Step 4 — Create profile")

    role_id       = _choose("Select your role", ROLES)
    name          = _prompt("Full name")
    commodity_ids = _choose_many("Select commodities you trade", COMMODITIES)
    qty_min       = float(_prompt("Minimum quantity (MT)", "100"))
    qty_max       = float(_prompt("Maximum quantity (MT)", "1000"))
    interest_ids  = _choose_many("What are you looking for?", INTERESTS)
    business_name = _prompt("Business / Firm name (optional, Enter to skip)", "") or None
    loc_name      = _choose("Business location", {loc: loc for loc in LOCATIONS})
    latitude, longitude = LOCATIONS[loc_name]

    body = _check(
        "POST /profile/",
        _hit("POST", "/profile/", params={"user_id": user_id}, json={
            "role_id":       role_id,
            "name":          name,
            "commodities":   commodity_ids,
            "quantity_min":  qty_min,
            "quantity_max":  qty_max,
            "interests":     interest_ids,
            "business_name": business_name,
            "latitude":      latitude,
            "longitude":     longitude,
        }),
        expect=200,
    )
    profile = body["data"]
    print(f"  Profile created.  profile_id={profile['id']}")
    return profile


def step_verify_profile(user_id: str) -> None:
    _section("Step 5 — Verification (optional)")
    if _prompt("Submit verification documents? (y/N)", "N").lower() != "y":
        print("  Skipped.")
        return

    IDENTITY_TYPES = {"PAN Card": "pan_card", "Aadhaar Card": "aadhaar_card"}
    BUSINESS_TYPES = {"GST Certificate": "gst_certificate", "Trade License": "trade_license"}
    payload: dict = {}

    if _prompt("Add identity proof? (y/N)", "N").lower() == "y":
        id_type   = _choose("Identity document type", IDENTITY_TYPES)
        id_number = _prompt("Enter document number")
        payload["identity_proof"] = {"document_type": id_type, "document_number": id_number}

    if _prompt("Add business proof? (y/N)", "N").lower() == "y":
        biz_type   = _choose("Business document type", BUSINESS_TYPES)
        biz_number = _prompt("Enter document number")
        payload["business_proof"] = {"document_type": biz_type, "document_number": biz_number}

    if not payload:
        print("  Nothing submitted.")
        return

    _check(
        "POST /profile/verify",
        _hit("POST", "/profile/verify", params={"user_id": user_id}, json=payload),
        expect=200,
    )
    print("  Documents submitted.")


# ---------------------------------------------------------------------------
# Post steps
# ---------------------------------------------------------------------------

def step_create_post(profile_id: int) -> int:
    _section("Step 6 — Create a post")
    cat_id = _choose("Select post category", CATEGORIES)
    com_id = _choose("Select commodity", COMMODITIES)
    caption = _prompt("Post caption", "Excited to join Vanijyaa!")

    json_body: dict = {
        "category_id": cat_id,
        "commodity_id": com_id,
        "caption": caption,
    }

    if cat_id == 4:  # Deal/Requirement
        json_body["grain_type_size"]    = _prompt("Grain type / size")
        json_body["commodity_quantity"] = float(_prompt("Quantity (MT)"))
        json_body["price_type"]         = _choose("Price type", {"Fixed": "fixed", "Negotiable": "negotiable"})

    if cat_id == 5:  # Other
        json_body["other_description"] = _prompt("Description")

    body = _check(
        "POST /posts/",
        _hit("POST", "/posts/", params={"profile_id": profile_id}, json=json_body),
        expect=201,
    )
    post_id = body["data"]["id"]
    print(f"  Post created.  post_id={post_id}")
    return post_id


def step_like_post(profile_id: int, post_id: int) -> None:
    _section("Step 7 — Like post")
    body = _check(
        f"POST /posts/{post_id}/like",
        _hit("POST", f"/posts/{post_id}/like", params={"profile_id": profile_id}),
        expect=200,
    )
    print(f"  liked={body['data']['liked']}  like_count={body['data']['like_count']}")


def step_comment_post(profile_id: int, post_id: int) -> None:
    _section("Step 8 — Add comment")
    content = _prompt("Comment text", "Great post!")
    body = _check(
        f"POST /posts/{post_id}/comments",
        _hit("POST", f"/posts/{post_id}/comments",
             params={"profile_id": profile_id},
             json={"content": content}),
        expect=201,
    )
    print(f"  comment_id={body['data']['id']}")


def step_view_feed(profile_id: int) -> None:
    _section("Step 9 — View feed")
    body = _check(
        "GET /posts/",
        _hit("GET", "/posts/", params={"profile_id": profile_id, "limit": 5}),
        expect=200,
    )
    print(f"  {len(body['data'])} post(s) in feed")


def step_cleanup_post(profile_id: int, post_id: int) -> None:
    _section("Step 10 — Delete post (cleanup)")
    skip = _prompt("Delete the test post? (Y/n)", "Y").lower()
    if skip == "n":
        print(f"  Kept.  post_id={post_id}")
        return
    _check(
        f"DELETE /posts/{post_id}",
        _hit("DELETE", f"/posts/{post_id}", params={"profile_id": profile_id}),
        expect=204,
    )
    print("  Post deleted.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Vanijyaa end-to-end flow")
    parser.add_argument("--base", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    global BASE
    BASE = args.base

    print()
    print("=" * 58)
    print("  Vanijyaa — End-to-End Flow")
    print("  onboarding → profile → post")
    print("=" * 58)

    # Auth
    print("\nEnter your phone number:")
    country_code = _prompt("Country code", "+91")
    phone_number = _prompt("Phone number (digits only)")

    step_send_otp(country_code, phone_number)
    token, user_id = step_verify_otp(country_code, phone_number)

    # Profile
    step_create_user(user_id, phone_number, country_code)
    profile = step_create_profile(user_id)
    step_verify_profile(user_id)

    # Posts
    profile_id = profile["id"]
    post_id = step_create_post(profile_id)
    step_like_post(profile_id, post_id)
    step_comment_post(profile_id, post_id)
    step_view_feed(profile_id)
    step_cleanup_post(profile_id, post_id)

    print()
    print("=" * 58)
    print("  Flow complete!")
    print("=" * 58)
    print(f"  user_id    : {user_id}")
    print(f"  profile_id : {profile_id}")
    print(f"  name       : {profile['name']}")
    print()


if __name__ == "__main__":
    main()
