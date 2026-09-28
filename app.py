import os, json, time, re, threading
from flask import Flask, render_template_string, request, redirect
import requests

app = Flask(__name__)
DATA_FILE = "shami_data.json"

# كاش فاضي بالبداية - مشان يقلع بسرعة
CACHE = {"prices": {"syp":"13,350","gold":"4,286","btc":"112k","time":"--:--","live":[]}, "news_all": {}, "price_time": 0, "news_time": 0, "loading": False}

DEFAULT = {
    "site_name": "شامي نيوز",
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي", "فن"],
    "news": [{"id":1,"title":"شامي نيوز - جاري تحميل الأخبار...","content":"الموقع قلع بنجاح، الأخبار رح تظهر خلال ثواني","category":"عاجل","image":"","time":time.strftime("%H:%M")}]
}

def load():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(DEFAULT,f,ensure_ascii=False,indent=2)
        return DEFAULT
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return DEFAULT

def save(d):
    with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)

def fetch_rss_quick(url, limit=20):
    try:
        r = requests.get(url, timeout=3, headers={"User-Agent":"Mozilla/5.0"}).text
        items = re.findall(r"<item>(.*?)</item>", r, re.DOTALL)[:limit]
        res=[]
        for it in items:
            t=re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", it) or re.search(r"<title>(.*?)</title>", it)
            if t:
                title=re.sub(r"<.*?>","",t.group(1)).strip()
                if len(title)>10: res.append(title)
        return res
    except: return []

def background_fetch():
    if CACHE["loading"]: return
    CACHE["loading"]=True
    try:
        SOURCES = {
            "سياسة": ["https://feeds.bbci.co.uk/arabic/rss.xml","https://www.france24.com/ar/rss"],
            "اقتصاد": ["https://feeds.bbci.co.uk/arabic/business/rss.xml"],
            "رياضة": ["https://www.filgoal.com/rss/news","https://feeds.bbci.co.uk/arabic/sport/rss.xml"],
            "فن": ["https://feeds.bbci.co.uk/arabic/entertainment_and_arts/rss.xml"],
            "محلي": ["https://www.sana.sy/rss.xml"],
            "عاجل": ["https://feeds.bbci.co.uk/arabic/rss.xml"]
        }
        all_news={}
        for cat, urls in SOURCES.items():
            all_news[cat]=[]
            for url in urls:
                titles=fetch_rss_quick(url, 30)
                for title in titles:
                    all_news[cat].append({"id":int(time.time()*1000)+len(all_news[cat]),"title":title,"content":title,"category":cat,"image":"","time":time.strftime("%H:%M"),"source":"BBC"})
                if len(all_news[cat])>=30: break
        CACHE["news_all"]=all_news
        CACHE["news_time"]=time.time()
        # اسعار
        try:
            r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",timeout=3).json()
            CACHE["prices"]["btc"]=f'{r["bitcoin"]["usd"]//1000}k'
        except: pass
    except: pass
    CACHE["loading"]=False

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>شامي نيوز</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{box-sizing:border-box} body{font-family:Tahoma;background:#f0f0f0;margin:0;padding-bottom:85px}
.top{background:#000;color:#fff;padding:8px 10px;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;font-size:13px}
.top span{background:#222;padding:7px 12px;border-radius:20px}
.header{background:#c40000;color:#fff;padding:14px 15px}
.urgent{background:#e00000;color:#fff;padding:11px;text-align:center;font-weight:bold}
.cats{padding:10px;display:flex;gap:8px;overflow-x:auto;background:#f0f0f0}
.cats a{background:#fff;padding:9px 18px;border-radius:20px;text-decoration:none;color:#333;border:1px solid #ddd;font-size:14px;white-space:nowrap}
.cats a.active{background:#c40000;color:#fff}
.card{background:#fff;margin:10px;border-radius:16px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,.06);border-right:5px solid #c40000}
.card img{width:100%;max-height:380px;object-fit:cover}
.inner{padding:14px}.inner h3{margin:0 0 8px;font-size:17px}.inner p{margin:0 0 8px;color:#555;font-size:13px}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:10px 0}
.nav a{color:#777;text-decoration:none;text-align:center;font-size:11px}.nav a i{display:block;font-size:22px;margin-bottom:3px}.nav a.active{color:#c40000}
</style>
<meta http-equiv="refresh" content="60">
</head><body>
<div class="top"><span>{{ p.time }}</span><span>BTC {{ p.btc }}</span><span>ذهب ${{ p.gold }}</span></div>
<div class="header"><h2 style="margin:0">شامي نيوز {% if loading %} - جاري التحديث...{% endif %}</h2></div>
<div class="urgent">عاجل: {{ news[0].title if news else 'جاري التحميل' }}</div>
<div class="cats"><a href="/" class="{% if not cat %}active{% endif %}">الكل ({{ total }})</a>{% for c in categories %}<a href="/?cat={{ c }}" class="{% if cat==c %}active{% endif %}">{{ c }} ({{ counts[c] }})</a>{% endfor %}</div>
<div style="max-width:700px;margin:auto">
{% for n in news %}<div class="card"><div class="inner"><h3>{{ n.title }}</h3><p>{{ n.content }}</p><small>{{ n.category }} | {{ n.time }}</small></div></div>{% endfor %}
</div>
<div class="nav"><a href="/" class="active"><i class="fa-solid fa-house"></i>الرئيسية</a><a href="/?cat=عاجل"><i class="fa-solid fa-fire"></i>عاجل</a><a href="/?cat=اقتصاد"><i class="fa-solid fa-chart-simple"></i>اقتصاد</a><a href="/?cat=رياضة"><i class="fa-solid fa-futbol"></i>رياضة</a><a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a></div>
<script>
// جيب الاخبار بعد ما يفتح الموقع
setTimeout(()=>{fetch('/api/refresh').then(()=>location.reload())}, 3000);
</script>
</body></html>
"""

@app.route("/")
def home():
    d=load()
    cat=request.args.get("cat")
    # اذا الكاش فاضي شغل التحميل بالخلفية
    if not CACHE["news_all"] and not CACHE["loading"]:
        threading.Thread(target=background_fetch, daemon=True).start()

    all_news=CACHE["news_all"]
    counts={c: len(all_news.get(c,[])) for c in DEFAULT["categories"]}
    total=sum(counts.values())

    if cat and cat in all_news:
        news=all_news[cat][:100]
    elif not cat:
        combined=[]
        for c in DEFAULT["categories"]:
            combined.extend(all_news.get(c,[])[:20])
        news=combined[:80] if combined else d["news"]
    else:
        news=[x for x in d["news"] if x["category"]==cat] or d["news"]

    return render_template_string(HTML, news=news, cat=cat, categories=DEFAULT["categories"], p=CACHE["prices"], total=total, counts=counts, loading=CACHE["loading"])

@app.route("/api/refresh")
def refresh():
    if time.time() - CACHE["news_time"] > 60 and not CACHE["loading"]:
        threading.Thread(target=background_fetch, daemon=True).start()
        return {"status":"refreshing"}
    return {"status":"cached", "count": sum(len(v) for v in CACHE["news_all"].values())}

@app.route("/admin", methods=["GET","POST"])
def admin():
    d=load()
    if request.method=="POST":
        title=request.form.get("title","").strip()
        if title:
            d["news"].insert(0,{"id":int(time.time()),"title":title,"content":request.form.get("content",""),"category":request.form.get("category","عاجل"),"image":request.form.get("image","").strip(),"time":time.strftime("%H:%M")})
            save(d)
        return redirect("/admin")
    return f'<div dir="rtl" style="padding:20px"><h2>تحكم</h2><form method="post"><input name="title" required style="width:100%;padding:10px"><br><br><textarea name="content" style="width:100%"></textarea><br><br><button>نشر</button></form><br><a href="/">رجوع</a><br><br>الكاش: {sum(len(v) for v in CACHE["news_all"].values())} خبر - <a href="/api/refresh">تحديث الان</a></div>'

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
