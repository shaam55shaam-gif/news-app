from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime
app = Flask(__name__)
DATA_FILE = "shami_data.json"

def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    try:
        with open(DATA_FILE,"w") as f: json.dump(d,f)
    except: pass

FEEDS = {
    "الكل":"https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴":"https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽":"https://www.yallakora.com/rss/rss.aspx",
    "أسعار 💱":"PRICES",
    "اقتصاد 💰":"https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️":"https://www.bbc.com/arabic/index.xml"
}

SPORTS=[
    {"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},
    {"url":"https://www.beinsports.com/ar/rss","name":"beIN SPORTS 🌍"},
    {"url":"https://www.kooora.com/rss.aspx","name":"كووورة ⚽"},
]

POLITICS=[
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC عربي 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
    {"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"},
]

EXTRA={
    "الكل": POLITICS[:1],  # الكل فقط من جوجل نيوز سوريا
    "عاجل 🔴": POLITICS,
   
