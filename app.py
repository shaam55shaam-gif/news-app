from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, requests, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_politics_full"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة+سورية&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "فن 🎨": "https://news.google.com/rss/search?q=فن+مشاهير+سوريا&hl=ar&gl=SA&ceid=SA:ar"
}

# رياضة - كل المصادر منظمة
SPORTS_SOURCES = [
    {"url": "https://sana.sy/feed/", "name": "سانا - رياضة 🇸🇾"},
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.filgoal.com/rss", "name": "فيلجول 🏆"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN Sports 🌍"},
    {"url": "https://news.google.com/rss/search?q=
