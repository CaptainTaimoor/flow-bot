from playwright.async_api import Page
import logging
import asyncio

logger = logging.getLogger(__name__)

class AuthState(str):
    AUTHENTICATED = "AUTHENTICATED"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    SECURITY_VERIFICATION_REQUIRED = "SECURITY_VERIFICATION_REQUIRED"
    UNKNOWN = "UNKNOWN"

class AuthManager:
    @staticmethod
    async def check_auth_status(page: Page) -> str:
        """
        Checks if the user is authenticated.
        Navigates past the landing page if necessary.
        """
        try:
            # Let the page load
            await asyncio.sleep(3)
            
            # If there's an entry button on a landing page, click it to see if it triggers login
            btn = page.locator("button:has-text('Create with Google Flow'), button:has-text('Try Google Flow'), a:has-text('Sign in')").first
            if await btn.count() > 0:
                logger.info("Found landing page entry button. Clicking to test auth...")
                await btn.click()
                await asyncio.sleep(5)
                
            url = page.url
            if "accounts.google.com" in url or "ServiceLogin" in url:
                return AuthState.NOT_AUTHENTICATED
            
            # If we are on the tool page (e.g. aitestkitchen.../tools/flow) or flow.google.com 
            # and no login prompt is visible, we assume authenticated.
            return AuthState.AUTHENTICATED
                
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
            return AuthState.UNKNOWN

    @staticmethod
    async def wait_for_manual_auth(page: Page, timeout: int = 300000):
        """
        Pauses and waits for the user to manually log in.
        It waits for the URL to leave the accounts.google.com domain and return to the app.
        """
        logger.info("Waiting for manual authentication. Please complete login in the browser window.")
        try:
            # Wait until we are no longer on the accounts page
            async def is_authenticated():
                url = page.url
                return "accounts.google.com" not in url and "ServiceLogin" not in url
                
            for _ in range(int(timeout / 1000)):
                if await is_authenticated():
                    logger.info("Authentication complete. URL changed to application.")
                    await asyncio.sleep(3) # Let the app load
                    return True
                await asyncio.sleep(1)
                
            logger.error("Manual authentication timed out.")
            return False
        except Exception as e:
            logger.error(f"Manual authentication failed: {e}")
            return False
