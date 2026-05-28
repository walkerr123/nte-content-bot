import feedparser
from datetime import datetime, timedelta
import os
from telebot import TeleBot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN or CHAT_ID not set in Vercel Environment Variables!")

BOT = TeleBot(TOKEN)

last_check_time = datetime.now() - timedelta(hours=3)

def is_important(title):
    keywords = ["patch", "1.1", "lacrimosa", "chaos", "porsche", "sunward", "tier", "update", "new character", "maintenance"]
    return any(kw in title.lower() for kw in keywords)

def fetch_new_posts():
    global last_check_time
    feed = feedparser.parse("https://www.reddit.com/r/NevernessToEverness/new/.rss")
    new_posts = []
    
    for entry in feed.entries:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
            if published > last_check_time and is_important(entry.title):
                new_posts.append(entry)
    
    if new_posts:
        last_check_time = datetime.now()
    return new_posts

def handler(request):
    try:
        posts = fetch_new_posts()
        if not posts:
            return {"statusCode": 200, "body": "No new important NTE updates."}
        
        msg = " **NEW NTE INFO DETECTED** \n\n"
        for post in posts[:3]:
            msg += f"**{post.title}**\n🔗 {post.link}\n\n"
            msg += "**Content Plan:**\n"
            msg += "• Short: Hook + key changes\n"
            msg += "• Main Guide: Intro → Pull Priority → Farming → Teams → Tips\n"
            msg += "• Thumbnail: \"NEW PATCH DROPPED 💀\"\n"
            msg += "═"*35 + "\n\n"
        
        BOT.send_message(CHAT_ID, msg[:3500])
        return {"statusCode": 200, "body": f"Sent {len(posts)} alert(s)!"}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}