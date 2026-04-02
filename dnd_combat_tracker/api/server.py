import uvicorn

from dnd_combat_tracker.config import settings


def main():
    uvicorn.run(
        "dnd_combat_tracker.api.app:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
