"""
Post-module interactive test runner.

Walks through every post API with user input — you choose the content,
and the script fires the request and shows PASS / FAIL for each step.

Prerequisites:
  1. alembic upgrade head
  2. uvicorn main:app --reload
  3. A profile must already exist (run scripts/onboarding.py first)

Run:
  python scripts/test_posts.py --profile-id 1
  python scripts/test_posts.py           # prompts for profile_id
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from typing import Any

BASE = "http://localhost:8000"

# Matches DB seed
CATEGORIES = {
    "Market Update":    1,
    "Knowledge":        2,
    "Discussion":       3,
    "Deal/Requirement": 4,
    "Other":            5,
}
COMMODITIES = {"Rice": 1, "Cotton": 2, "Sugar": 3}
PRICE_TYPES = {"Fixed": "fixed", "Negotiable": "negotiable"}

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hit(method: str, path: str, **kwargs) -> httpx.Response:
    return getattr(httpx, method.lower())(f"{BASE}{path}", timeout=10, **kwargs)


def _check(label: str, r: httpx.Response, expect: int) -> dict | None:
    ok = r.status_code == expect
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}  ->  HTTP {r.status_code}")
    if not ok:
        try:
            print(f"         {r.json()}")
        except Exception:
            print(f"         {r.text[:300]}")
    if not ok:
        return None
    return r.json() if r.content else None


def _section(title: str) -> None:
    print(f"\n{'-' * 58}")
    print(f"  {title}")
    print(f"{'-' * 58}")


def _prompt(question: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"  {question}{suffix}: ").strip()
    if not value and default is not None:
        return default
    if not value:
        print(f"  ERROR: {question} is required.")
        sys.exit(1)
    return value


def _choose(label: str, options: dict[str, Any]) -> Any:
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


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def step_create_post(profile_id: int) -> int:
    _section("Step 1 — Create a post")

    cat_id = _choose("Post category", CATEGORIES)
    com_id = _choose("Commodity", COMMODITIES)
    caption = _prompt("Caption")
    is_public = _prompt("Visible to all? (Y/n)", "Y").lower() != "n"
    allow_comments = _prompt("Allow comments? (Y/n)", "Y").lower() != "n"

    body: dict = {
        "category_id": cat_id,
        "commodity_id": com_id,
        "caption": caption,
        "is_public": is_public,
        "allow_comments": allow_comments,
    }

    if cat_id == 4:  # Deal / Requirement
        print("\n  Deal/Requirement fields:")
        body["grain_type_size"]    = _prompt("Grain type / size")
        body["commodity_quantity"] = float(_prompt("Quantity (MT)"))
        body["price_type"]         = _choose("Price type", PRICE_TYPES)

    if cat_id == 5:  # Other
        body["other_description"] = _prompt("Description")

    r = _hit("POST", "/posts/", params={"profile_id": profile_id}, json=body)
    result = _check("POST /posts/", r, expect=201)
    if not result:
        print("\n  Cannot continue — post creation failed.")
        sys.exit(1)

    post_id = result["data"]["id"]
    print(f"\n  Post created.  post_id={post_id}")
    return post_id


def step_view_post(profile_id: int, post_id: int) -> None:
    _section("Step 2 — View post (GET)")
    r = _hit("GET", f"/posts/{post_id}", params={"profile_id": profile_id})
    result = _check(f"GET /posts/{post_id}", r, expect=200)
    if result:
        d = result["data"]
        print(f"  caption      : {d['caption']}")
        print(f"  category_id  : {d['category_id']}")
        print(f"  commodity_id : {d['commodity_id']}")
        print(f"  is_public    : {d['is_public']}")
        print(f"  views        : {d['view_count']}")


def step_update_post(profile_id: int, post_id: int) -> None:
    _section("Step 3 — Update post (PATCH)")
    print("  Leave a field blank to skip it.")

    new_caption = input("  New caption (blank to skip): ").strip() or None
    toggle_comments = _prompt("Toggle allow_comments? (y/N)", "N").lower()

    payload: dict = {}
    if new_caption:
        payload["caption"] = new_caption
    if toggle_comments == "y":
        # fetch current value first
        r0 = _hit("GET", f"/posts/{post_id}", params={"profile_id": profile_id})
        if r0.status_code == 200:
            current = r0.json()["data"]["allow_comments"]
            payload["allow_comments"] = not current
            print(f"  Toggling allow_comments: {current} -> {not current}")

    if not payload:
        print("  Nothing to update — skipped.")
        return

    r = _hit("PATCH", f"/posts/{post_id}", params={"profile_id": profile_id}, json=payload)
    result = _check(f"PATCH /posts/{post_id}", r, expect=200)
    if result:
        d = result["data"]
        print(f"  caption        : {d['caption']}")
        print(f"  allow_comments : {d['allow_comments']}")


def step_like_post(profile_id: int, post_id: int) -> None:
    _section("Step 4 — Like / unlike post")
    r = _hit("POST", f"/posts/{post_id}/like", params={"profile_id": profile_id})
    result = _check(f"POST /posts/{post_id}/like", r, expect=200)
    if result:
        d = result["data"]
        print(f"  liked={d['liked']}  like_count={d['like_count']}")

    if _prompt("Unlike it now? (y/N)", "N").lower() == "y":
        r2 = _hit("POST", f"/posts/{post_id}/like", params={"profile_id": profile_id})
        result2 = _check(f"POST /posts/{post_id}/like (unlike)", r2, expect=200)
        if result2:
            d = result2["data"]
            print(f"  liked={d['liked']}  like_count={d['like_count']}")


def step_comments(profile_id: int, post_id: int) -> None:
    _section("Step 5 — Comments")

    content = _prompt("Enter your comment", "Great post!")
    r = _hit("POST", f"/posts/{post_id}/comments",
             params={"profile_id": profile_id},
             json={"content": content})
    result = _check(f"POST /posts/{post_id}/comments", r, expect=201)
    comment_id = result["data"]["id"] if result else None
    if comment_id:
        print(f"  comment_id={comment_id}")

    # List comments
    r2 = _hit("GET", f"/posts/{post_id}/comments", params={"profile_id": profile_id})
    result2 = _check(f"GET /posts/{post_id}/comments", r2, expect=200)
    if result2:
        comments = result2["data"]
        print(f"  {len(comments)} comment(s):")
        for c in comments:
            print(f"    [{c['id']}] {c['content']}")

    # Delete
    if comment_id and _prompt("Delete your comment? (Y/n)", "Y").lower() != "n":
        r3 = _hit("DELETE", f"/posts/{post_id}/comments/{comment_id}",
                  params={"profile_id": profile_id})
        _check(f"DELETE /posts/{post_id}/comments/{comment_id}", r3, expect=204)


def step_share(profile_id: int, post_id: int) -> None:
    _section("Step 6 — Share post")
    if _prompt("Record a share? (Y/n)", "Y").lower() == "n":
        print("  Skipped.")
        return
    r = _hit("POST", f"/posts/{post_id}/share", params={"profile_id": profile_id})
    result = _check(f"POST /posts/{post_id}/share", r, expect=200)
    if result:
        print(f"  share_count={result['data']['share_count']}")


def step_save(profile_id: int, post_id: int) -> None:
    _section("Step 7 — Save post")
    if _prompt("Save this post? (Y/n)", "Y").lower() == "n":
        print("  Skipped.")
        return

    r = _hit("POST", f"/posts/{post_id}/save", params={"profile_id": profile_id})
    result = _check(f"POST /posts/{post_id}/save", r, expect=200)
    if result:
        print(f"  saved={result['data']['saved']}")

    # Show saved list
    r2 = _hit("GET", "/posts/saved", params={"profile_id": profile_id})
    result2 = _check("GET /posts/saved", r2, expect=200)
    if result2:
        print(f"  {len(result2['data'])} post(s) in your saved list")

    if _prompt("Unsave it now? (y/N)", "N").lower() == "y":
        r3 = _hit("POST", f"/posts/{post_id}/save", params={"profile_id": profile_id})
        result3 = _check(f"POST /posts/{post_id}/save (unsave)", r3, expect=200)
        if result3:
            print(f"  saved={result3['data']['saved']}")


def step_view_feed(profile_id: int) -> None:
    _section("Step 8 — View feed")
    r = _hit("GET", "/posts/", params={"profile_id": profile_id, "limit": 5})
    result = _check("GET /posts/ (feed)", r, expect=200)
    if result:
        posts = result["data"]
        print(f"  {len(posts)} post(s) in feed:")
        for p in posts:
            print(f"    [{p['id']}] {p['caption'][:50]}  likes={p['like_count']}  views={p['view_count']}")


def step_delete_post(profile_id: int, post_id: int) -> None:
    _section("Step 9 — Delete post")
    if _prompt(f"Delete post {post_id}? (Y/n)", "Y").lower() == "n":
        print(f"  Kept.  post_id={post_id}")
        return

    r = _hit("DELETE", f"/posts/{post_id}", params={"profile_id": profile_id})
    _check(f"DELETE /posts/{post_id}", r, expect=204)

    # Confirm 404
    r2 = _hit("GET", f"/posts/{post_id}", params={"profile_id": profile_id})
    ok_flag = r2.status_code == 404
    tag = PASS if ok_flag else FAIL
    print(f"  [{tag}] Confirm deleted  ->  HTTP {r2.status_code}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Vanijyaa post module interactive tester")
    parser.add_argument("--profile-id", type=int, help="Profile ID to use")
    parser.add_argument("--base", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    global BASE
    BASE = args.base

    profile_id = args.profile_id
    if profile_id is None:
        try:
            profile_id = int(input("Enter profile_id to use: ").strip())
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid profile_id.")
            sys.exit(1)

    print()
    print("=" * 58)
    print("  Vanijyaa -- Post Module Interactive Tester")
    print(f"  profile_id = {profile_id}   base = {BASE}")
    print("=" * 58)

    post_id = step_create_post(profile_id)
    step_view_post(profile_id, post_id)
    step_update_post(profile_id, post_id)
    step_like_post(profile_id, post_id)
    step_comments(profile_id, post_id)
    step_share(profile_id, post_id)
    step_save(profile_id, post_id)
    step_view_feed(profile_id)
    step_delete_post(profile_id, post_id)

    print()
    print("=" * 58)
    print("  Done.")
    print("=" * 58)
    print()


if __name__ == "__main__":
    main()
