from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_super_sources_2026"

# === 25+ مصدر مضمون ===
FEEDS_MULTI = {
    "الكل": [
        "https://news.google.com/rss?hl=ar&gl=SA&ceid=SA:ar",
        "https://feeds.bbci.co.uk/arabic/rss.xml",
        "https://www.aljazeera.net/aljazeerarss/a7c186be-1c09-4a2d-b0d8-9e98653d08d8",
        "https://www.alarabiya.net/.mrss/ar.xml",
        "https://arabic.rt.com/rss/",
        "https://arabic.cnn.com/api/v1/rss/rss.xml",
        "https://www.skynewsarabia.com/web/rss"
    ],
    "عاجل 🔴": [
        "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=SA&ceid=SA:ar",
        "https://www.aljazeera.net/aljazeerarss/e6a0b8a9-8a8f-459e-8606-a7c94b0d5513",
        "https://www.alarabiya.net/.mrss/ar.xml",
        "https://news.google.com/rss/search?q=عاجل+الآن+اليوم&hl=ar&gl=EG&ceid=EG:ar"
    ],
    "رياضة ⚽": [
        "https://news.google.com/rss/search?q=رياضة+كرة+قدم&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=الدوري+السعودي+مصر+برشلونة+ريال&hl=ar&gl=SA&ceid=SA:ar",
        "https://www.yallakora.com/rss",
        "https://news.google.com/rss/search?q=منتخب+مصر+السعودية+رياضة&hl=ar&gl=EG&ceid=EG:ar",
        "https://www.kooora.com/?rss=1",
        "https://feeds.bbci.co.uk/arabic/sport/rss.xml"
    ],
    "اقتصاد 💰": [
        "https://news.google.com/rss/search?q=اقتصاد+ذهب+دولار+اسهم&hl=ar&gl=SA&ceid=SA:ar",
        "https://www.alarabiya.net/.mrss/ar/business.xml",
        "https://news.google.com/rss/search?q=سعر+الدولار+الذهب+النفط&hl=ar&gl=EG&ceid=EG:ar",
        "https://arabic.cnn.com/api/v1/rss/business/rss.xml"
    ],
    "سياسة 🏛️": [
        "https://news.google.com/rss/search?q=سياسة+الشرق+الاوسط+فلسطين&hl=ar&gl=SA&ceid=SA:ar",
        "https://feeds.bbci.co.uk/arabic/topics/الشرق-الأوسط/rss.xml",
        "https://www.aljazeera.net/aljazeerarss/6a1d67a8-c0f1-4ff4-b7c5-1c82cf8d6a82",
        "https://arabic.rt.com/rss/politics/"
    ],
    "ثقافية 🎭": [
        "https://news.google.com/rss/search?q=ثقافة+فن+سينما+كتب&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=افلام+مسلسلات+مهرجان+القاهرة&hl=ar&gl=EG&ceid=EG:ar",
        "https://www.youm7.com/rss/SectionRss?SectionID=89", # ثقافة اليوم السابع
        "https://news.google.com/rss/search?q=فن+نجوم+ثقافة+عربية&hl=ar&gl=SA&ceid=SA:ar",
        "https://www.skynewsarabia.com/web/rss/category/entertainment"
    ]
}

FEEDS = {k: v[0] for k,v in FEEDS_MULTI.items()} # للتابات

CUSTOM_FILE = "custom_news.json"
CUSTOM_NEWS = []
if os.path.exists(CUSTOM_FILE):
    try: CUSTOM_NEWS = json.load(open(CUSTOM_FILE, encoding="utf-8"))
    except: pass
def save_custom():
    try: json.dump(CUSTOM_NEWS, open(CUSTOM_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass

def get_image(entry):
    if hasattr(entry, 'media_content'): return entry.media_content[0]['url']
    if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description', ''))
    if m: return m.group(1)
    # صور مناسبة لكل فئة
    return random.choice([
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600",
        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600"
    ])

def get_news(cat):
    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat or n.get("category")=="الكل"]
    all_news = []
    # لف على كل مصادر الفئة
    for feed_url in FEEDS_MULTI.get(cat, FEEDS_MULTI["الكل"]):
        try:
            feed = feedparser.parse(feed_url)
            for e in feed.entries[:8]:
                # منع التكرار
                if any(a['title'][:20]==e.title[:20] for a in all_news): continue
                all_news.append({
                    "title": e.title,
                    "link": e.link,
                    "time": getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),
                    "source": getattr(e.source,'title','مصدر') if hasattr(e,'source') else feed_url.split('/')[2][:15],
                    "image": get_image(e),
                    "wa": f"https://wa.me/?text={urllib.parse.quote(e.title+' '+e.link)}",
                    "is_custom": False
                })
                if len(all_news) >= 25: break
        except: continue
        if len(all_news) >= 25: break

    random.shuffle(all_news) # خلط المصادر
    return cf + all_news[:20] if all_news else cf + [{"title":f"جاري سحب أخبار {cat} من {len(FEEDS_MULTI.get(cat,[]))} مصادر...","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":"https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600","wa":"#","is_custom":False}]

@app.route('/api/news')
def api_news():
    return jsonify(get_news(request.args.get('cat','الكل')))

@app.route('/manifest.json')
def manifest():
    data = {"name": "أخبار شامي","short_name": "شامي نيوز","start_url": "/","display": "standalone","background_color": "#b71c1c","theme_color": "#b71c1c","lang": "ar","dir": "rtl","icons": [{"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "192x192","type": "image/png"}]}
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/manifest+json')

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('install',e=>self.skipWaiting());", mimetype='application/javascript')

ADMIN_PASSWORD = "shami123"
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.args.get('logout'):
        session.pop('admin', None)
        return redirect('/admin')
    if request.method == 'POST':
        if request.form.get('password'):
