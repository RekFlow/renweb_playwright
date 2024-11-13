# RenWeb School Portal Scraper

A Python-based web scraping tool that automates login and navigation through the RenWeb School Portal using Playwright. This script provides automated access to the school portal with comprehensive logging and error handling.

## Features

- Automated login to RenWeb School Portal
- Screenshot capture for debugging purposes
- Comprehensive logging system
- Environment variable configuration
- Handles both popup and parent page scenarios
- Cross-platform compatibility

## Prerequisites

Before running this script, ensure you have the following installed:
- Python 3.7 or higher
- pip (Python package installer)

## Required Packages

```bash
playwright==1.41.0
python-dotenv==1.0.0
```

## Installation

1. Clone this repository or download the script:
```bash
git clone <repository-url>
```

2. Install required packages:
```bash
pip install playwright python-dotenv
```

3. Install Playwright browsers:
```bash
playwright install
```

## Configuration

1. Create a `.env` file in the root directory with the following variables:
```env
NCS_USERNAME=your_username
NCS_PASSWORD=your_password
DISTRICT_CODE=your_district_code
```

## Usage

Run the script using:
```bash
python script_name.py
```

## Script Workflow

1. **Environment Setup**
   - Loads credentials from `.env` file
   - Configures logging system

2. **Browser Automation**
   - Launches Chromium browser in visible mode
   - Navigates to the login page
   - Captures initial page screenshot

3. **Login Process**
   - Handles popup login window
   - Inputs credentials
   - Manages form submission

4. **Verification**
   - Verifies successful login
   - Checks both popup and parent pages
   - Captures confirmation screenshots

## Output Files

The script generates several files during execution:
- `page_loaded.png`: Screenshot of initial page load
- `dashboard_loaded.png`: Screenshot after successful login (popup page)
- `dashboard_loaded_parent.png`: Screenshot after successful login (parent page)
- Log entries with timestamp and status information

## Error Handling

The script includes handling for common scenarios:
- Login page loading failures
- Button visibility issues
- Page redirection problems
- Dashboard loading verification

## Logging

Comprehensive logging is implemented with:
- Timestamp for each action
- Clear status messages
- Error reporting
- URL tracking

## Security Notes

- Credentials are stored in `.env` file (not included in version control)
- Browser runs in visible mode for debugging (can be modified for headless operation)
- Screenshots may contain sensitive information - handle with care

## Troubleshooting

Common issues and solutions:

1. **Login Button Not Found**
   - Check if selector `button.schoolsite-popup-button` is still valid
   - Verify page load completion
   - Check network connectivity

2. **Credentials Not Loading**
   - Verify `.env` file exists and is properly formatted
   - Check environment variable names
   - Ensure proper file permissions

3. **Screenshots Not Saving**
   - Verify write permissions in script directory
   - Check for available disk space
   - Ensure valid file paths

## Contributing

Feel free to submit issues and enhancement requests.

## License

[Specify your license here]

## Disclaimer

This tool is for educational purposes only. Ensure compliance with RenWeb's terms of service and obtain necessary permissions before use.
