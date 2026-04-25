# Selenium Crawler IRC Bot

A powerful, robust IRC bot that detects URLs in chat channels and automatically generates rich link previews. Built with Python, it utilizes a hybrid scraping architecture: a blazingly fast `BeautifulSoup` miniscraper for standard static web pages, backed by a heavyweight headless Selenium crawler powered by an AI language model for Javascript-rendered sites and cookie walls.

[![Trivy Container Vulnerability Scanner](https://github.com/KasaLahtinen/selenium-crawler/actions/workflows/trivy.yml/badge.svg)](https://github.com/KasaLahtinen/selenium-crawler/actions/workflows/trivy.yml)
[![CodeQL Vulnerability Scanning](https://github.com/KasaLahtinen/selenium-crawler/actions/workflows/codeql.yml/badge.svg)](https://github.com/KasaLahtinen/selenium-crawler/actions/workflows/codeql.yml)
[![OSV-Scanner](https://github.com/KasaLahtinen/selenium-crawler/actions/workflows/osv-scanner.yml/badge.svg)](https://github.com/KasaLahtinen/selenium-crawler/actions/workflows/osv-scanner.yml)
## 🚀 Features

- **Hybrid Scraping Architecture**: 
  - Uses `requests` and `BeautifulSoup` for instant HTML parsing.
  - Automatically falls back to a headless Chromium Selenium instance running behind a FastAPI wrapper when cookie walls or Javascript rendering are detected.
- **Local Threat Detection**: Protects channels by instantly checking posted URLs against a local SQLite database synced with industry-standard threat feeds (e.g., URLhaus) to block malware distribution.
- **Telegram Cross-Publishing**: Automatically mirrors IRC URL previews into configured Telegram chats using a unified SQLite broadcast queue.
- **Explicit Heavy Commands**: Users can force the AI crawler to fetch a URL using the `!heavy <url>` command.
- **SQLite Caching**: Link previews are cached in a lightweight SQLite database for 24 hours, dramatically reducing redundant network requests.
- **Rate Limiting Protection**: Built-in cooldowns protect against IRC excess-flood disconnects (5 seconds for standard scrapes, 30 seconds for heavy scrapes).
- **Containerized Orchestration**: The entire stack is orchestrated with Podman/Docker Compose and uses hardened Alpine-based images for enhanced security.

## 🏗️ Architecture

The project is split into four interconnected container services:

1. **bot**: The Python IRC bot that connects to IRC, listens for URLs, handles threat-checking, and queries the API. It places results into a shared SQLite broadcast queue.
2. **telegram-bot**: A Python Telegram bot that consumes the shared SQLite broadcast queue and relays URL previews to configured Telegram chats.
3. **api**: A FastAPI service that manages the heavy crawler queue and interacts with the remote browser.
4. **selenium**: An official `docker.io/selenium/standalone-chromium` container that provides a remote WebDriver for the API to control.

## 📁 Project Structure

Below is a breakdown of the key files and directories found in the root of the project:

- **`cli.py`**: The primary Python command-line interface for managing the stack (`start`, `stop`, `restart`, `logs`). It provides a clean, user-friendly output and orchestrates the containers.
- **`main.py`**: The FastAPI backend application that receives URL requests and manages the queue for the heavy Selenium scraper.
- **`crawler.py`**: Contains the core Selenium Webdriver logic and AI summarization used by the API to process Javascript-heavy websites.
- **`podman-compose.yml`**: The orchestration file that defines the multi-container environment (`api`, `bot`, `telegram-bot`, `selenium`).
- **`Containerfile.api`** & **`Containerfile.bot`**: The OCI-compliant build instructions (Dockerfiles) for the Alpine-based API and IRC/Telegram Bot images respectively.
- **`Gemini-IRC-bot/`**: A Git submodule containing the core IRC and Telegram bot logic, SQLite caching, and URL parsing mechanisms.
- **`requirements.txt`** & **`requirements.in`**: Pinned Python dependencies for the API service with secure hashes.
- **`pyproject.toml`**: Python project configuration (e.g., formatting and linting tools like Ruff).
- **`.env`**: Contains environment variables such as API keys and bot tokens.
- **`.gitmodules`**: Git configuration linking the `Gemini-IRC-bot` submodule to the parent repository.
- **`containers.conf`**: Configuration for container behavior.
- **`manage.sh`**: A historic bash wrapper script used previously to manage the multi-container environment (now superseded by `cli.py`).
- **`start-pod.sh`** & **`stop-pod.sh`**: Historic shell scripts retained for reference/notes on starting and stopping pods manually.
- **`fix_bot.py`** & **`github_init.sh`**: One-off historic utility scripts retained for later reference.

## ⚙️ Prerequisites

- **Podman** or **Docker**
- `podman-compose` or `docker-compose`

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/KasaLahtinen/selenium-crawler.git
   cd selenium-crawler
   ```

2. **Configure the Environment**:
   - Copy `.env.example` to `.env` in the root directory and edit it to set your API keys and override compose variables.
   - Copy `Gemini-IRC-bot/config.example.yaml` to `Gemini-IRC-bot/config.yaml` and edit it to set your bot's nickname, server, and channels to join.

3. **Start the Stack**:
   Use the provided Python CLI tool to spin up the entire multi-container environment:
   ```bash
   ./cli.py stack up
   ```
   *Note: The bot container will wait automatically until the Selenium browser and the API are fully healthy before connecting to your IRC server.*

4. **Stop the Stack**:
   ```bash
   ./cli.py stack down
   ```

5. **View Logs**:
   ```bash
   ./cli.py stack logs
   ```

## 📖 Usage

Once the bot connects to your configured IRC channels:

- **Automatic Previews**: Just post a link in the chat.
  ```
  <User> Check this out: https://example.com
  <Bot> Example Domain
  <Bot> This domain is for use in illustrative examples in documents.
  ```
- **Force AI Crawler**: Use the `!heavy` command for stubborn sites.
  ```
  <User> !heavy https://javascript-heavy-site.com
  <Bot> AI Summary
  <Bot> [Generated summary of the page content]
  ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
