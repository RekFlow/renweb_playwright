import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)


class GradeScraperException(Exception):
    """Custom exception for grade scraping errors"""

    pass


class RenWebScraper:
    def __init__(self):
        self.username = os.getenv("NCS_USERNAME")
        self.password = os.getenv("NCS_PASSWORD")
        self.district_code = os.getenv("DISTRICT_CODE")
        self.base_url = f"https://schoolsitefp.renweb.com/?districtCode={self.district_code}&schoolCode="
        self.logged_in = False

    def login(self, page: Page) -> None:
        """Handle the login process"""
        try:
            logging.info("Initiating login process...")
            page.goto(self.base_url)

            # Wait for and click initial login button
            page.wait_for_selector("button.schoolsite-popup-button", timeout=30000)
            with page.expect_popup() as popup_info:
                page.click("button.schoolsite-popup-button")

            # Handle login popup
            popup_page = popup_info.value
            popup_page.wait_for_load_state("networkidle")

            # Fill login form
            popup_page.fill("input[id='rw-district-code']", self.district_code)
            popup_page.fill("input[id='rw-username']", self.username)
            popup_page.fill("input[id='rw-password']", self.password)

            # Submit login
            popup_page.click("input[id='next']")
            popup_page.wait_for_load_state("networkidle")

            # Verify login success
            if "familyportal.renweb.com/en-us/school/index" in popup_page.url:
                self.logged_in = True
                logging.info("Login successful")
                return popup_page
            else:
                raise GradeScraperException("Login failed - unexpected redirect URL")

        except PlaywrightTimeout as e:
            logging.error(f"Timeout during login: {str(e)}")
            raise GradeScraperException(f"Login process timed out: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error during login: {str(e)}")
            raise GradeScraperException(f"Login failed: {str(e)}")

    def navigate_to_grades(self, page: Page) -> None:
        """Navigate to the grades section"""
        try:
            logging.info("Navigating to grades page...")

            # Wait for and click the grades navigation link
            page.wait_for_selector("a[href*='grades']", timeout=30000)
            page.click("a[href*='grades']")

            # Wait for grades content to load
            page.wait_for_selector(".grades-container", timeout=30000)
            logging.info("Successfully navigated to grades page")

        except PlaywrightTimeout as e:
            logging.error(f"Timeout while navigating to grades: {str(e)}")
            raise GradeScraperException("Failed to navigate to grades page")
        except Exception as e:
            logging.error(f"Error navigating to grades: {str(e)}")
            raise GradeScraperException(f"Navigation failed: {str(e)}")

    def extract_grades(self, page: Page) -> List[Dict]:
        """Extract grades data from the page"""
        try:
            logging.info("Extracting grades data...")

            # Wait for the grades table to be visible
            page.wait_for_selector("table.grades-table", timeout=30000)

            # Extract grades data using JavaScript evaluation
            grades_data = page.evaluate(
                """
                () => {
                    const rows = Array.from(document.querySelectorAll('table.grades-table tr'));
                    return rows.slice(1).map(row => {
                        const cells = Array.from(row.querySelectorAll('td'));
                        return {
                            subject: cells[0]?.textContent?.trim(),
                            current_grade: cells[1]?.textContent?.trim(),
                            letter_grade: cells[2]?.textContent?.trim(),
                            last_updated: cells[3]?.textContent?.trim()
                        };
                    });
                }
            """
            )

            logging.info(f"Successfully extracted {len(grades_data)} grade entries")
            return grades_data

        except PlaywrightTimeout as e:
            logging.error(f"Timeout while extracting grades: {str(e)}")
            raise GradeScraperException("Failed to extract grades data")
        except Exception as e:
            logging.error(f"Error extracting grades: {str(e)}")
            raise GradeScraperException(f"Grade extraction failed: {str(e)}")

    def save_grades(self, grades_data: List[Dict]) -> None:
        """Save grades data to a file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"grades_{timestamp}.json"

            import json

            with open(filename, "w") as f:
                json.dump(grades_data, f, indent=4)

            logging.info(f"Grades data saved to {filename}")

        except Exception as e:
            logging.error(f"Error saving grades data: {str(e)}")
            raise GradeScraperException(f"Failed to save grades data: {str(e)}")

    def run(self) -> Optional[List[Dict]]:
        """Main execution method"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # Execute scraping process
                logged_in_page = self.login(page)
                self.navigate_to_grades(logged_in_page)
                grades_data = self.extract_grades(logged_in_page)
                self.save_grades(grades_data)

                browser.close()
                return grades_data

        except GradeScraperException as e:
            logging.error(f"Scraping failed: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return None


def main():
    scraper = RenWebScraper()
    grades = scraper.run()

    if grades:
        logging.info("Scraping completed successfully")
    else:
        logging.error("Scraping failed")


if __name__ == "__main__":
    main()
