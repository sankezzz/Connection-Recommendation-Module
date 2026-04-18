"""
Post recommendation endpoints.

GET  /posts/recommendation/feed
POST /posts/recommendation/jobs/expiry
POST /posts/recommendation/jobs/popular-sync
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.modules.post.post_recommendation_module import service, jobs
from app.modules.post.post_recommendation_module.schemas import JobResult, RecommendedPost
from app.modules.profile.models import Profile

router = APIRouter(prefix="/posts/recommendation", tags=["post-recommendation"])


def _profile_id_for(user_id, db: Session) -> int:
    profile = db.query(Profile).filter(Profile.users_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found – complete onboarding first",
        )
    return profile.id


@router.get("/feed", response_model=list[RecommendedPost])
def get_feed(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    profile_id = _profile_id_for(user_id, db)
    try:
        results = service.get_recommended_posts(db, profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return results


@router.post("/jobs/expiry", response_model=JobResult)
def trigger_expiry_job(db: Session = Depends(get_db)):
    result = jobs.run_expiry_job(db)
    return JobResult(status="ok", details=result)


@router.post("/jobs/popular-sync", response_model=JobResult)
def trigger_popular_sync(db: Session = Depends(get_db)):
    result = jobs.run_popular_posts_sync(db)
    return JobResult(status="ok", details=result)
