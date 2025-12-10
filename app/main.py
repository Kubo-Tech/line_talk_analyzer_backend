"""FastAPI application entry point.

This module serves as the main entry point for the LINE Talk Analyzer Backend.
"""

from fastapi import FastAPI

app = FastAPI(
    title="LINE Talk Analyzer",
    version="1.0.0",
    description="Backend API for analyzing LINE chat history",
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint for health check.

    Returns:
        dict[str, str]: Status message
    """
    return {"message": "LINE Talk Analyzer API is running"}
