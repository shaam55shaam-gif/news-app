import os, json, time, re, urllib.parse, concurrent.futures, requests, feedparser
from flask import Flask, request

app = Flask(__name__)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'}

SRC = {
 "رياضة ⚽": [
  {"u":"https://www.yallakora.com/rss/rss.aspx","n":"يلا كورة"},
  {"u":"https://www.bbc.com/arabic/sport/rss.xml","n":"BBC Sport"},
  {"u":"https://www.france24.com/ar/tag/رياضة/rss","n":"France24 Sport"},
  {"u":"https://www.kooora.com/rss.aspx","n":"كووورة"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي"},
 ],
 "سياسة 🏛️": [
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC عربي"},
  {"u":"https://www.france24.com/ar/rss","n":"France24"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي عربية"},
  {"u":"https://arabic.cnn.com/rss","n":"CNN عربي"},
  {"u":"https://www.aljazeera.net/xml/rss/all.xml","n":"الجزيرة"},
 ],
 "اقتصاد 💰": [
  {"u":"https://www.cnbcarabia.com/rss","n":"CNBC عربية"},
  {"u":"https://www.alarabiya.net/.mrss/ar/business.xml","n":"العربية"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي"},
 ],
 "فن 🎭": [
  {"u":"https://www.france24.com/ar/tag/ثقافة/rss","n":"ثقافة"},
  {"u":"https://www.bbc.com/arabic/art-and-culture/rss.xml","n":"BBC فن"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي فن"},
 ],
 "عاجل 🔴": [
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.aljazeera.net/xml/rss/all.xml","n":"الجزيرة"},
 ],
 "الكل": [
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.france24.com/ar/rss","n":"France24"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي"},
 ]
}

CACHE = {}

def get_img(entry):
    try:
        if 'media_content' in entry and entry.media_content:
            url = entry.media_content[0]['url']
            if url.startswith('http'): return url
        if 'media_thumbnail' in entry and entry.media_thumbnail:
            url = entry.media_thumbnail[0]['url']
            if url.startswith('http'): return url
        if 'enclosures' in entry and entry.enclosures:
            url = entry.enclosures[0].get('href','')
            if url.startswith('http'): return url
    except: pass
    # صورة افتراضية حلوة بدل المربع الأبيض
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&h=400&fit=crop"

def fetch_one(s):
    try:
        r = requests.get(s["u"], headers=HEADERS, timeout=7)
        f = feedparser.parse(r.content)
        out=[]
        for e in f.entries[:5]:
            out.append({
                "title": getattr(e,'title','خبر جديد')[:120],
                "link": getattr(e,'link','#'),
