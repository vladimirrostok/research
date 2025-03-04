import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

# List of known Nitter instances
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://xcancel.com"
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://lightbrd.com",
    "https://nitter.lucabased.xyz",
    "https://nitter.space",
]

# Different browser User-Agent headers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36",
]

# Initialize Cloudflare scraper
scraper = cloudscraper.create_scraper()

# Function to check which Nitter instance is working
def get_working_nitter_instance():
    for instance in NITTER_INSTANCES:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            response = scraper.get(instance, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"✅ Using working Nitter instance: {instance}")
                time.sleep(random.uniform(1, 2))  # Ensure response is fully processed
                return instance

        except Exception:
            continue
    print("❌ No working Nitter instances found.")
    return None

# Find a working instance
NITTER_BASE_URL = get_working_nitter_instance()
if not NITTER_BASE_URL:
    exit()

def scrape_nitter(query, num_pages=1):
    all_tweets = []

    for page in range(1, num_pages + 1):
        url = f"{NITTER_BASE_URL}/search?f=tweets&q={query}&page={page}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        time.sleep(random.uniform(1, 2))  # Ensure response is fully processed


        try:
            response = scraper.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            continue

        time.sleep(random.uniform(1, 2))  # Ensure response is fully processed
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract tweets
        tweets = soup.find_all("div", class_="timeline-item")
        
        if not tweets:
            print(f"⚠️ No tweets found on page {page}.")
            continue

        for tweet in tweets:
            tweet_text = tweet.find("div", class_="tweet-content")
            if tweet_text:
                all_tweets.append(tweet_text.get_text(separator=" ", strip=True))

        time.sleep(random.uniform(1, 3))  # Avoid rate limits

    return all_tweets

# 🔍 Run scraper with a search term
query = "cybersecurity"
tweets = scrape_nitter(query, num_pages=1)

# Save tweets to CSV
if tweets:
    df = pd.DataFrame(tweets, columns=["Tweet"])
    df.to_csv("tweets.csv", index=False)
    print(f"✅ Scraped {len(tweets)} tweets related to '{query}' and saved to tweets.csv.")
else:
    print("⚠️ No tweets scraped. Try a different Nitter instance or check the structure.")