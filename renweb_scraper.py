import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)

# Global credentials and URLs
USERNAME = os.getenv("NCS_USERNAME")
PASSWORD = os.getenv("NCS_PASSWORD")
DISTRICT_CODE = os.getenv("DISTRICT_CODE")
LOGIN_URL = f"https://schoolsitefp.renweb.com/?districtCode={DISTRICT_CODE}&schoolCode="

# Create output directory for debug files
DEBUG_DIR = Path("debug_output")
DEBUG_DIR.mkdir(exist_ok=True)


def save_debug_file(content, filename, is_binary=False):
    """Save debug content to file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = DEBUG_DIR / f"{filename}_{timestamp}"
    if is_binary:
        filepath = filepath.with_suffix(".png")
        with open(filepath, "wb") as f:
            f.write(content)
    else:
        filepath = filepath.with_suffix(".html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    logging.info(f"Saved debug file: {filepath}")


def save_data(data, filename):
    """Save scraped data to a JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = DEBUG_DIR / f"{filename}_{timestamp}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Data saved to {filepath}")


def extract_grades_from_iframe(frame):
    """Extract grade information from an iframe"""
    try:
        # Wait for page content
        frame.wait_for_selector("body", state="attached", timeout=30000)

        # Save frame content for debugging
        frame_content = frame.content()
        save_debug_file(frame_content, "frame_content_debug")

        # Get basic course info if available
        course_info = {"course_name": "", "teacher_name": "", "term": ""}
        try:
            header_text = frame.locator("body").first.inner_text().split("\n")[0:3]
            course_info = {
                "course_name": header_text[0] if len(header_text) > 0 else "",
                "teacher_name": header_text[1] if len(header_text) > 1 else "",
                "term": header_text[2] if len(header_text) > 2 else "",
            }
        except Exception as e:
            logging.error(f"Error extracting course info: {str(e)}")

        grades_data = {"course_info": course_info, "categories": {}, "term_grade": None}

        current_category = None

        # Get all tables
        tables = frame.locator("table").all()

        for table in tables:
            try:
                table_text = table.inner_text().strip().lower()

                # Check if this is a category header
                if any(
                    cat in table_text
                    for cat in ["classwork", "homework", "projects", "quizzes", "tests"]
                ):
                    current_category = table_text.split()[-1].strip()
                    grades_data["categories"][current_category] = {
                        "assignments": [],
                        "category_average": None,
                    }
                    continue

                # Get headers
                headers = [
                    cell.inner_text().strip().lower()
                    for cell in table.locator("th,td").first.all()
                ]

                # If this looks like an assignment table
                if "assignment" in headers:
                    rows = table.locator("tr").all()

                    for row in rows[1:]:  # Skip header row
                        cells = row.locator("td").all()
                        cell_texts = [cell.inner_text().strip() for cell in cells]

                        # Skip empty rows
                        if not any(cell_texts):
                            continue

                        # Check if this is a category average row
                        if "category average" in cell_texts[0].lower():
                            if current_category and len(cell_texts) > 1:
                                grades_data["categories"][current_category][
                                    "category_average"
                                ] = cell_texts[1]
                            continue

                        # Check if this is the term grade
                        if "term grade" in cell_texts[0].lower():
                            if len(cell_texts) > 2:
                                grades_data["term_grade"] = {
                                    "score": cell_texts[1],
                                    "letter": (
                                        cell_texts[2] if len(cell_texts) > 2 else ""
                                    ),
                                }
                            continue

                        # Regular assignment row
                        if current_category and len(cell_texts) >= 5:
                            assignment = {
                                "name": cell_texts[0],
                                "points": cell_texts[1],
                                "max_points": cell_texts[2],
                                "percentage": (
                                    str(
                                        round(
                                            float(cell_texts[1])
                                            / float(cell_texts[2])
                                            * 100,
                                            2,
                                        )
                                    )
                                    if cell_texts[1] and cell_texts[2]
                                    else None
                                ),
                                "status": cell_texts[4],
                                "due_date": (
                                    cell_texts[5] if len(cell_texts) > 5 else None
                                ),
                            }
                            grades_data["categories"][current_category][
                                "assignments"
                            ].append(assignment)

            except Exception as e:
                logging.error(f"Error processing table: {str(e)}")
                continue

        return (
            grades_data
            if grades_data["categories"] or grades_data["term_grade"]
            else None
        )

    except Exception as e:
        logging.error(f"Error extracting grades from iframe: {str(e)}")
        return None


def scrape_grades(page):
    """Navigate to and scrape grades data"""
    try:
        # Navigate directly to grades page
        base_url = page.url.split("/en-us")[0]
        grades_url = f"{base_url}/en-us/student/grades"

        logging.info(f"Navigating to grades URL: {grades_url}")
        page.goto(grades_url)

        # Wait for page and frames to load
        page.wait_for_load_state("networkidle")
        time.sleep(10)

        # Save initial page state
        save_debug_file(page.content(), "initial_grades_page")
        screenshot_bytes = page.screenshot(full_page=True)
        save_debug_file(screenshot_bytes, "initial_grades_page", is_binary=True)

        # Get all frames
        frames = page.frames
        all_courses_data = []

        for frame in frames:
            try:
                if frame.url and (
                    "grades.cfm" in frame.url.lower() or "/GradeBook/" in frame.url
                ):
                    logging.info(f"Processing grades frame: {frame.url}")
                    frame_data = extract_grades_from_iframe(frame)
                    if frame_data:
                        all_courses_data.append(frame_data)
            except Exception as e:
                logging.error(f"Error processing frame: {str(e)}")

        return all_courses_data if all_courses_data else None

    except Exception as e:
        logging.error(f"Error in scrape_grades: {str(e)}")
        return None


def perform_login(page):
    """Handle the login process"""
    try:
        # Navigate to login page
        logging.info("Navigating to login page...")
        page.goto(LOGIN_URL)

        # Wait for and click initial login button
        logging.info("Waiting for initial login button...")
        page.wait_for_selector("button.schoolsite-popup-button", timeout=30000)

        with page.expect_popup() as popup_info:
            page.locator("button.schoolsite-popup-button").click()

        # Handle login popup
        popup_page = popup_info.value
        popup_page.wait_for_load_state("networkidle")

        # Fill login form
        logging.info("Filling login form...")
        popup_page.fill("input[id='rw-district-code']", DISTRICT_CODE)
        popup_page.fill("input[id='rw-username']", USERNAME)
        popup_page.fill("input[id='rw-password']", PASSWORD)

        # Submit login form
        logging.info("Submitting login form...")
        popup_page.wait_for_selector("input[id='next']", state="visible", timeout=60000)
        popup_page.locator("input[id='next']").click()

        # Wait for login process
        time.sleep(5)

        return popup_page

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return None


def main():
    """Main function to run the scraper"""
    if not all([USERNAME, PASSWORD, DISTRICT_CODE]):
        logging.error(
            "Missing required environment variables. Please check your .env file."
        )
        return

    with sync_playwright() as p:
        try:
            # Launch browser with specific settings
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            # Perform login
            popup_page = perform_login(page)
            if not popup_page:
                logging.error("Login failed")
                return

            # Check for successful login
            current_url = popup_page.url
            logging.info(f"Current URL after login: {current_url}")

            # Determine which page has the dashboard
            dashboard_page = None
            if "familyportal.renweb.com" in current_url:
                logging.info("Dashboard loaded in popup page")
                dashboard_page = popup_page
            else:
                logging.info("Checking parent page for dashboard...")
                popup_page.close()

                page.wait_for_load_state("networkidle", timeout=10000)
                if "familyportal.renweb.com" in page.url:
                    logging.info("Dashboard loaded in parent page")
                    dashboard_page = page
                else:
                    logging.error("Failed to find dashboard")
                    return

            # Scrape grades
            if dashboard_page:
                logging.info("Starting grades extraction...")
                grades_data = scrape_grades(dashboard_page)

                if grades_data:
                    data = {
                        "school_info": {
                            "name": dashboard_page.locator(
                                "#facts-school-name-span"
                            ).inner_text(),
                            "year": dashboard_page.locator(
                                "#facts-school-year-term-span"
                            ).inner_text(),
                        },
                        "courses": grades_data,
                        "debug": {
                            "url": dashboard_page.url,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                    save_data(data, "grades_data")
                    logging.info("Successfully extracted grades data")
                else:
                    logging.error("No grades data found")

                # Save final page state
                final_screenshot = dashboard_page.screenshot(full_page=True)
                save_debug_file(final_screenshot, "final_state", is_binary=True)

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            if "page" in locals():
                error_screenshot = page.screenshot()
                save_debug_file(error_screenshot, "error_screenshot", is_binary=True)

        finally:
            if "browser" in locals():
                browser.close()


if __name__ == "__main__":
    main()
