import os
import time
import random
import pandas as pd
import pyautogui
import threading
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
OUTPUT_FILE = os.path.join(OUTPUT_DIRECTORY, "tweets.csv")
# Ensure the output directory exists
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# Configure Selenium to use your real browser
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # Keep browser open after script ends to let us save the page with all content, or just see what was the end

    # adding argument to disable the AutomationControlled flag to bypass bot detection
    options.add_argument("--disable-blink-features=AutomationControlled") 
    # exclude the collection of enable-automation switches 
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    # turn-off userAutomationExtension 
    options.add_experimental_option("useAutomationExtension", False) 
    
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
    driver.set_window_size(1200, 800)  # Set fixed size to maintain fixed consistent behavior, as UI adopts to screen size
    driver.set_window_position(100, 100)  # Place it where you can see it

    return driver

"""
Solution 3: Simulate User Interaction (Mouse Movements)
Chrome pauses execution when idle. You can force it to stay active by sending fake mouse movements:
Usage: Run this function in a separate thread to keep Chrome from pausing:
"""

"""
1️⃣ keep_browser_active() does not exit cleanly if Chrome closes.

If the browser crashes, the thread will run indefinitely, leading to errors.
Solution: Modify the loop to exit if driver is closed.

4️⃣ Fix thread management for keep_browser_active().

Currently, the thread never stops, even when scraping completes.
Solution: Ensure the thread terminates cleanly when the script finishes.
"""
def keep_browser_active(driver):
    while driver.service.is_connectable():  # Stop if driver quits
        try:
            pyautogui.moveRel(1, 0, duration=0.1)
            pyautogui.moveRel(-1, 0, duration=0.1)
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error in keep_browser_active(): {e}")
            # break # keep app alive, try to see if it will still keep working after this error

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

        
"""
Call this inside your scroll loop:
check_for_errors(driver)
"""

"""
2️⃣ fast_scroll() needs a better stuck detection mechanism.

Currently, it only prints "Scrolling is stuck" but does not recover.
Solution: Force refresh if stuck (this was commented out in your version).
"""
def fast_scroll(driver, scroll_times=10):
    """ Scrolls down while detecting if scrolling is stuck. If stuck, it triggers unstuck scrolling. """
    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(random.uniform(5, 25))  # Vary scroll timing
        new_height = driver.execute_script("return document.body.scrollHeight")

        # 🔹 If scrolling is stuck, trigger smooth unstuck scroll
        if new_height == last_height:
            print("⚠️ Scrolling is stuck. Triggering smooth scroll and retry button...")
            smooth_scroll_unstuck(driver)  # Call our new function
            # Try another fast scroll up after unstucking
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")

            # also try to press the button after the scrolling
            retry_button(driver)

            # Hope in next iteration it will scroll down and repeat and fix it.

            """
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)
            time.sleep(1)
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)
            time.sleep(1)
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            """

            #driver.refresh()
            #time.sleep(random.uniform(5, 10))
            #break  # Stop early to prevent infinite looping
        last_height = new_height

# 🔹 Extract all tweet details with human-like scrolling behavior
def scrape_twitter(query, max_scrolls=10, save_every=10):
    driver = setup_driver()
    twitter_login(driver) # 🔹 Log in to Twitter first

    # Open Twitter search page
    search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
    driver.get(search_url)
    time.sleep(random.uniform(3, 8))  # Wait for page to load

    # Start the function in a separate thread
    # Prevent javascript from sleeping by moving the mouse.
    keep_active_thread = threading.Thread(target=keep_browser_active, args=(driver,))
    keep_active_thread.start()

    tweets_data = []
    seen_tweet_ids = set()  # Avoid duplicates
    total_tweets_saved = 0  # Track total tweets saved

    # TODO1:
    # Periodically push PAGE UP two times, then script will gradually jump back to bottom of screen
    # It will trigger the "Retry/Update page" action, and unblock the script itself.
    # Probably it will start running fine in the headless mode as well, or at least resolve issue itself.
    # NB, when scrolling is blocked, scrolling stops at the same position, meaning no data is lost as scrolling does not go through
    # processing script will process tweets up to this moment, and then when scrolling unblocks it will get new data.
    # we just have to unblock it when it's stuck, then it will auto resolve itself and continue...

    # TODO2:
    # Implement method to stop duplicating tweet id-s,
    # Add topic or keyword search information somewhere. 

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
        fast_scroll(driver, scroll_times=random.randint(2, 5))  

        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        print(f"🔍 Scroll Batch {scroll_round+1}/{max_scrolls}: Found {len(tweets)} tweets on this page.")

        for tweet in tweets:
            try:
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
                    author_profile_link = "https://x.com/" + author_element.get_attribute("href")
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
                tweets_data.append({
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
scrape_twitter(query, max_scrolls=10000000, save_every=5)
print(f"✅ Scraping completed. Results saved to: {OUTPUT_FILE}")