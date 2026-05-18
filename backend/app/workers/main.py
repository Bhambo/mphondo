"""Arq worker entry point.

Start with: python -m app.workers.main
Or via Docker Compose: command: python -m app.workers.main
"""

from arq import run_worker

from app.workers.tasks import WorkerSettings


def main() -> None:
    run_worker(WorkerSettings)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
