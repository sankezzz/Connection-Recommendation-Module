from fastapi import FastAPI
from app.modules.connections.routes import connections
from app.modules.connections.routes import recommendations
from app.modules.auth.router import router as auth_router
from app.modules.profile.router import router as profile_router
from app.modules.post.router import router as post_router

app = FastAPI(title="Vanijyaa API")

# Auth module
app.include_router(auth_router)

# Profile module
app.include_router(profile_router)

# Post module
app.include_router(post_router)

# Connections & recommendations (old async routes)
app.include_router(recommendations.router)
app.include_router(connections.router)
