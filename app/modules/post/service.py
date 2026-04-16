from sqlalchemy.orm import Session
from uuid import UUID


def get_my_posts(db: Session, profile_id: UUID, limit: int = 20, offset: int = 0) -> list:
    # TODO: implement full post fetching
    return []


def get_saved_posts(db: Session, profile_id: UUID, limit: int = 20, offset: int = 0) -> list:
    # TODO: implement saved posts
    return []
