from flask import Flask, request, Response, jsonify
import feedparser, urllib.parse, json, re, os, time, concurrent.futures, requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_ticker_prices_translate"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://www.yallakora.com/rss/rss.aspx",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://www.bbc.com/arabic/index.xml",
    "ثقافية 🎭": "https://sana.sy/feed/",
    "فن 🎨": "https://www.snacksyrian.com/feed/"
}

SPORTS_SOURCES = [
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا رياضة 🇸🇾"},
    {"url": "https://www.kooora.com/rss.aspx", "name": "كووورة ⚽"},
    {"url": "https://www.goal.com/ar/rss", "name": "Goal ⚽"},
]
POLITICS_SOURCES = [
    {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC 🌍"},
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا سياسة 🇸🇾"},
    {"url": "https://www.skynewsarabia.com/web/rss", "name": "سكاي نيوز 🌍"},
    {"url": "https://arabic.cnn.com/rss", "name": "CNN 🌍"},
]
ECONOMY_SOURCES = [
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 💰"},
    {"url": "https://sana.sy/feed/", "name": "سانا اقتصاد 🇸🇾"},
]
EXTRA_FEEDS = {
    "الكل": POLITICS_SOURCES[:3] + SPORTS_SOURCES[:2],
    "عاجل 🔴": POLITICS_SOURCES[:4],
    "رياضة ⚽": SPORTS_SOURCES,
    "سي
