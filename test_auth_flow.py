"""
Auth + Profile API full-flow test script
-----------------------------------------
Run from the backend folder:
    python scripts/test_auth_flow.py

Firebase is MOCKED — no real OTP / SIM needed.
The script creates a real test user in your DB, runs every step,
then deletes the test account via the DELETE /profile/user endpoint.

Avatar upload is skipped (requires live Supabase storage).
"""

import json
import sys
from unittest.mock import patch

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from main import app
from app.core.config import settings

client = TestClient(app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Test credentials
# ---------------------------------------------------------------------------
TEST_PHONE        = "9000000099"
TEST_COUNTRY_CODE = "+91"
FAKE_TOKEN        = "fake-firebase-id-token-for-testing"

PROFILE_PAYLOAD = {
    "role_id": 1,
    "name": "Test Trader",
    "commodities": [1, 2],
    "interests":   [1, 3],
    "quantity_min": 100.0,
    "quantity_max": 5000.0,
    "business_name": "Test Agro Pvt Ltd",
    "city": "Pune",
    "state": "Maharashtra",
    "latitude":  18.5204,
    "longitude": 73.8567,
}

EXPECTED_EXPIRES_IN = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

# ---------------------------------------------------------------------------
# Pre-test cleanup — remove leftover test user from a previous failed run
# ---------------------------------------------------------------------------

def _pre_cleanup():
    from app.core.database.session import SessionLocal
    from app.modules.profile.models import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.phone_number == TEST_PHONE,
            User.country_code == TEST_COUNTRY_CODE,
        ).first()
        if user:
            db.delete(user)
            db.commit()
            print(f"[pre-cleanup] Removed leftover test user {TEST_PHONE} from previous run.")
    finally:
        db.close()

_pre_cleanup()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = 0
FAIL = 0

def show(label, payload):
    print(f"\n{'='*64}")
    print(f"  {label}")
    print(f"{'='*64}")
    print(json.dumps(payload, indent=2, default=str))

def check(name, condition, actual=None):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {name}")
        PASS += 1
    else:
        print(f"  [FAIL] {name}  |  got: {actual}")
        FAIL += 1

def section(title):
    print(f"\n{'#'*64}")
    print(f"  {title}")
    print(f"{'#'*64}")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

state = {}

with patch(
    "app.modules.auth.router.verify_firebase_token",
    return_value=(TEST_PHONE, TEST_COUNTRY_CODE),
):

    # ========================================================================
    section("AUTH & ONBOARDING")
    # ========================================================================

    # --------------------------------------------------------
    # STEP 1 — firebase-verify (new user)
    # --------------------------------------------------------
    req = {
        "firebase_id_token": FAKE_TOKEN,
        "device_info": "Test Runner / Windows",
    }
    show("STEP 1 - REQUEST  POST /auth/firebase-verify  (new user)", req)

    r = client.post("/auth/firebase-verify", json=req)
    body = r.json()
    show("STEP 1 - RESPONSE POST /auth/firebase-verify", body)

    check("status 200",               r.status_code == 200, r.status_code)
    check("is_new_user = true",       body["data"]["is_new_user"] is True)
    check("onboarding_token present", body["data"]["onboarding_token"] is not None)
    check("access_token is null",     body["data"]["access_token"] is None)

    state["onboarding_token"] = body["data"]["onboarding_token"]
    headers_onboarding = {"Authorization": f"Bearer {state['onboarding_token']}"}


    # --------------------------------------------------------
    # STEP 2 — create user row
    # --------------------------------------------------------
    show("STEP 2 - REQUEST  POST /profile/user", {"Authorization": "Bearer <onboarding_token>"})

    r = client.post("/profile/user", headers=headers_onboarding)
    body = r.json()
    show("STEP 2 - RESPONSE POST /profile/user", body)

    check("status 201",         r.status_code == 201, r.status_code)
    check("user id present",    "id" in body["data"])
    check("phone_number match", body["data"]["phone_number"] == TEST_PHONE)
    check("country_code match", body["data"]["country_code"] == TEST_COUNTRY_CODE)

    state["user_id"] = body["data"]["id"]


    # --------------------------------------------------------
    # STEP 3 — create profile  ->  first real token pair
    # --------------------------------------------------------
    show("STEP 3 - REQUEST  POST /profile/  (create profile)", PROFILE_PAYLOAD)

    r = client.post("/profile/", json=PROFILE_PAYLOAD, headers=headers_onboarding)
    body = r.json()
    show("STEP 3 - RESPONSE POST /profile/", body)

    check("status 200",                      r.status_code == 200, r.status_code)
    check("access_token present",            body["data"]["access_token"] is not None)
    check("refresh_token present",           body["data"]["refresh_token"] is not None)
    check(f"expires_in = {EXPECTED_EXPIRES_IN}",
          body["data"]["expires_in"] == EXPECTED_EXPIRES_IN, body["data"]["expires_in"])
    check("profile name correct",            body["data"]["profile"]["name"] == PROFILE_PAYLOAD["name"])
    check("profile has phone_number",        "phone_number" in body["data"]["profile"])
    check("profile has country_code",        "country_code" in body["data"]["profile"])
    check("profile has posts_count",         "posts_count" in body["data"]["profile"])
    check("profile has followers_count",     "followers_count" in body["data"]["profile"])
    check("posts_count = 0 (new profile)",   body["data"]["profile"]["posts_count"] == 0)
    check("followers_count = 0 (new profile)", body["data"]["profile"]["followers_count"] == 0)

    state["access_token"]  = body["data"]["access_token"]
    state["refresh_token"] = body["data"]["refresh_token"]
    state["profile_id"]    = body["data"]["profile"]["id"]
    headers_access = {"Authorization": f"Bearer {state['access_token']}"}


    # ========================================================================
    section("PROFILE APIs")
    # ========================================================================

    # --------------------------------------------------------
    # STEP 4 — GET /profile/me  (JWT protected, no query param)
    # --------------------------------------------------------
    show("STEP 4 - REQUEST  GET /profile/me  (JWT auth)", {"Authorization": "Bearer <access_token>"})

    r = client.get("/profile/me", headers=headers_access)
    body = r.json()
    show("STEP 4 - RESPONSE GET /profile/me", body)

    check("status 200",                    r.status_code == 200, r.status_code)
    check("name matches",                  body["data"]["name"] == PROFILE_PAYLOAD["name"])
    check("city matches",                  body["data"]["city"] == PROFILE_PAYLOAD["city"])
    check("state matches",                 body["data"]["state"] == PROFILE_PAYLOAD["state"])
    check("role_id matches",               body["data"]["role_id"] == PROFILE_PAYLOAD["role_id"])
    check("2 commodities",                 len(body["data"]["commodities"]) == 2)
    check("2 interests",                   len(body["data"]["interests"]) == 2)
    check("phone_number present",          body["data"]["phone_number"] == TEST_PHONE)
    check("country_code present",          body["data"]["country_code"] == TEST_COUNTRY_CODE)
    check("posts_count present",           "posts_count" in body["data"])
    check("followers_count present",       "followers_count" in body["data"])
    check("is_verified = false",           body["data"]["is_verified"] is False)
    check("is_user_verified = false",      body["data"]["is_user_verified"] is False)
    check("is_business_verified = false",  body["data"]["is_business_verified"] is False)
    check("avatar_url is null initially",  body["data"]["avatar_url"] is None)


    # --------------------------------------------------------
    # STEP 5 — PATCH /profile/  (update name + city)
    # --------------------------------------------------------
    update_payload = {
        "name": "Updated Trader",
        "city": "Mumbai",
        "state": "Maharashtra",
        "latitude": 19.0760,
        "longitude": 72.8777,
    }
    show("STEP 5 - REQUEST  PATCH /profile/  (update profile)", update_payload)

    r = client.patch("/profile/", json=update_payload, headers=headers_access)
    body = r.json()
    show("STEP 5 - RESPONSE PATCH /profile/", body)

    check("status 200",               r.status_code == 200, r.status_code)
    check("name updated",             body["data"]["name"] == "Updated Trader")
    check("city updated",             body["data"]["city"] == "Mumbai")
    check("phone still present",      body["data"]["phone_number"] == TEST_PHONE)
    check("posts_count still present",body["data"]["posts_count"] == 0)


    # --------------------------------------------------------
    # STEP 6 — verify update persisted via GET /profile/me
    # --------------------------------------------------------
    show("STEP 6 - REQUEST  GET /profile/me  (confirm update)", {})

    r = client.get("/profile/me", headers=headers_access)
    body = r.json()
    show("STEP 6 - RESPONSE GET /profile/me  (after update)", body)

    check("name persisted",  body["data"]["name"] == "Updated Trader")
    check("city persisted",  body["data"]["city"] == "Mumbai")


    # --------------------------------------------------------
    # STEP 7 — PATCH /profile/user/fcm-token
    # --------------------------------------------------------
    fcm_payload = {"fcm_token": "test-fcm-token-abc123xyz"}
    show("STEP 7 - REQUEST  PATCH /profile/user/fcm-token", fcm_payload)

    r = client.patch("/profile/user/fcm-token", json=fcm_payload, headers=headers_access)
    body = r.json()
    show("STEP 7 - RESPONSE PATCH /profile/user/fcm-token", body)

    check("status 200", r.status_code == 200, r.status_code)


    # --------------------------------------------------------
    # STEP 8 — POST /profile/verify  (KYC documents)
    # --------------------------------------------------------
    verify_payload = {
        "identity_proof": {
            "document_type": "pan_card",
            "document_number": "ABCDE1234F"
        },
        "business_proof": {
            "document_type": "gst_certificate",
            "document_number": "27AAPFU0939F1ZV"
        }
    }
    show("STEP 8 - REQUEST  POST /profile/verify", verify_payload)

    r = client.post("/profile/verify", json=verify_payload, headers=headers_access)
    body = r.json()
    show("STEP 8 - RESPONSE POST /profile/verify", body)

    check("status 200",                   r.status_code == 200, r.status_code)
    check("pan_card in submitted",        "pan_card" in body["data"]["submitted"])
    check("gst_certificate in submitted", "gst_certificate" in body["data"]["submitted"])
    check("status = pending_review",      body["data"]["status"] == "pending_review")


    # --------------------------------------------------------
    # STEP 9 — POST /profile/verify  (bad document_type)
    # --------------------------------------------------------
    bad_verify = {
        "identity_proof": {
            "document_type": "passport",
            "document_number": "A1234567"
        }
    }
    show("STEP 9 - REQUEST  POST /profile/verify  (invalid document_type)", bad_verify)

    r = client.post("/profile/verify", json=bad_verify, headers=headers_access)
    body = r.json()
    show("STEP 9 - RESPONSE POST /profile/verify  (should be 400)", body)

    check("status 400 (invalid doc type)", r.status_code == 400, r.status_code)


    # --------------------------------------------------------
    # STEP 10 — GET /profile/{profile_id}  (public, no auth)
    # --------------------------------------------------------
    show(f"STEP 10 - REQUEST  GET /profile/{state['profile_id']}  (public, no auth)", {})

    r = client.get(f"/profile/{state['profile_id']}")
    body = r.json()
    show(f"STEP 10 - RESPONSE GET /profile/{state['profile_id']}", body)

    check("status 200",                       r.status_code == 200, r.status_code)
    check("profile id matches",               body["data"]["id"] == state["profile_id"])
    check("name updated (shows new name)",    body["data"]["name"] == "Updated Trader")
    check("followers_count present",          "followers_count" in body["data"])
    check("posts_count present",              "posts_count" in body["data"])
    check("commodities present",              len(body["data"]["commodities"]) > 0)
    check("phone_number NOT in public view",  "phone_number" not in body["data"])
    check("interests NOT in public view",     "interests" not in body["data"])


    # --------------------------------------------------------
    # STEP 11 — GET /profile/{bad_id}  (should be 404)
    # --------------------------------------------------------
    show("STEP 11 - REQUEST  GET /profile/999999  (non-existent)", {})

    r = client.get("/profile/999999")
    body = r.json()
    show("STEP 11 - RESPONSE GET /profile/999999  (should be 404)", body)

    check("status 404", r.status_code == 404, r.status_code)


    # ========================================================================
    section("TOKEN LIFECYCLE")
    # ========================================================================

    # --------------------------------------------------------
    # STEP 12 — POST /auth/refresh
    # --------------------------------------------------------
    req = {"refresh_token": state["refresh_token"]}
    show("STEP 12 - REQUEST  POST /auth/refresh", req)

    r = client.post("/auth/refresh", json=req)
    body = r.json()
    show("STEP 12 - RESPONSE POST /auth/refresh", body)

    check("status 200",              r.status_code == 200, r.status_code)
    check("new access_token issued", body["access_token"] != state["access_token"])
    check("refresh_token rotated",   body["refresh_token"] != state["refresh_token"])

    old_refresh = state["refresh_token"]
    state["access_token"]  = body["access_token"]
    state["refresh_token"] = body["refresh_token"]
    headers_access = {"Authorization": f"Bearer {state['access_token']}"}


    # --------------------------------------------------------
    # STEP 13 — old rotated refresh token must be dead
    # --------------------------------------------------------
    show("STEP 13 - REQUEST  POST /auth/refresh  (old / rotated token)", {"refresh_token": "..."})

    r = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    body = r.json()
    show("STEP 13 - RESPONSE  (should be 401)", body)

    check("status 401 (rotated token rejected)", r.status_code == 401, r.status_code)


    # --------------------------------------------------------
    # STEP 14 — logout
    # --------------------------------------------------------
    show("STEP 14 - REQUEST  POST /auth/logout", {"Authorization": "Bearer <access_token>"})

    r = client.post("/auth/logout", json={}, headers=headers_access)
    body = r.json()
    show("STEP 14 - RESPONSE POST /auth/logout", body)

    check("status 200", r.status_code == 200, r.status_code)


    # --------------------------------------------------------
    # STEP 15 — refresh after logout must fail
    # --------------------------------------------------------
    req = {"refresh_token": state["refresh_token"]}
    show("STEP 15 - REQUEST  POST /auth/refresh  (after logout)", req)

    r = client.post("/auth/refresh", json=req)
    body = r.json()
    show("STEP 15 - RESPONSE  (should be 401)", body)

    check("status 401 (session revoked after logout)", r.status_code == 401, r.status_code)


    # --------------------------------------------------------
    # STEP 16 — GET /profile/me with revoked token must fail
    # --------------------------------------------------------
    show("STEP 16 - REQUEST  GET /profile/me  (with revoked token)", {})

    # The access token is still a valid JWT (not expired) but session is revoked
    # For JWT-only auth (no session DB check), this will still pass —
    # document what the app actually does so the test is honest
    r = client.get("/profile/me", headers=headers_access)
    show("STEP 16 - RESPONSE GET /profile/me  (revoked session)", r.json())

    # NOTE: Our current get_current_user does JWT-only validation (no DB lookup).
    # So the access token is still valid until it expires even after logout.
    # This is the expected behaviour — logout only kills the refresh path.
    # A truly revoked session is enforced at the refresh level.
    check("JWT-only: access token still works until exp (expected)", r.status_code == 200, r.status_code)


    # --------------------------------------------------------
    # STEP 17 — returning user login
    # --------------------------------------------------------
    req = {
        "firebase_id_token": FAKE_TOKEN,
        "device_info": "Test Runner / second login",
    }
    show("STEP 17 - REQUEST  POST /auth/firebase-verify  (returning user)", req)

    r = client.post("/auth/firebase-verify", json=req)
    body = r.json()
    show("STEP 17 - RESPONSE POST /auth/firebase-verify  (returning user)", body)

    check("status 200",                              r.status_code == 200, r.status_code)
    check("is_new_user = false",                     body["data"]["is_new_user"] is False)
    check("access_token present",                    body["data"]["access_token"] is not None)
    check("refresh_token present",                   body["data"]["refresh_token"] is not None)
    check(f"expires_in = {EXPECTED_EXPIRES_IN}",
          body["data"]["expires_in"] == EXPECTED_EXPIRES_IN, body["data"]["expires_in"])
    check("user_id matches",                         body["data"]["user_id"] == state["user_id"])
    check("profile_id matches",                      body["data"]["profile_id"] == state["profile_id"])

    state["access_token"]  = body["data"]["access_token"]
    state["refresh_token"] = body["data"]["refresh_token"]
    headers_access = {"Authorization": f"Bearer {state['access_token']}"}


    # --------------------------------------------------------
    # STEP 18 — tampered access token must be rejected
    # --------------------------------------------------------
    bad_token = state["access_token"][:-5] + "XXXXX"
    show("STEP 18 - tampered token (last 5 chars replaced)", {"snippet": bad_token[:40] + "..."})

    from app.core.security.jwt_handler import decode_access_token
    from fastapi import HTTPException
    try:
        decode_access_token(bad_token)
        check("tampered token rejected", False, "no error raised")
    except HTTPException as e:
        check("tampered token rejected with 401", e.status_code == 401, e.status_code)


    # ========================================================================
    section("CLEANUP — DELETE ACCOUNT")
    # ========================================================================

    # --------------------------------------------------------
    # STEP 19 — DELETE /profile/user  (full account delete via API)
    # --------------------------------------------------------
    show("STEP 19 - REQUEST  DELETE /profile/user  (full account delete)", {})

    r = client.delete("/profile/user", headers=headers_access)
    body = r.json()
    show("STEP 19 - RESPONSE DELETE /profile/user", body)

    check("status 200 (account deleted)", r.status_code == 200, r.status_code)


    # --------------------------------------------------------
    # STEP 20 — verify account is really gone
    # --------------------------------------------------------
    show(f"STEP 20 - REQUEST  GET /profile/{state['profile_id']}  (should be 404 now)", {})

    r = client.get(f"/profile/{state['profile_id']}")
    body = r.json()
    show(f"STEP 20 - RESPONSE GET /profile/{state['profile_id']}  (after delete)", body)

    check("status 404 (profile gone after delete)", r.status_code == 404, r.status_code)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'='*64}")
print(f"  RESULTS:  {PASS} passed   {FAIL} failed")
print(f"{'='*64}\n")

if FAIL:
    sys.exit(1)
