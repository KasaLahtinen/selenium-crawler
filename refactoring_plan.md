# Project Refactoring & Scaling Roadmap

## Phase 1: Observability & Standards (The Safety Net) [COMPLETED]
*Before tearing apart `bot.py`, we need a safety net. If something breaks, we need clear logs.*

* **Step 1: Implement Unified Logging.** Replace all scattered `print()` and `logging.error()` calls across `bot.py`, `commands.py`, and `main.py` with **Loguru**. This provides thread-safe, color-coded, and timestamped container logs.
* **Step 2: Introduce Linting.** Create a `pyproject.toml` file and configure **Ruff**. This ensures we don't leave behind unused imports, undefined variables, or formatting inconsistencies as we move code around.

## Phase 2: Container Stability (The Infrastructure) [COMPLETED]
*Ensure the containers themselves are fully aware of each other's states.*

* **Step 3: Container Healthchecks.** Update `podman-compose.yml` and the `Containerfile`s to include native health checks. Configure the `bot` container to wait until the `api` container explicitly reports that Uvicorn is healthy and listening.

## Phase 3: Decoupling Architecture (Taming the God Object) [COMPLETED]
*With logging and stable containers in place, safely refactor the Python codebase.*

* **Step 4: Extract URL Logic.** Create a new module named `link_preview.py`. Surgically extract `_get_url_info`, the `BeautifulSoup` HTML parsing, and the heavy crawler HTTP fallback out of `bot.py`. `bot.py` will simply pass the detected URL to this new module and await a string response.

## Phase 4: Optimization & Protection (Scaling Up) [COMPLETED]
*With a clean, decoupled architecture, easily inject middleware for performance and security.*

* **Step 5: Implement SQLite Caching.** Inside `link_preview.py`, add a lightweight SQLite cache. Before executing `requests.get` or hitting the FastAPI crawler, the bot checks the database. If the URL was summarized in the last 24 hours, it returns the cached response instantly.
* **Step 6: Rate Limiting.** Add a token-bucket or cooldown dictionary to `bot.py` to ignore users who spam URLs too quickly, preventing IRC flood disconnects and API abuse.
