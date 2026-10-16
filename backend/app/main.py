"""FastAPI application entrypoint.

Holds the bare application instance only. Routes and features are added later.
"""

from fastapi import FastAPI

app = FastAPI(title="inspektorati-ai")
