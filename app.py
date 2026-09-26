from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, requests, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_search_real"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة+سورية&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا+دولار&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "فن 🎨": "https://news.google.com/rss/search?q=فن+مشاهير+سوريا&hl=ar&gl=SA&ceid=SA:ar"
}

# مصادر فيها صور حقيقية
REAL_SOURCES = {
    "الكل": [
        {"url": "https://sana.sy/feed/", "name": "سانا 🇸🇾"},
        {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC 🌍"},
        {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 🌍"},
    ],
    "رياضة ⚽": [
        {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
        {"url": "https://sana.sy/feed/", "name": "سانا رياضة 🇸🇾"},
        {"url": "https://www.beinsports.com/ar/rss", "name": "beIN 🌍"},
    ],
    "سياسة 🏛️": [
        {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC 🌍"},
        {"url": "https://sana.sy/feed/", "name": "سانا 🇸🇾"},
        {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة"},
    ],
    "اقتصاد 💰": [
        {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 💰"},
        {"url": "https://sana.sy/feed/", "name": "سانا اقتصاد 🇸🇾"},
    ],
}

CUSTOM_FILE = "custom_news.json"
CUSTOM_NEWS = []
if os.path.exists(CUSTOM_FILE):
    try: CUSTOM_NEWS = json.load(open(CUSTOM_FILE, encoding="utf-8"))
    except: pass

def save_custom():
    try: json.dump(CUSTOM_NEWS, open(CUSTOM_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass

DEFAULT_IMAGES = {
    "الكل": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600",
    "عاجل 🔴": "https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=600",
    "رياضة ⚽": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600",
    "اقتصاد 💰": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600",
    "سياسة 🏛️": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600",
    "ثقافية 🎭": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600",
    "فن 🎨": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=600",
}

def get_image(entry, cat="الكل"):
   
