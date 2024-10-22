import logging
import os
import time

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    # Credentials from .env file
    username = os.getenv("NCS_USERNAME")
    password = os.getenv("NCS_PASSWORD")
    district_code = os.getenv("DISTRICT_CODE")

    login_url = (
        f"https://schoolsitefp.renweb.com/?districtCode={district_code}&schoolCode="
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Launch browser
        page = browser.new_page()

        # Navigate to the login page
        logging.info("Navigating to the login page...")
        page.goto(login_url)

        # Take a screenshot for debugging
        page.screenshot(path="page_loaded.png")
        logging.info("Screenshot saved as 'page_loaded.png'.")

        # Wait for the initial login button to be visible
        logging.info("Waiting for initial login button...")
        page.wait_for_selector("button.schoolsite-popup-button", timeout=30000)

        # Click the initial "LOG IN" button
        logging.info("Clicking the 'LOG IN' button and waiting for the new page...")
        with page.expect_popup() as popup_info:
            log_in_button = page.locator("button.schoolsite-popup-button")
            log_in_button.click()

        # Get the newly opened popup page
        popup_page = popup_info.value
        popup_page.wait_for_load_state("networkidle")
        logging.info("Popup page loaded.")

        # Fill in District Code
        logging.info("Filling in District Code...")
        popup_page.fill("input[id='rw-district-code']", district_code)

        # Fill in Username
        logging.info("Filling in Username...")
        popup_page.fill("input[id='rw-username']", username)

        # Fill in Password
        logging.info("Filling in Password...")
        popup_page.fill("input[id='rw-password']", password)

        # Wait for the "LOG IN" button to be visible and interactable
        logging.info("Waiting for 'LOG IN' button to be visible...")
        popup_page.wait_for_selector("input[id='next']", state="visible", timeout=60000)

        # Scroll the "LOG IN" button into view to ensure it's clickable
        logging.info("Scrolling 'LOG IN' button into view...")
        popup_page.locator("input[id='next']").scroll_into_view_if_needed()

        # Submit the form by clicking the "LOG IN" button
        logging.info("Clicking the 'LOG IN' button...")
        popup_page.click("input[id='next']")

        # Wait for a short delay to allow for redirection
        time.sleep(5)

        # Debug: Log the current URL after login
        current_url = popup_page.url
        logging.info(f"Current URL after login: {current_url}")

        # Check if the popup has redirected to the dashboard
        if "familyportal.renweb.com/en-us/school/index" in current_url:
            logging.info("Dashboard loaded successfully on popup page!")
            popup_page.screenshot(path="dashboard_loaded.png")
        else:
            logging.info("Popup page did not load the dashboard, checking parent page.")

            # Close the popup page
            popup_page.close()

            # Check the parent page
            page.wait_for_load_state("networkidle", timeout=10000)
            parent_url = page.url
            logging.info(f"Parent page current URL: {parent_url}")

            # Check if the parent page has redirected to the dashboard
            if "familyportal.renweb.com/en-us/school/index" in parent_url:
                logging.info("Dashboard loaded successfully on parent page!")
                page.screenshot(path="dashboard_loaded_parent.png")
            else:
                logging.error("Failed to load Dashboard on parent page.")

        # Close the browser
        browser.close()


if __name__ == "__main__":
    main()
