from pydantic import BaseModel


class RecommendedPost(BaseModel):
    post_id: int
    score: float


class JobResult(BaseModel):
    status: str
    details: dict
