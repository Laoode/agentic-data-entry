"""Run the embedding service: ``python -m embed`` (or ``uvicorn embed.app:app``)."""

import uvicorn

from embed.settings import get_settings


def main() -> None:
    cfg = get_settings()
    uvicorn.run("embed.app:app", host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
