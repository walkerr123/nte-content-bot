import feedparser
from datetime import datetime, timedelta
import os
import json
from telebot import TeleBot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def handler(event, context):
    try:
        if not TOKEN or not CHAT_ID:
            return {"statusCode": 500, "body": "Missing env vars"}

        BOT = TeleBot(TOKEN)
        
        feed = feedparser.parse("https://www.reddit.com/r/NevernessToEverness/new/.rss")
        new_posts = []
        last_check = datetime.now() - timedelta(hours=3)
        
        for entry in feed.entries[:8]:
            if hasattr(entry, 'published_parsed'):
                pub_time = datetime(*entry.published_parsed[:6])
                if pub_time > last_check and any(kw in entry.title.lower() for kw in ["patch", "1.1", "lacrimosa", "porsche", "update"]):
                    new_posts.append(entry)
        
        if not new_posts:
            return {"statusCode": 200, "body": "No new updates"}
        
        msg = "🚨 **NEW NTE UPDATE** 🚨\n\n"
        for post in new_posts[:3]:
            msg += f"**{post.title}**\n🔗 {post.link}\n\n"
            msg += "Content Plan:\n• Short + Main Guide ready\n"
        
        BOT.send_message(CHAT_ID, msg[:3500])
        return {"statusCode": 200, "body": "Alert sent!"}
        
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}