import argparse
import asyncio
import logging
from src.browser.manager import BrowserManager
from src.flow.auth import AuthManager, AuthState
from src.config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def run_auth():
    manager = BrowserManager()
    settings.HEADLESS = False
    await manager.start()
    page = await manager.get_page()

    logger.info(f"Navigating to {settings.FLOW_URL}...")
    await page.goto(settings.FLOW_URL)

    status = await AuthManager.check_auth_status(page)
    logger.info(f"Current Status: {status}")

    if status != AuthState.AUTHENTICATED:
        logger.info("Waiting for manual login... Please log in to the opened browser window.")
        await AuthManager.wait_for_manual_auth(page, timeout=600000)

    logger.info("Auth check complete. Closing browser.")
    await manager.stop()

def main():
    parser = argparse.ArgumentParser(description="Google Flow Automation Bot V2 CLI")
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start the FastAPI backend and job runner")
    auth_parser = subparsers.add_parser("auth", help="Perform manual browser authentication")

    args = parser.parse_args()

    if args.command == "start":
        from src.main import main as start_main
        start_main()
    elif args.command == "auth":
        asyncio.run(run_auth())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
