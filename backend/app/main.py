"""FastAPI application entrypoint.

Creates the app, allows the frontend to call it from the browser (CORS) and
registers the routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin_users, attachments, auth, kerkesa, roles
from app.core import config

app = FastAPI(title="inspektorati-ai")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(admin_users.router)
app.include_router(kerkesa.router)  # public citizen portal (no login)
app.include_router(attachments.router)
