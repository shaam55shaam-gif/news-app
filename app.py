import os, json, time, re, urllib.parse, concurrent.futures, requests, feedparser
from flask import Flask, request, jsonify

app = Flask(__name__)
HEADERS = {'User-Agent': 'Mozilla/5.0'}

SRC = {
 "رياضة ⚽": [
  {"u":"https://www.yallakora.com/rss/rss.aspx","n":"يلا كورة"},
  {"u":"https://www.bbc.com/arabic/sport/rss.xml","n":"BBC"},
  {"u":"https://www.france24.com/ar/tag/رياضة/rss","n":"France24"},
  {"u":"https://www.kooora.com/rss.aspx","n":"كووورة"},
 ],
 "سياسة 🏛️": [
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.france24.com/ar/rss","n":"France24"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي"},
 ],
 "اقتصاد 💰": [
  {"u":"https://www.cnbcarabia.com/rss","n":"CNBC"},
  {"u":"https://www.alarabiya.net/.mrss/ar/business.xml","n":"العربية"},
 ],
 "فن 🎭": [
  {"u":"https://www.france24.com/ar/tag/ثقافة/rss","n":"France24"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي"},
 ],
 "عاجل 🔴": [
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.aljazeera.net/xml/rss/all.xml","n":"الجزيرة"},
 ],
 "الكل": [
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.france24.com/ar/rss","n":"France24"},
 ]
}

def fetch_one(s):
    try:
        r = requests.get(s["u"], headers=HEADERS, timeout=6)
        f = feedparser.parse(r.content)
        out=[]
        for e in f.entries[:4]:
            img = "https://images.unsplash.com/photo-1495020689067?w=600"
            try:
                if 'media_content' in e: img = e.media_content[0]['url']
            except: pass
            out.append({"title":getattr(e,'title','بدون عنوان'),"link":getattr(e,'link','#'),"source":s["n"],"image":img})
        return out
    except Exception as e:
        print(f"feed fail {s['u']}: {e}")
        return []

def get_news(cat):
    try:
        srcs = SRC.get(cat, SRC["الكل"])
        all_n=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futures = [ex.submit(fetch_one, s) for s in srcs]
            for fu in futures:
                try: all_n.extend(fu.result())
                except: pass
        return all_n[:20] if all_n else [{"title":"لا يوجد أخبار حاليا - جاري التحديث","link":"#","source":"شامي","image":"https://images.unsplash.com/photo-1495020689067?w=600"}]
    except Exception as e:
        print(f"get_news error {e}")
        return []

@app.route('/')
def home():
    try:
        cat = request.args.get('cat','الكل')
        news = get_news(cat)
        cats = ["الكل","عاجل 🔴","رياضة ⚽","سياسة 🏛️","اقتصاد 💰","فن 🎭"]
        tabs = "".join([f'<a href="/?cat={urllib.parse.quote(c)}" style="margin:5px;padding:6px 12px;background:{"#000;color:#fff" if c==cat else "#eee"};border-radius:20px;text-decoration:none">{c}</a>' for c in cats])
        cards = "".join([f'<div style="border:1px solid #ddd;margin:10px;border-radius:10px;overflow:hidden"><img src="{n["image"]}" style="width:100%;height:160px;object-fit:cover"><div style="padding:8px"><b>{n["title"]}</b><br><small>{n["source"]}</small><br><a href="{n["link"]}" target="_blank">اقرأ الخبر</a></div></div>' for n in news])
        return f'<html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>شامي</title></head><body style="font-family:sans-serif;padding:10px"><h2>شامي نيوز</h2><div>{tabs}</div><hr>{cards}</body></html>'
    except Exception as e:
        return f"<h1>Error: {e}</h1>", 200

@app.route('/health')
def health(): return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
