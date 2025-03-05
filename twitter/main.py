import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from datetime import datetime

# 🔹 Twitter Login Credentials
TWITTER_USERNAME = ""
TWITTER_PASSWORD = ""

# 🔹 Set the output directory to the script's execution folder
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))  # Gets the folder where the script is executed
OUTPUT_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "TwitterScraperResults")
OUTPUT_FILE = os.path.join(OUTPUT_DIRECTORY, "tweets.csv")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# Configure Selenium to use your real browser
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # Keep browser open
    options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    driver = webdriver.Chrome(options=options)
    return driver

# 🔹 Auto-Login Function with Human-Like Delays & Dynamic Waiting
def twitter_login(driver):
    driver.get("https://x.com/login")
    time.sleep(random.uniform(5, 8))  # Simulating user delay

    wait = WebDriverWait(driver, 15)  # Wait up to 15 seconds for elements

    try:
        # Wait for Username Field
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        for char in TWITTER_USERNAME:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # Simulate typing speed
        username_input.send_keys(Keys.RETURN)

        time.sleep(random.uniform(10, 15))  # Wait for next screen (verification or password)
        # Use this sleep to bypass additional verification if it happens

        # **New Fix: Handle Possible Verification Step**
        try:
            verification_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
            print("🔹 Twitter is asking for additional verification. Entering username again...")
            verification_input.send_keys(TWITTER_USERNAME)
            verification_input.send_keys(Keys.RETURN)
            time.sleep(random.uniform(3, 5))
        except:
            print("✅ No extra verification needed.")

        # **Fix: Wait for the Password Field to Appear**
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        for char in TWITTER_PASSWORD:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # Simulate typing speed
        password_input.send_keys(Keys.RETURN)

        time.sleep(random.uniform(5, 8))  # Simulate waiting for login

        print("✅ Successfully logged into Twitter.")

    except Exception as e:
        print(f"❌ Login Failed: {e}")

# 🔹 Save data to CSV and accumulate tweets instead of overwriting
def save_to_csv(tweets_data):
    if not tweets_data:
        print("⚠️ No tweets to save. Skipping CSV write operation.")
        return

    df = pd.DataFrame(tweets_data)

    try:
        print(f"📂 Saving {len(tweets_data)} tweets to {OUTPUT_FILE}")

        # Append mode with headers only on the first save
        file_exists = os.path.exists(OUTPUT_FILE)
        
        df.to_csv(OUTPUT_FILE, mode='a', header=not file_exists, index=False)

        print(f"✅ Successfully saved {len(tweets_data)} tweets.")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def fast_scroll(driver, scroll_times=10):
    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(random.uniform(5, 25))  # Simulate varied user scrolling speed

# 🔹 Extract all tweet details with human-like scrolling behavior
def scrape_twitter(query, max_scrolls=10, save_every=10):
    driver = setup_driver()
    
    # 🔹 Log in to Twitter first
    twitter_login(driver)

    # Open Twitter search page
    search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
    driver.get(search_url)
    time.sleep(random.uniform(3, 8))  # Wait for page to load

    tweets_data = []
    seen_tweet_ids = set()  # Avoid duplicates
    total_tweets_saved = 0  # Track total tweets saved

    for scroll_round in range(max_scrolls):
        # 🔹 Use fast JavaScript scrolling instead of slow key presses
        # Run scrolling multiple times before processing to optimize resource use.
        fast_scroll(driver, scroll_times=random.randint(2, 5))  

        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        print(f"🔍 Scroll Batch {scroll_round+1}/{max_scrolls}: Found {len(tweets)} tweets on this page.")

        for tweet in tweets:
            try:
                # 🔹 Get Current Timestamp
                scrape_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

                # 🔹 Extract Tweet ID
                try:
                    tweet_id = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]').get_attribute("href").split("/")[-1]
                except:
                    print("⚠️ Skipping tweet with no ID (Tweet ID extraction failed).")
                    continue

                if tweet_id in seen_tweet_ids:
                    print(f"🔄 Duplicate tweet skipped: {tweet_id}")
                    continue  # Skip duplicates
                
                # 🔹 Extract Author's Username & Profile Link
                try:
                    author_element = tweet.find_element(By.XPATH, './/a[@role="link"]')
                    author_profile_link = "https://x.com" + author_element.get_attribute("href")
                    author_username = author_profile_link.split("/")[-1]  # Extract username from URL
                except Exception as e:
                    print(f"⚠️ Could not extract author details: {e}")
                    author_username = "Unknown"
                    author_profile_link = "N/A"

                # 🔹 Updated: Check if author is verified (NEW METHOD)
                #try:
                #    tweet.find_element(By.XPATH, './/div[@data-testid="User-Name"]//svg[@data-testid="icon-verified"]')
                #    is_verified = "Yes"
                #except:
                #    is_verified = "No"

                # 🔹 Extract Tweet Text
                try:
                    tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                except:
                    tweet_text = "No text available"

                # 🔹 Extract Tweet Reactions (Likes, Retweets, Replies, Quotes, Views)
                try:
                    likes = tweet.find_element(By.XPATH, './/div[@data-testid="like"]').text
                except:
                    likes = "0"

                try:
                    retweets = tweet.find_element(By.XPATH, './/div[@data-testid="retweet"]').text
                except:
                    retweets = "0"

                try:
                    replies = tweet.find_element(By.XPATH, './/div[@data-testid="reply"]').text
                except:
                    replies = "0"

                try:
                    views = tweet.find_element(By.XPATH, './/div[@data-testid="view"]').text
                except:
                    views = "0"

                try:
                    quotes = tweet.find_element(By.XPATH, './/div[@data-testid="quote"]').text
                except:
                    quotes = "0"

                # 🔹 Extract Multimedia (Images, Videos)
                images = tweet.find_elements(By.XPATH, './/img[contains(@src, "twimg.com/media")]')
                image_urls = [img.get_attribute("src") for img in images]

                videos = tweet.find_elements(By.XPATH, './/video')
                video_urls = [vid.get_attribute("src") for vid in videos]

                # 🔹 Append tweet data
                tweet_data = {
                    "Scrape Timestamp": scrape_timestamp,  # Add the timestamp
                    "Tweet ID": tweet_id,
                    "Author Username": author_username,
                    "Profile Link": author_profile_link,
                    #"Verified": is_verified,
                    "Text": tweet_text,
                    "Likes": likes,
                    "Retweets": retweets,
                    "Replies": replies,
                    "Quotes": quotes,
                    "Views": views,
                    "Images": ", ".join(image_urls) if image_urls else "No images",
                    "Videos": ", ".join(video_urls) if video_urls else "No videos"
                }

                tweets_data.append(tweet_data)
                seen_tweet_ids.add(tweet_id)

                # Debug: Print every tweet collected
                print(f"✅ Collected Tweet ID: {tweet_id} | Author: {author_username} | Scraped at: {scrape_timestamp}")

                # Save every `save_every` tweets
                if len(tweets_data) >= save_every:
                    save_to_csv(tweets_data)
                    total_tweets_saved += len(tweets_data)
                    tweets_data.clear()  # Reset list AFTER saving

            except Exception as e:
                print(f"❌ Error extracting tweet: {e}")

    # 🔹 Final save for remaining tweets
    if tweets_data:
        save_to_csv(tweets_data)
        total_tweets_saved += len(tweets_data)

    print(f"✅ Total Tweets Saved: {total_tweets_saved}")
    driver.quit()

# Run Scraper
query = "syria"
scrape_twitter(query, max_scrolls=10000000, save_every=5)
print(f"✅ Scraping completed. Results saved to: {OUTPUT_FILE}")