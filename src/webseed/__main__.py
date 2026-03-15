"""webseed — uvicorn entrypoint."""

import os

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    import uvicorn

    from webseed.api.app import create_app

    database_url = os.environ.get("DATABASE_URL", "postgresql://webseed:webseed@localhost:5432/webseed")
    results_dir = os.environ.get("RESULTS_DIR", "results")

    app = create_app(database_url, results_dir)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
