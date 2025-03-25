import os
import time
import random
import pandas as pd
import pyautogui
import threading
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# 🔹 Twitter Login Credentials
TWITTER_USERNAME = ""
TWITTER_PASSWORD = ""

# 🔹 Set the output directory to the script's execution folder
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))  # Gets the folder where the script is executed
OUTPUT_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "TwitterScraperResults")
OUTPUT_FILE = os.path.join(OUTPUT_DIRECTORY, "feed.csv")
# Ensure the output directory exists
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# Configure Selenium to use your real browser
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # Keep browser open after script ends to let us save the page with all content, or just see what was the end
    
    options.add_argument("--disable-blink-features=AutomationControlled") # adding argument to disable the AutomationControlled flag to bypass bot detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) # exclude the collection of enable-automation switches 
    options.add_experimental_option("useAutomationExtension", False) # turn-off userAutomationExtension 
    
    # Force Browser to Stay Active (Even When Minimized)
    # Prevents JavaScript execution from slowing down when window is in the background.
    options.add_argument("--disable-background-timer-throttling")  # Prevent slowdowns in background
    # Prevents Chrome from pausing when minimized.
    options.add_argument("--disable-backgrounding-occluded-windows")  # Keep browser active even if minimized
    # Ensures Selenium can still interact with the page when minimized.
    options.add_argument("--disable-renderer-backgrounding")  # Prevent rendering freeze when in background
    # Ensures proper rendering of UI elements.
    options.add_argument("--force-device-scale-factor=1")  # Ensures proper rendering
    options.add_argument("--disable-gpu")  # Prevent GPU from stopping rendering when minimized


    driver = webdriver.Chrome(options=options)

    # changing the property of the navigator value for webdriver to undefined 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

    # Resize and reposition window to ensure visibility
    driver.set_window_size(1200, 1200)  # Set fixed size to maintain fixed consistent behavior, as UI adopts to screen size
    driver.set_window_position(100, 100)  # Place it where you can see it

    return driver

def keep_browser_active(driver):
    while driver.service.is_connectable():  # Stop if driver quits
        try:
            # move mouse to keep javascript active
            pyautogui.moveRel(1, 0, duration=0.1)
            pyautogui.moveRel(-1, 0, duration=0.1)
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error in keep_browser_active(): {e}")
            # break # keep app alive, try to see if it will still keep working after this error

# 🔹 Auto-Login Function with Human-Like Delays & Dynamic Waiting
def twitter_login(driver):
    driver.get("https://x.com/login")
    time.sleep(random.uniform(2, 4))  # Simulating user delay
    wait = WebDriverWait(driver, 3)  # Wait up to 15 seconds for elements

    try:
        # Wait for Username Field
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        for char in TWITTER_USERNAME:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # Simulate typing speed
        username_input.send_keys(Keys.RETURN)
        # Use this sleep to bypass additional verification if it happens
        time.sleep(random.uniform(10, 15))  # Wait for next screen (verification or password)

        # **New Fix: Handle Possible Verification Step**
        try:
            verification_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
            print("🔹 Twitter is asking for additional verification. Entering username again...")
            verification_input.send_keys(TWITTER_USERNAME)
            verification_input.send_keys(Keys.RETURN)
            time.sleep(random.uniform(3, 5))
        except:
            print("✅ No extra verification needed.")
            pass

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
# ✅ Save data progressively (prevent data loss on crash)
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

"""
3️⃣ check_for_errors() is commented out.

This function should run inside the scroll loop to automatically click "Retry" if Twitter blocks actions.
"""
def retry_button(driver):
    try:
        print("🔄 Attempting to press the retry button.")
        retry_button = driver.find_element(By.XPATH, '//div[contains(text(), "Retry")]')
        retry_button.click()
        time.sleep(random.uniform(1, 2))
    except:
        pass  # No error, continue


def parse_metric_value(metric_text):
    """
    Converts metric text (like "8.4K") to integer values.
    """
    metric_text = metric_text.strip().replace(',', '')
    multiplier = 1
    if metric_text.endswith('K'):
        multiplier = 1_000
        metric_text = metric_text[:-1]
    elif metric_text.endswith('M'):
        multiplier = 1_000_000
        metric_text = metric_text[:-1]
    
    try:
        return int(float(metric_text) * multiplier)
    except:
        return 0

def extract_tweet_metrics(tweet):
    """
    Extract numeric values for replies, reposts, likes, and views.
    """
    metrics = {"Replies": 0, "Reposts": 0, "Likes": 0, "Views": 0}
    
    try:
        metrics_container = tweet.find_element(
            By.XPATH, './/div[@role="group" and @aria-label]'
        )
        aria_label = metrics_container.get_attribute("aria-label")

        metrics_patterns = {
            "Replies": r'(\d[\d.,KkMm]*) replies?',
            "Reposts": r'(\d[\d.,KkMm]*) reposts?',
            "Likes": r'(\d[\d.,KkMm]*) likes?',
            "Views": r'(\d[\d.,KkMm]*) views?'
        }

        for key, pattern in metrics_patterns.items():
            match = re.search(pattern, aria_label, re.I)
            if match:
                metrics[key] = parse_metric_value(match.group(1))
    except Exception as e:
        print(f"⚠️ Error extracting tweet metrics: {e}")

    return metrics

def extract_video_urls(tweet):
    video_urls = []
    try:
        videos = tweet.find_elements(By.XPATH, './/video')
        for video in videos:
            src = video.get_attribute("src")
            if src and not src.startswith('blob:'):
                # Directly accessible video URL
                video_urls.append(src)
            else:
                # Twitter-hosted video using blob URLs; extract tweet URL instead
                tweet_link_element = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
                tweet_url = tweet_link_element.get_attribute('href')
                video_urls.append(tweet_url)  # URL of the tweet itself
    except Exception as e:
        print(f"⚠️ Error extracting video URLs: {e}")

    return video_urls

def click_following_tab(driver):
    try:
        wait = WebDriverWait(driver, 5)

        # Wait for the "Following" tab to become visible and clickable
        following_tab = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//a[@href="/home" and .//span[text()="Following"]]'))
        )
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", following_tab)
        time.sleep(random.uniform(1, 2))
        
        following_tab.click()
        print("✅ Successfully clicked on 'Following' tab.")
        
        # Allow some time for the page to load tweets
        time.sleep(random.uniform(3, 4))
        
    except Exception as e:
        print(f"❌ Could not click 'Following' tab: {e}")


def smooth_scroll_unstuck(driver):
    """ Simulates real user scrolling by using actual mouse wheel events. """
    print("🔄 Attempting to unstuck scrolling with real user input...")

    try:
        for _ in range(3):  # Scroll up slowly
            pyautogui.scroll(300)  # Scroll UP (Positive Value)
            time.sleep(random.uniform(1, 1.5))

        time.sleep(random.uniform(1, 3))  # Pause for UI refresh

        for _ in range(3):  # Scroll back down slowly
            pyautogui.scroll(-300)  # Scroll DOWN (Negative Value)
            time.sleep(random.uniform(1, 1.5))

        print("✅ Real mouse scroll completed.")

    except Exception as e:
        print(f"❌ Error in real scrolling: {e}")

        
def scroll(driver, scroll_steps=50, step_size=500, delay=3):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for step in range(scroll_steps):
        driver.execute_script(f"window.scrollBy(0, {step_size});")
        time.sleep(delay + random.uniform(1, 3))  # Allow tweets to load
        new_height = driver.execute_script("return document.body.scrollHeight")

        # If reached bottom, break
        if new_height == last_height:
            print("🔚 Reached the end of the page or no new tweets loaded.")
            break
        last_height = new_height

# 🔹 Extract all tweet details with human-like scrolling behavior
def scrape_twitter(query, max_scrolls=10, save_every=5):
    driver = setup_driver()
    twitter_login(driver) # 🔹 Log in to Twitter first

    # Open Twitter search page
    search_url = f"https://x.com/home"
    driver.get(search_url)
    time.sleep(random.uniform(3, 8))  # Wait for page to load

    # 🔥 NEW STEP: Click on Following tab after login
    click_following_tab(driver)

    # Start the function in a separate thread
    # Prevent javascript from sleeping by moving the mouse.
    keep_active_thread = threading.Thread(target=keep_browser_active, args=(driver,))
    keep_active_thread.start()

    tweets_data = []
    seen_tweet_ids = set()  # Avoid duplicates
    total_tweets_saved = 0  # Track total tweets saved

    for scroll_round in range(max_scrolls):
        # check_for_errors(driver)

        # On every 5 scrolls, PAGE UP two times up and down, if the bot was blocked by rate limiter
        # This will auto-trigger the "Something went wrong.. Retry" button  
        """
        if scroll_round % 5 == 0:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)
            time.sleep(1)
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)
            time.sleep(1)
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        """
        
        # Run scrolling multiple random times before processing.
        scroll(driver, scroll_steps=random.randint(10, 20), step_size=600, delay=2)

        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        print(f"🔍 Scroll Batch {scroll_round+1}/{max_scrolls}: Found {len(tweets)} tweets on this page.")

        for tweet in tweets:
            try:
                scrape_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                tweet_timestamp = tweet.find_element(By.XPATH, './/time').get_attribute("datetime")

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
                    author_profile_link = author_element.get_attribute("href")
                    author_username = author_profile_link.split("/")[-1]  # Extract username from URL
                    author_visible_name = tweet.find_element(
                        By.XPATH,
                        './/a[@role="link"]//span[not(.//*)]'
                    ).text
                except Exception as e:
                    print(f"⚠️ Could not extract author details: {e}")
                    author_username = "Unknown"
                    author_profile_link = "N/A"

                # 🔹 Extract Tweet Text
                try:
                    tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                except:
                    tweet_text = "No text available"

                # 🔹 Extract Multimedia (Images, Videos)
                images = tweet.find_elements(By.XPATH, './/img[contains(@src, "twimg.com/media")]')
                image_urls = [img.get_attribute("src") for img in images]

                # Enhanced video extraction:
                video_urls = extract_video_urls(tweet)

                # 🔹 Extract Tweet Reactions (Likes, Retweets, Replies, Quotes, Views)
                # Extract tweet metrics
                metrics = extract_tweet_metrics(tweet)

                # 🔹 Append tweet data
                tweets_data.append({
                    "Scrape Timestamp": scrape_timestamp,  # Add the timestamp
                    "Tweet timestamp": tweet_timestamp,
                    "Tweet ID": tweet_id,
                    "Visible name": author_visible_name,
                    "Author Username": author_username,
                    "Profile Link": author_profile_link,
                    "Text": tweet_text,
                    "Replies": metrics["Replies"],
                    "Retweets": metrics["Reposts"],
                    "Likes": metrics["Likes"],
                    "Views": metrics["Views"],
                    "Images": ", ".join(image_urls) if image_urls else "No images",
                    "Videos": ", ".join(video_urls) if video_urls else "No videos"
                })

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
query = "deepseek"
scrape_twitter(query, max_scrolls=10000000, save_every=1)
print(f"✅ Scraping completed. Results saved to: {OUTPUT_FILE}")