import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Twitter login credentials - replace with your own
TWITTER_ID = ""  # Enter your twitter username
TWITTER_PASSWORD = ""    # Enter your password

def setup_driver():
    """Set up and return a configured Chrome webdriver"""
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    
    # Set up the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_to_twitter(driver):
    """Login to Twitter account using mobile number"""
    try:
        # Open Twitter login page
        driver.get("https://twitter.com/i/flow/login")
        
        # Wait for the login page to load
        wait = WebDriverWait(driver, 15)
        
        # Enter phone number
        print("Attempting to login to Twitter...")
        login_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        login_field.send_keys(TWITTER_ID)
        login_field.send_keys(Keys.RETURN)
        
        # Wait for the password field
        time.sleep(2)
        
        # Try different selectors for password field as Twitter might change them
        password_selectors = [
            "//input[@name='password']",
            "//input[@autocomplete='current-password']",
            "//div[@data-testid='Password']//input"
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                break
            except:
                continue
        
        if not password_field:
            print("Couldn't find password field")
            return False
            
        password_field.send_keys(TWITTER_PASSWORD)
        password_field.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        time.sleep(5)
        
        # Check if login was successful by looking for home timeline
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='primaryColumn']")))
            print("Successfully logged in to Twitter")
            return True
        except:
            print("Login unsuccessful. Check your credentials or Twitter might be requiring additional verification.")
            return False
            
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return False

def format_count(count_text):
    """Convert Twitter number format to integer string"""
    if not count_text:
        return "N/A"
    
    # Remove commas and any non-numeric characters except digits, dots, K, M
    count_text = re.sub(r'[^\d\.KkMm]', '', count_text)
    
    if not count_text:
        return "N/A"
    
    # Convert K, M to actual numbers
    if 'K' in count_text.upper():
        count_text = str(int(float(count_text.upper().replace('K', '')) * 1000))
    elif 'M' in count_text.upper():
        count_text = str(int(float(count_text.upper().replace('M', '')) * 1000000))
    
    return count_text

def extract_count_from_text(element_text):
    """Extract just the number from text like '123 Following' or 'Following 123'"""
    # Find all numbers in the text (including those with K or M suffix)
    numbers = re.findall(r'\b\d+[,\.]?\d*[KkMm]?\b', element_text)
    if numbers:
        return numbers[0]  # Return the first number found
    return ""

def normalize_twitter_url(url):
    """Normalize Twitter URLs to a standard format and handle @ symbols"""
    # Handle URLs that include the @ symbol
    if '@' in url:
        # Remove the @ symbol from the username part
        parts = url.split('.com/')
        if len(parts) > 1:
            username_part = parts[1]
            if username_part.startswith('@'):
                username_part = username_part[1:]
            url = parts[0] + '.com/' + username_part
    
    # Ensure URL has the correct protocol
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url
    
    return url

def is_valid_twitter_url(url):
    """Check if the URL is a valid Twitter profile URL"""
    # First normalize the URL
    url = normalize_twitter_url(url)
    
    # Basic pattern for Twitter URLs
    twitter_pattern = re.compile(r'https?://(www\.)?(twitter|x)\.com/[a-zA-Z0-9_]+')
    return bool(twitter_pattern.match(url))

def check_profile_exists(driver, url):
    """Check if the Twitter profile exists by looking for specific error indicators"""
    try:
        # Look for elements that indicate a profile doesn't exist
        error_elements = driver.find_elements(By.XPATH, "//div[contains(text(), 'This account doesn')]")
        
        # Check for other error messages
        for error_text in ["doesn't exist", "Account suspended", "Page not found"]:
            if error_text in driver.page_source:
                return False
                
        # Additional check for the primary column (should exist for valid profiles)
        primary_column = driver.find_elements(By.XPATH, "//div[@data-testid='primaryColumn']")
        if not primary_column:
            return False
            
        return True
    except Exception as e:
        print(f"Error checking if profile exists: {str(e)}")
        return False

def scrape_twitter_profile(driver, profile_url):
    """Scrape data from a Twitter profile page with improved selectors"""
    # First normalize the URL
    normalized_url = normalize_twitter_url(profile_url)
    
    profile_data = {
        'profile_url': profile_url,  # Keep original URL in the output
        'normalized_url': normalized_url,  # Add normalized URL for reference
        'bio': "N/A",
        'following_count': "N/A",
        'followers_count': "N/A",
        'location': "N/A",
        'website': "N/A",
        'status': "Success"
    }
    
    try:
        # Validate URL format first
        if not is_valid_twitter_url(profile_url):
            profile_data['status'] = "Invalid URL format"
            print(f"Invalid Twitter URL format: {profile_url}")
            return profile_data
        
        # Load the Twitter profile page with the normalized URL
        driver.get(normalized_url)
        
        # Wait for the page to load (wait for primary column)
        wait = WebDriverWait(driver, 15)
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='primaryColumn']")))
        except TimeoutException:
            profile_data['status'] = "Profile not found or page failed to load"
            print(f"Profile not found or failed to load: {normalized_url}")
            return profile_data
        
        # Check if profile exists
        if not check_profile_exists(driver, normalized_url):
            profile_data['status'] = "Profile doesn't exist"
            print(f"Profile doesn't exist: {normalized_url}")
            return profile_data
        
        # Give the page more time to fully render
        time.sleep(5)
        
        # Extract bio
        try:
            # Try multiple possible selectors for bio
            bio_selectors = [
                "//div[@data-testid='userBio']",
                "//div[contains(@class, 'profile-bio')]",
                "//div[contains(@class, 'UserDescription')]",
                "//div[@data-testid='UserDescription']"
            ]
            
            for selector in bio_selectors:
                bio_elements = driver.find_elements(By.XPATH, selector)
                if bio_elements and bio_elements[0].text:
                    profile_data['bio'] = bio_elements[0].text
                    break
        except Exception as e:
            print(f"Bio not found for {normalized_url}: {str(e)}")
        
        # Extract follower and following counts - improved method
        try:
            # Get all elements that might contain following/followers information
            follow_sections = driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Follow')]/span")
            
            # Debug - print what we found
            print("Found follow elements:")
            for elem in follow_sections:
                print(f"  Text: '{elem.text}'")
            
            # Specifically look for elements with numbers
            following_count = ""
            followers_count = ""
            
            # Method 1: Look for specific text patterns
            for elem in follow_sections:
                text = elem.text.strip()
                if re.search(r'\b\d+\b.*follow', text.lower()):
                    count = extract_count_from_text(text)
                    if 'following' in text.lower() and not following_count:
                        following_count = format_count(count)
                    elif 'follower' in text.lower() and not followers_count:
                        followers_count = format_count(count)
            
            # Method 2: Use more specific XPath queries if method 1 fails
            if not following_count or not followers_count:
                print("Using alternative method to find follow counts")
                
                # Try to find follow stats by looking for specific link texts
                stats = driver.execute_script("""
                    var followingElement = Array.from(document.querySelectorAll('a')).find(el => 
                        el.textContent.toLowerCase().includes('following') && 
                        el.href.includes('/following'));
                    var followersElement = Array.from(document.querySelectorAll('a')).find(el => 
                        el.textContent.toLowerCase().includes('follower') && 
                        el.href.includes('/verified_followers'));
                    
                    return {
                        following: followingElement ? followingElement.textContent : '',
                        followers: followersElement ? followersElement.textContent : ''
                    };
                """)
                
                if stats:
                    print(f"JavaScript found: Following='{stats['following']}', Followers='{stats['followers']}'")
                    if stats['following'] and not following_count:
                        following_count = format_count(extract_count_from_text(stats['following']))
                    if stats['followers'] and not followers_count:
                        followers_count = format_count(extract_count_from_text(stats['followers']))
            
            # Update the profile data
            if following_count and following_count != "N/A":
                profile_data['following_count'] = following_count
            if followers_count and followers_count != "N/A":
                profile_data['followers_count'] = followers_count
            
            print(f"Extracted following count: {following_count}, followers count: {followers_count}")
                
        except Exception as e:
            print(f"Error getting follow stats for {normalized_url}: {str(e)}")
        
        # Extract location
        try:
            location_selectors = [
                "//span[contains(@data-testid, 'UserLocation')]",
                "//div[contains(@data-testid, 'UserProfileHeader_Items')]/span[contains(@class, 'r-')]",
                "//div[contains(@data-testid, 'UserProfileHeader_Items')]/span[1]"
            ]
            
            for selector in location_selectors:
                location_elements = driver.find_elements(By.XPATH, selector)
                if location_elements and location_elements[0].text:
                    profile_data['location'] = location_elements[0].text
                    break
        except Exception as e:
            print(f"Error getting location for {normalized_url}: {str(e)}")
        
        # Extract website
        try:
            website_selectors = [
                "//a[contains(@data-testid, 'UserUrl')]",
                "//a[contains(@data-testid, 'UserProfileHeader_Items')]",
                "//div[contains(@data-testid, 'UserProfileHeader_Items')]//a"
            ]
            
            for selector in website_selectors:
                website_elements = driver.find_elements(By.XPATH, selector)
                if website_elements and website_elements[0].get_attribute('href'):
                    profile_data['website'] = website_elements[0].get_attribute('href')
                    break
        except Exception as e:
            print(f"Error getting website for {normalized_url}: {str(e)}")
        
        print(f"Scraped data for {normalized_url}: {profile_data}")
        return profile_data
    
    except Exception as e:
        print(f"Error scraping {normalized_url}: {str(e)}")
        profile_data['status'] = f"Error: {str(e)}"
        return profile_data

def main():
    # Initialize the webdriver
    driver = setup_driver()
    
    try:
        # Login to Twitter
        if not login_to_twitter(driver):
            print("Failed to login. Exiting.")
            return
        
        # Read Twitter profile URLs from the input CSV file
        input_profiles = []
        try:
            with open('twitter_links.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and row[0].strip():  # Check if the row is not empty
                        url = row[0].strip()
                        input_profiles.append(url)
        except Exception as e:
            print(f"Error reading input file: {str(e)}")
            return
        
        if not input_profiles:
            print("No valid Twitter profile URLs found in the input file.")
            return
        
        # Scrape data for each profile
        results = []
        for profile_url in input_profiles:
            print(f"Scraping: {profile_url}")
            profile_data = scrape_twitter_profile(driver, profile_url)
            # Remove the normalized_url field before adding to results
            if 'normalized_url' in profile_data:
                del profile_data['normalized_url']
            results.append(profile_data)
            # Add a delay between requests to avoid rate limiting
            time.sleep(3)
        
        # Write the results to a new CSV file
        with open('twitter_profiles_data.csv', 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['profile_url', 'bio', 'following_count', 'followers_count', 'location', 'website', 'status']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"Scraping completed. Data saved to 'twitter_profiles_data.csv'")
    
    finally:
        # Clean up
        driver.quit()

if __name__ == "__main__":
    main()