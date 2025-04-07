from playwright.sync_api import sync_playwright
import pandas as pd
import json
import os
from datetime import datetime

USERNAME = ""
PASSWORD = ""

# https://x.com/deepseek_ai
# https://x.com/OpenAI


TARGET_USER = "deepseek_ai"
OUTPUT_DIR = "DeepSeek"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(OUTPUT_DIR, f"{TARGET_USER}_tweets.csv")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, f"{TARGET_USER}_tweets.json")


def save_tweets(tweets):
    if not tweets:
        return

    df = pd.DataFrame(tweets)
    df.fillna("", inplace=True)

    if not os.path.isfile(OUTPUT_CSV):
        df.to_csv(OUTPUT_CSV, index=False)
    else:
        df.to_csv(OUTPUT_CSV, index=False, mode='a', header=False)
    print(f"✅ Saved {len(tweets)} tweets to CSV.")

    existing = []
    if os.path.isfile(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read existing JSON: {e}")

    existing_ids = {t["tweet_id"] for t in existing}
    new_unique = [t for t in tweets if t["tweet_id"] not in existing_ids]

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(existing + new_unique, f, ensure_ascii=False, indent=2)
    print(f"🧾 Saved {len(new_unique)} new tweets to JSON.")


def extract_all_tweets(obj, collected=None):
    if collected is None:
        collected = {}

    if not isinstance(obj, dict):
        return collected

    # Dive into tweet structure
    if obj.get("__typename") == "TweetWithVisibilityResults":
        obj = obj.get("tweet", {})

    legacy = obj.get("legacy")
    if legacy:
        tweet_id = legacy.get("id_str")
        if tweet_id and tweet_id not in collected:
            tweet = {
                "scraped_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "tweet_id": tweet_id,
                "created_at": legacy.get("created_at"),
                "text": legacy.get("full_text") or legacy.get("text", ""),
                "reply_count": legacy.get("reply_count"),
                "retweet_count": legacy.get("retweet_count"),
                "like_count": legacy.get("favorite_count"),
                "view_count": legacy.get("view_count"),
                "url": f"https://x.com/{TARGET_USER}/status/{tweet_id}",
                "card_type": "",
                "card_url": "",
                "quoted_text": "",
                "media_urls": []
            }

            # Note Tweets (long articles)
            note = obj.get("note_tweet", {}).get("note_tweet_results", {}).get("result", {})
            if note:
                tweet["text"] = note.get("text", tweet["text"])

            # Card (preview/links)
            card = obj.get("card", {})
            if card:
                tweet["card_type"] = card.get("name", "")
                tweet["card_url"] = card.get("url", "")

            # Media
            media_list = legacy.get("extended_entities", {}).get("media", [])
            media_urls = []
            for media in media_list:
                media_url = media.get("media_url_https")
                if media.get("type") in ["video", "animated_gif"]:
                    variants = media.get("video_info", {}).get("variants", [])
                    best = max((v for v in variants if "bitrate" in v), key=lambda x: x.get("bitrate", 0), default={})
                    media_url = best.get("url", media_url)
                if media_url:
                    media_urls.append(media_url)
            tweet["media_urls"] = media_urls

            # Quoted tweet text (if any)
            quoted_result = obj.get("quoted_status_result", {}).get("result", {})
            quoted_legacy = quoted_result.get("legacy", {})
            if quoted_legacy:
                tweet["quoted_text"] = quoted_legacy.get("full_text", "")

            collected[tweet_id] = tweet

    # Recurse into all nested dictionaries
    for v in obj.values():
        if isinstance(v, dict):
            extract_all_tweets(v, collected)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    extract_all_tweets(item, collected)

    return collected


def parse_tweets(json_data):
    all_tweets = {}

    instructions = json_data.get("data", {}).get("user", {}).get("result", {}) \
        .get("timeline", {}).get("timeline", {}).get("instructions", [])

    for instruction in instructions:
        entries = instruction.get("entries", [])
        for entry in entries:
            entry_type = entry.get("entryId", "")

            # Handle standard tweets (TimelineTimelineItem)
            if "tweet" in entry_type or entry.get("content", {}).get("entryType") == "TimelineTimelineItem":
                item_content = entry.get("content", {}).get("itemContent", {})
                tweet_result = item_content.get("tweet_results", {}).get("result", {})
                extract_all_tweets(tweet_result, collected=all_tweets)

            # Handle modules (TimelineTimelineModule), e.g., grouped tweets
            elif entry.get("content", {}).get("entryType") == "TimelineTimelineModule":
                items = entry.get("content", {}).get("items", [])
                for module_item in items:
                    tweet_result = module_item.get("item", {}).get("itemContent", {}) \
                        .get("tweet_results", {}).get("result", {})
                    extract_all_tweets(tweet_result, collected=all_tweets)

    return list(all_tweets.values())


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Login to Twitter
        page.goto("https://x.com/i/flow/login")
        page.wait_for_selector('input[name="text"]', timeout=10000)
        page.fill('input[name="text"]', USERNAME)
        page.keyboard.press('Enter')
        page.wait_for_selector('input[name="password"]', timeout=10000)
        page.fill('input[name="password"]', PASSWORD)
        page.keyboard.press('Enter')
        page.wait_for_selector("[data-testid='SideNav_AccountSwitcher_Button']", timeout=5000)
        print("✅ Logged in successfully.")

        visited_ids = set()

        def handle_response(response):
            if "UserTweets" in response.url and response.status == 200:
                try:
                    json_data = response.json()
                    tweets = parse_tweets(json_data)
                    new_tweets = [t for t in tweets if t["tweet_id"] not in visited_ids]
                    for tweet in new_tweets:
                        visited_ids.add(tweet["tweet_id"])
                        print(f"🐦 [{tweet['created_at']}] {tweet['text'][:80]}...")
                    save_tweets(new_tweets)
                except Exception as e:
                    print(f"⚠️ Error parsing response: {e}")

        page.on("response", handle_response)

        # Navigate to target user
        page.goto(f"https://x.com/{TARGET_USER}")
        page.wait_for_selector("[data-testid='primaryColumn']", timeout=10000)

        # Scroll to load tweets
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            page.wait_for_timeout(3000)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("🔚 Reached end of tweets.")
                break
            last_height = new_height

        print(f"🎉 Scraping completed! Total tweets collected: {len(visited_ids)}")
        browser.close()


if __name__ == "__main__":
    run()