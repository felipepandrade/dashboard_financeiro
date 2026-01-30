
import logging
from typing import Dict, Optional, List
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class OracleAuthService:
    """
    Service to handle authentication with Oracle Fusion Cloud via Browser Automation.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        # The welcome page usually contains this pattern
        self.success_url_pattern = "FuseWelcome" 

    def login_and_get_cookies(self) -> Optional[Dict[str, str]]:
        """
        Launches a visible browser for the user to login.
        Waits for the successful redirect to the Oracle Dashboard.
        Captures and returns the cookies.
        """
        print("Launching Browser for Oracle Login...")
        
        with sync_playwright() as p:
            # Launch headful browser (visible to user) - Using Edge as requested
            # args=['--start-maximized'] is helpful for user experience
            browser = p.chromium.launch(headless=False, channel="msedge", args=['--start-maximized'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            # Additional permissions can be granted here if needed
            
            page = context.new_page()
            
            try:
                # Navigate to the Oracle Login/Home Page
                print(f"Navigating to: {self.base_url}")
                page.goto(self.base_url)

                # Wait for the user to complete the login process (SSO, MFA, etc.)
                # We identify success when the URL contains 'FuseWelcome'
                # Timeout is set high (e.g., 300 seconds = 5 minutes) to give user time
                print("Waiting for user to complete login (timeout: 5 minutes)...")
                
                # Check for the target URL pattern
                page.wait_for_url(f"**/{self.success_url_pattern}**", timeout=300000)
                
                print("Login detected! Capturing session...")
                
                # Get all cookies
                cookies_list = context.cookies()
                
                # Convert to simple key-value dict for requests
                cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
                
                print(f"Captured {len(cookies_dict)} cookies.")
                return cookies_dict

            except Exception as e:
                print(f"Error during login flow: {e}")
                return None
            
            finally:
                # Always close the browser
                print("Closing browser...")
                browser.close()

if __name__ == "__main__":
    # Test execution
    BASE_URL = "https://emcf.fa.us2.oraclecloud.com"
    auth = OracleAuthService(BASE_URL)
    cookies = auth.login_and_get_cookies()
    if cookies:
        print("Success! Cookies keys:", list(cookies.keys()))
