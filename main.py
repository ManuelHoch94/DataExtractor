"""Application entry point.

Run with:
    python main.py
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os

import uvicorn

from data_extractor.api.app import create_app

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

app = create_app()


def main() -> None:
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
