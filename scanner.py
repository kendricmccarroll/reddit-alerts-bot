import os
import json
import praw
import smtplib
import requests
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

CONFIG_FILE = "config.json"
SEEN_FILE = "seen_posts.json"



USERS_FILE = "users.json"

def load_user_config(user_id: str):
    if not os.path.exists(USERS_FILE):
        return {"keywords": [], "subreddits": []}
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    return users.get(user_id, {"keywords": [], "subreddits": []})

def save_user_config(user_id: str, config: dict):
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = {}
    users[user_id] = config
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_all_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    return list(users.keys())

def save_seen(post_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(post_ids, f)

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE) as f:
        return set(json.load(f))

def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

def scan_reddit(user_id):
    config = load_user_config(user_id)
    seen = load_seen()
    new_posts = []

    for sub in config["subreddits"]:
        for post in reddit.subreddit(sub).new(limit=20):
            if post.id in seen:
                continue
            title = post.title.lower()
            if any(kw.lower() in title for kw in config["keywords"]):
                link = f"https://reddit.com{post.permalink}"
                new_posts.append(f"{post.title}\n{link}\n")
                seen.add(post.id)

    if new_posts:
        message = "\n\n".join(new_posts)
        send_email("Reddit Keyword Alert", message)
        send_telegram(message)
        save_seen(list(seen))
