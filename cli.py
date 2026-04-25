#!/usr/bin/env python3
import argparse
import os
import sys
import sqlite3
import subprocess
import requests
import yaml
import time
import socket

# Add bot directory to path to reuse modules seamlessly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_DIR = os.path.join(BASE_DIR, "Gemini-IRC-bot")
sys.path.insert(0, BOT_DIR)

# Auto-activate virtual environment
venv_path = os.path.join(BASE_DIR, ".venv")
if "VIRTUAL_ENV" not in os.environ and os.path.exists(venv_path):
    venv_python = os.path.join(venv_path, "bin", "python")
    os.environ["VIRTUAL_ENV"] = venv_path
    os.execl(venv_python, venv_python, *sys.argv)

from link_preview import get_link_preview

# Use the data directory for the cache database (matching container logic)
CACHE_DB_PATH = os.path.join(BASE_DIR, "data", "cache.db")

def scrape(args):
    url = args.url
    force_heavy = args.heavy
    print(f"Scraping {url} (Heavy: {force_heavy})...")
    
    # Ensure data dir exists
    os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)
    os.environ["CACHE_DB_PATH"] = CACHE_DB_PATH
    
    # Needs CRAWLER_API_URL set to localhost if hitting the containerized API from host
    if "CRAWLER_API_URL" not in os.environ:
        os.environ["CRAWLER_API_URL"] = "http://localhost:8000/resolve"
        
    try:
        preview = get_link_preview(url, force_heavy=force_heavy)
        if preview:
            print("\n--- Preview Output ---")
            print(preview)
            print("----------------------")
        else:
            print("Failed to generate preview. The page might be unreachable or requires heavy scraping.")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the crawler API.")
        print("Hint: If you are using --heavy, make sure the API container is running.")
        print("   Run: ./cli.py stack up")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

def get_bot_container():
    res = subprocess.run(["podman", "ps", "-q", "-f", "name=bot"], capture_output=True, text=True)
    cid = res.stdout.strip().split('\n')[0]
    if not cid:
        print("Error: Bot container is not running. Start the stack first (`./cli.py stack up`).")
        sys.exit(1)
    return cid

def cache_view(args):
    cid = get_bot_container()
    python_script = """
import sqlite3, time
try:
    with sqlite3.connect('/app/data/cache.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT url, timestamp, is_heavy FROM url_cache ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        if not rows:
            print("Cache is empty.")
        else:
            print(f"{'Timestamp':<20} | {'Type':<8} | {'URL'}")
            print("-" * 80)
            for row in rows:
                url, ts, is_heavy = row
                time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
                type_str = "HEAVY" if is_heavy else "FAST"
                print(f"{time_str:<20} | {type_str:<8} | {url}")
except Exception as e:
    print(f"Error: {e}")
"""
    subprocess.run(["podman", "exec", cid, "python", "-c", python_script])

def cache_clear(args):
    cid = get_bot_container()
    python_script = """
import sqlite3
try:
    with sqlite3.connect('/app/data/cache.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM url_cache")
        conn.commit()
    print("Cache cleared successfully.")
except Exception as e:
    print(f"Error clearing cache: {e}")
"""
    subprocess.run(["podman", "exec", cid, "python", "-c", python_script])

def stack_cmd(args):
    cmd = args.action
    compose_cmd = ["podman-compose"]
    
    # Set the containers.conf environment variable just like manage.sh
    env = os.environ.copy()
    env["CONTAINERS_CONF"] = os.path.join(BASE_DIR, "containers.conf")
    
    # Check if podman-compose is installed
    import shutil
    if not shutil.which("podman-compose"):
        print("Error: 'podman-compose' is not installed or not in PATH.")
        print("Hint: Install it via your package manager or pip (e.g., pip install podman-compose).")
        sys.exit(1)
    
    if cmd == "up":
        subprocess.run(compose_cmd + ["up", "-d", "--build"], env=env)
    elif cmd == "down":
        subprocess.run(compose_cmd + ["down"], env=env)
    elif cmd == "logs":
        subprocess.run(compose_cmd + ["logs", "-f"], env=env)
    elif cmd == "status":
        subprocess.run(compose_cmd + ["ps"], env=env)

def broadcast(args):
    message = args.message
    cid = get_bot_container()
    
    # Escape quotes for the python script
    safe_msg = message.replace('"', '\\"')
    python_script = f"""
import sqlite3
try:
    with sqlite3.connect('/app/data/cache.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO broadcast_queue (message) VALUES (?)", ("{safe_msg}",))
        conn.commit()
    print("Queued broadcast message: '{message}'")
except Exception as e:
    print(f"Error queuing message: {{e}}")
"""
    subprocess.run(["podman", "exec", cid, "python", "-c", python_script])

def main():
    description = """
Selenium Crawler & IRC Bot CLI
------------------------------
A unified command-line interface to manage your crawler infrastructure,
test the scraping engine directly, and broadcast messages to IRC.
"""
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    subparsers = parser.add_subparsers(title="Available Commands", dest="command", required=True)

    # Scrape command
    scrape_help = "Scrape a URL to test the preview output locally without IRC.\nExample: ./cli.py scrape https://example.com"
    scrape_parser = subparsers.add_parser("scrape", help=scrape_help, description=scrape_help)
    scrape_parser.add_argument("url", help="The full URL to scrape (e.g., https://example.com)")
    scrape_parser.add_argument("--heavy", action="store_true", help="Force the heavy AI Selenium crawler instead of the fast BeautifulSoup scraper")
    scrape_parser.set_defaults(func=scrape)

    # Cache commands
    cache_help = "Manage the SQLite cache database that stores previous URL previews."
    cache_parser = subparsers.add_parser("cache", help=cache_help, description=cache_help)
    cache_sub = cache_parser.add_subparsers(title="Cache Actions", dest="cache_action", required=True)
    
    cache_view_parser = cache_sub.add_parser("view", help="View a formatted table of all cached URLs and timestamps")
    cache_view_parser.set_defaults(func=cache_view)
    
    cache_clear_parser = cache_sub.add_parser("clear", help="Clear all entries from the cache database to force fresh scrapes")
    cache_clear_parser.set_defaults(func=cache_clear)

    # Stack commands
    stack_help = "Manage the podman-compose container stack (API and Bot).\nExample: ./cli.py stack up"
    stack_parser = subparsers.add_parser("stack", help=stack_help, description=stack_help)
    stack_parser.add_argument("action", choices=["up", "down", "logs", "status"], 
                              help="Action to perform:\n"
                                   "  up     - Start the containers in the background\n"
                                   "  down   - Stop and remove the containers\n"
                                   "  logs   - Follow the log output of the containers\n"
                                   "  status - View the running status of the containers")
    stack_parser.set_defaults(func=stack_cmd)

    # Broadcast command
    broadcast_help = "Broadcast a message directly to all IRC channels configured in config.yaml.\nExample: ./cli.py broadcast \"Hello World!\""
    broadcast_parser = subparsers.add_parser("broadcast", help=broadcast_help, description=broadcast_help)
    broadcast_parser.add_argument("message", help="The string message to send")
    broadcast_parser.set_defaults(func=broadcast)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
