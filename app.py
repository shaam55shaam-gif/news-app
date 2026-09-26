from flask import Flask, request
import requests, feedparser, os, urllib.parse

app = Flask(__name__)
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def get_img(e):
    try:
        if hasattr(e, 'media_content') and e.media_content:
            u = e.media_content[0]['url']
            if u.startswith('http'): return u
    except: pass
    return "https://images.unsplash.com/photo-1495020689067?w=600&h=400&fit=crop"

def fetch_feed(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=7)
        f = feedparser.parse(r.content)
        out = []
        for x in f.entries[:8]:
            out.append({
                "title": x.title,
                "link": x.link,
                "image": get_img(x),
                "source": "BBC"
            })
        return out
    except:
        return []

@app.route('/')
def home():
    cat = request.args.get('cat', 'الكل')
    news = fetch_feed("https://www.bbc.com/arabic/index.xml")

    cats = ["الكل","عاجل 🔴","رياضة ⚽","سياسة 🏛️","اقتصاد 💰","فن 🎭"]
    tabs_html = ""
    for c in cats:
        active = 'active' if c == cat else ''
        link = "/?cat=" + urllib.parse.quote(c)
        tabs_html += '<a href="' + link + '" class="' + active + '">' + c + '</a>'

    cards_html = ""
    for n in news:
        cards_html += '<div class="card"><img src="' + n["image"] + '" onerror="this.src=\'https://images.unsplash.com/photo-1495020689067?w=600\'"><div class="c"><h3>' + n["title"] + '</h3><small>' + n["source"] + '</small><br><a class="link" href="' + n["link"] + '" target="_blank">اقرأ الخبر</a></div></div>'

    html = """<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>شامي نيوز</title>
<style>
body{font-family:system-ui;background:#f6f7f9;margin:0}
.header{background:#fff;padding:15px;position:sticky;top:0;box-shadow:0 2px 8px #0001}
.tabs{display:flex;gap:8px;overflow:auto;padding:10px}
.tabs a{padding:8px 16px;border-radius:25px;background:#e9e9eb;color:#333;text-decoration:none;font-weight:600}
.tabs a.active{background:#000;color:#fff}
.card{background:#fff;border-radius:16px;overflow:hidden;margin:12px;box-shadow:0 4px 12px #0001}
.card img{width:100%;height:200px;object-fit:cover;background:#ddd}
.card.c{padding:12px}
.card h3{margin:0 0 6px;font-size:17px}
.link{color:#6b21a8;text-decoration:none;font-weight:bold}
</style></head><body>
<div class="header"><h2>شامي نيوز</h2></div>
<div class="tabs">""" + tabs_html + """</div>
<div>""" + cards_html + """</div>
</body></html>"""
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
