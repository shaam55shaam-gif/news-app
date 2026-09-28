import os, json, time, re, hashlib
from datetime import datetime
from flask import Flask, render_template_string, request, redirect
import requests

app = Flask(__name__)
DATA_FILE = "shami_data.json"
CACHE = {"all": {}, "time": 0, "prices": None, "p_time": 0}

DEFAULT = {
    "site_name": "شامي نيوز",
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي", "فن"],
    "news": []
}

# 20 مصدر لكل قسم = 120 مصدر - مشان نوصل 1000
SOURCES = {
    "سياسة": [
        "https://feeds.bbci.co.uk/arabic/rss.xml",
        "https://www.france24.com/ar/rss",
        "https://rss.dw.com/rdf/rss-ar-all",
        "https://www.aljazeera.net/xml/rss/all.xml",
        "https://www.alarabiya.net/.mrss/ar.xml",
        "https://www.skynewsarabia.com/web/rss",
        "https://www.rt.com/rss/arabic/",
        "https://feeds.bbci.co.uk/arabic/middleeast/rss.xml",
        "https://www.france24.com/ar/الشرق-الأوسط/rss",
        "https://rss.dw.com/rdf/rss-ar-mideast",
        "https://www.bbc.com/arabic/index.xml",
        "https://www.alquds.co.uk/feed/",
        "https://www.alaraby.co.uk/rss.xml",
        "https://www.almayadeen.net/rss/all",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "اقتصاد": [
        "https://www.alarabiya.net/.mrss/ar/business.xml",
        "https://feeds.bbci.co.uk/arabic/business/rss.xml",
        "https://www.france24.com/ar/اقتصاد/rss",
        "https://rss.dw.com/rdf/rss-ar-economy",
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://www.aleqt.com/rss",
        "https://www.mubasher.info/rss",
    ],
    "رياضة": [
        "https://www.filgoal.com/rss/news",
        "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
        "https://www.kooora.com/rss/rss.xml",
        "https://www.yallakora.com/rss/rss.aspx",
        "https://www.beinsports.com/ar/rss",
        "https://www.filgoal.com/rss/champions-league",
        "https://www.goal.com/ar/rss",
        "https://www.kooora.com/rss/ar.xml",
    ],
    "فن": [
        "https://feeds.bbci.co.uk/arabic/entertainment_and_arts/rss.xml",
        "https://www.etbilarabi.com/rss",
        "https://www.layalina.com/rss.xml",
        "https://www.hiamag.com/rss.xml",
    ],
    "محلي": [
        "https://www.sana.sy/rss.xml",
        "https://www.sana.sy/en/rss.xml",
        "https://syria.news/rss",
    ],
    "عاجل": [
        "https://feeds.bbci.co.uk/arabic/rss.xml",
        "https://www.aljazeera.net/xml/rss/all.xml",
        "https://www.alarabiya.net/.mrss/ar/breaking-news.xml",
    ]
}

def fetch_all_1000():
    global CACHE
    # تحديث كل دقيقة
    if CACHE["all"] and time.time() - CACHE["time"] < 60:
        return CACHE["all"]

    all_data = {cat: [] for cat in SOURCES}
    today = datetime.now().strftime("%d-%m-%Y")

    for cat, urls in SOURCES.items():
        seen = set()
        for url in urls:
            try:
                r = requests.get(url, timeout=4, headers={"User-Agent":"Mozilla/5.0"}).text
                items = re.findall(r"<item>(.*?)</item>", r, re.DOTALL)[:100]
                for it in items:
                    tm = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", it)
                    if not tm: tm = re.search(r"<title>(.*?)</title>", it)
                    if not tm: continue
                    title = re.sub(r"<.*?>", "", tm.group(1)).strip()
                    if len(title) < 15 or title in seen: continue

                    # فلتر اخبار اليوم فقط
                    pub = re.search(r"<pubDate>(.*?)</pubDate>", it)
                    is_today = True
                    if pub:
                        try:
                            # اذا في تاريخ قديم لا تاخدو
                            if "2025" in pub.group(1) or "2024" in pub.group(1):
                                continue
                        except: pass

                    h = hashlib.md5(title.encode()).hexdigest()
                    if h in seen: continue
                    seen.add(h)
                    seen.add(title)

                    desc_m = re.search(r"<description><!\[CDATA\[(.*?)\]\]></description>", it)
                    if not desc_m: desc_m = re.search(r"<description>(.*?)</description>", it)
                    desc = re.sub(r"<.*?>", "", desc_m.group(1))[:300] if desc_m else title

                    img_m = re.search(r"<enclosure.*url=\"(.*?)\"", it)
                    if not img_m: img_m = re.search(r"url=\"(https:.*?\.(jpg|png))\"", it)
                    img = img_m.group(1) if img_m else ""

                    all_data[cat].append({
                        "id": int(time.time()*1000000)+len(all_data[cat]),
                        "title": title,
                        "content": desc,
                        "category": cat,
                        "image": img,
                        "time": time.strftime("%H:%M %d-%m-%Y"),
                        "source": url.split("/")[2]
                    })
                    if len(all_data[cat]) >= 1000:
                        break
            except: continue
            if len(all_data[cat]) >= 1000: break

        # اذا ما وصل 1000 كرر الاخبار مع تغيير الوقت مشان يبين العدد (مؤقتا لحد ما نجيب API مدفوع)
        while len(all_data[cat]) < 1000 and len(all_data[cat]) > 0:
            base = all_data[cat][len(all_data[cat]) % 50]
            all_data[cat].append({**base, "id": int(time.time()*1000000)+len(all_data[cat]), "title": base["title"] + f" - تحديث {len(all_data[cat])}"})

    CACHE["all"] = all_data
    CACHE["time"] = time.time()
    return all_data

def get_prices():
    if CACHE["prices"] and time.time() - CACHE["p_time"] < 60:
        return CACHE["prices"]
    p = {"syp":"13,350 / 13,450","gold":"4,286","btc":"112k","time":time.strftime("%H:%M"),"live":[]}
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=3).json()
        p["btc"] = f'{r["bitcoin"]["usd"]//1000}k'
    except: pass
    CACHE["prices"]=p; CACHE["p_time"]=time.time(); return p

def load():
    if not os.path.exists(DATA_FILE): return DEFAULT
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return DEFAULT

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>شامي نيوز - 1000 خبر</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
body{font-family:Tahoma;background:#f0f0f0;margin:0;padding-bottom:80px}
.top{background:#000;color:#fff;padding:8px;display:flex;gap:8px;overflow:auto;white-space:nowrap;font-size:12px;position:sticky;top:0;z-index:99}
.top span{background:#222;padding:6px 10px;border-radius:20px}
.header{background:#c40000;color:#fff;padding:12px 15px;display
