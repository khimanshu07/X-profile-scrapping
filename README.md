# Twitter Profile Scraper

This project is a Python script that automates the process of logging into Twitter and scraping profile data such as bio, following count, followers count, location, and website. The script uses Selenium for browser automation and handles various edge cases to ensure robust data extraction.

## Features

- **Login to Twitter**: Automatically logs into Twitter using provided credentials.
- **Profile Scraping**: Extracts profile information including bio, following count, followers count, location, and website.
- **CSV Input/Output**: Reads Twitter profile URLs from a CSV file and writes the scraped data to another CSV file.
- **Robust Selectors**: Uses multiple selectors to handle changes in Twitter's HTML structure.

## Requirements

To run this script, you need the following:

- Python 3.x
- Selenium
- ChromeDriver (automatically installed by `webdriver_manager`)
- A Twitter account (for login credentials)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/twitter-profile-scraper.git
   cd twitter-profile-scraper

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt

3. Update the twitter_links.csv file with the Twitter profile URLs you want to scrape.
4. Update Your Twitter Credentials
   
    - TWITTER_ID = ""    # Enter your twitter username
    - TWITTER_PASSWORD = ""    # Enter your password
5. Run the script:
    ```bash
    python main.py

6. The scraped data will be saved in twitter_profiles_data.csv.
