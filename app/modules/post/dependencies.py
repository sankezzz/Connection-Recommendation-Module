from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.modules.profile.models import Profile


def get_current_profile_id(
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> int:
    row = db.query(Profile.id).filter(Profile.users_id == user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found for this user")
    return row[0]
