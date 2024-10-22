# RenWeb Playwright Scraper

A Python-based web scraper for extracting student data from RenWeb/FACTS school management system using Playwright.

## Features

- Automated login to RenWeb portal
- Multi-student support
- Class information extraction
- Screenshot capture for debugging

## Setup

1. Clone the repository:

```bash
git clone https://github.com/RekFlow/renweb_playwright.git
cd renweb_playwright
```

2. Create and activate virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. Install required packages:

```bash
pip install playwright python-dotenv
playwright install
```

4. Create a `.env` file with your credentials:

```
NCS_USERNAME=your_username
NCS_PASSWORD=your_password
DISTRICT_CODE=your_district_code
```

## Usage

Run the scraper:

```bash
python renweb_scraper.py
```

## Project Structure

```
renweb_playwright/
├── renweb_scraper.py  # Main scraper script
├── .env               # Environment variables (not tracked)
└── .gitignore        # Git ignore rules
```

## Development Status

Currently implements basic login and navigation functionality. Future development will include:

- Grade extraction
- Homework information
- Attendance records
