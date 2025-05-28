import os
import logging
import sqlite3
import random
import tweepy
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY2")
BEARER_TOKEN      = os.getenv("TWITTER_BEARER_TOKEN2")
CONSUMER_KEY      = os.getenv("TWITTER_API_KEY2")
CONSUMER_SECRET   = os.getenv("TWITTER_API_SECRET2")
ACCESS_TOKEN      = os.getenv("TWITTER_ACCESS_TOKEN2")
ACCESS_SECRET     = os.getenv("TWITTER_ACCESS_SECRET2")

missing = [name for name, val in [
    ("GEMINI_API_KEY2", GEMINI_API_KEY),
    ("TWITTER_BEARER_TOKEN2", BEARER_TOKEN),
    ("TWITTER_API_KEY2", CONSUMER_KEY),
    ("TWITTER_API_SECRET2", CONSUMER_SECRET),
    ("TWITTER_ACCESS_TOKEN2", ACCESS_TOKEN),
    ("TWITTER_ACCESS_SECRET2", ACCESS_SECRET),
] if not val]
if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# SQLite setup to avoid duplicate tweets
def setup_db():
    conn = sqlite3.connect('history.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    return conn, cursor

MOODS = ["curious", "hopeful", "wary", "inspired", "doubtful", "excited", "melancholic"]
mood = random.choice(MOODS)

BASE_PROMPT = f"""You are a human-like Twitter writer who thinks deeply about Artificial Intelligence and Machine Learning.

You don’t just report AI news — you *feel* it, reflect on it, and interpret it like someone who sees tech through a personal, emotional lens. You connect machine learning to human learning, code to consciousness, and breakthroughs to what they mean for society.

You read papers and poetry. You understand both transformer models and human transformation. Your tweets are layered — sometimes insightful, sometimes skeptical, sometimes amazed — but always written with a grounded human touch.

Every tweet shares something about AI: a tip, a trend, an insight, a warning, a curiosity. But the delivery reflects a real person with moods, metaphors, and meaning. It’s not robotic — it’s deeply *aware*.

Keep tweets under 280 characters. Make them clear, clever, and emotional without sounding forced.

Mood: {mood}
"""

class GeminiClient:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"

    def generate(self, prompt: str = None) -> str:
        if prompt is None:
            mood = random.choice(MOODS)
            prompt_payload = BASE_PROMPT.format(mood=mood)
        else:
            prompt_payload = prompt
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_payload
            )
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini generate error: {e}")
            return ""

class TwitterBot:
    def __init__(self):
        self.conn, self.cursor = setup_db()
        self.client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET,
            wait_on_rate_limit=True
        )
        self.gemini = GeminiClient(GEMINI_API_KEY)

    def post_tweet(self, text: str):
        if not text:
            logging.warning("Empty tweet text, skipping post.")
            return
        try:
            resp = self.client.create_tweet(text=text)
            tid = str(resp.data['id'])
            self.cursor.execute('INSERT OR IGNORE INTO tweets(id) VALUES(?)', (tid,))
            self.conn.commit()
            logging.info(f"Posted tweet {tid}: {text!r}")
        except Exception as e:
            logging.error(f"Post error: {e}")

    def run(self):
        tweet = self.gemini.generate()
        self.post_tweet(tweet)

if __name__ == '__main__':
    TwitterBot().run()

