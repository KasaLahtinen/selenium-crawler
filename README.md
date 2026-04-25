# Selenium Crawler IRC Bot

A powerful, robust IRC bot that detects URLs in chat channels and automatically generates rich link previews. Built with Python, it utilizes a hybrid scraping architecture: a blazingly fast `BeautifulSoup` miniscraper for standard static web pages, backed by a heavyweight headless Selenium crawler powered by an AI language model for Javascript-rendered sites and cookie walls.

## 🚀 Features

- **Hybrid Scraping Architecture**: 
  - Uses `requests` and `BeautifulSoup` for instant HTML parsing.
  - Automatically falls back to a headless Chromium Selenium instance running behind a FastAPI wrapper when cookie walls or Javascript rendering are detected.
- **Explicit Heavy Commands**: Users can force the AI crawler to fetch a URL using the `!heavy <url>` command.
- **SQLite Caching**: Link previews are cached in a lightweight SQLite database for 24 hours, dramatically reducing redundant network requests.
- **Rate Limiting Protection**: Built-in cooldowns protect against IRC excess-flood disconnects (5 seconds for standard scrapes, 30 seconds for heavy scrapes).
- **Containerized Orchestration**: The entire stack is containerized and orchestrated with Podman/Docker Compose, complete with automatic healthchecks and dependent startup sequencing.

## 🏗️ Architecture

The project is split into three interconnected container services:

1. **bot**: The Python IRC bot (using standard sockets) that connects to IRC, listens for URLs, handles caching and rate-limiting, and queries the API for heavy URLs.
2. **api**: A FastAPI service that manages the heavy crawler queue and interacts with the remote browser.
3. **selenium**: An official `docker.io/selenium/standalone-chromium` container that provides a remote WebDriver for the API to control.

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
   - Create a `.env` file in the root directory if you need to override compose variables.
   - Edit the IRC configuration in `Gemini-IRC-bot/config.yaml` to set your bot's nickname, server, and channels to join.

3. **Start the Stack**:
   Use the provided management script to spin up the entire multi-container environment:
   ```bash
   ./manage.sh start
   ```
   *Note: The bot container will wait automatically until the Selenium browser and the API are fully healthy before connecting to your IRC server.*

4. **Stop the Stack**:
   ```bash
   ./manage.sh stop
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
