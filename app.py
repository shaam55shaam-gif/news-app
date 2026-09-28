import os, json, time, re, threading
from flask import Flask, render_template_string, request, redirect
import requests

app = Flask(__name__)
DATA_FILE = "shami_data.json"

CACHE = {
    "news": {"عاجل":[],"سياسة":[],"اقتصاد":[],"رياضة":[],"محلي":[],"فن":[]},
    "time": 0,
    "loading": False,
    "prices": {"time": "--:--", "btc": "112k", "gold": "4,286"}
}

DEFAULT_CATS = ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي", "فن"]

def load():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump({"site_name":"شامي نيوز","news":[]},f,ensure_ascii=False)
        return {"news":[]}
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return {"news":[]}

def save(d):
    with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)

def get_rss(url, limit=40):
    try:
        txt = requests.get(url, timeout=3, headers={"User-Agent":"Mozilla/5.0"}).text
        items = re.findall(r"<item>(.*?)</item>", txt, re.DOTALL)[:limit]
        out=[]
        for it in items:
            t = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", it) or re.search(r"<title>(.*?)</title>", it)
            if t:
                title = re.sub(r"<.*?>","", t.group(1)).strip()
                if len(title)>12:
                    out.append(title)
        return out
    except:
        return []

def fetch_all():
    if CACHE["loading"]: return
    CACHE["loading"]=True
    try:
        S = {
            "سياسة": ["https://feeds.bbci.co.uk/arabic/rss.xml","https://www.france24.com/ar/rss","https://rss.dw.com/rdf/rss-ar-all"],
            "اقتصاد": ["https://feeds.bbci.co.uk/arabic/business/rss.xml","https://www.alarabiya.net/.mrss/ar/business.xml"],
            "رياضة": ["https://www.filgoal.com/rss/news","https://feeds.bbci.co.uk/arabic/sport/rss.xml"],
            "فن": ["https://feeds.bbci.co.uk/arabic/entertainment_and_arts/rss.xml"],
            "محلي": ["https://www.sana.sy/rss.xml"],
            "عاجل": ["https://feeds.bbci.co.uk/arabic/rss.xml"]
        }
        new_data = {c: [] for c in DEFAULT_CATS}
        for cat, urls in S.items():
            seen=set()
            for url in urls:
                for title in get_rss(url, 40):
                    if title not in seen:
                        new_data[cat].append({
                            "id": int(time.time()*1000)+len(new_data[cat]),
                            "title": title,
                            "content": title,
                            "category": cat,
                            "image": "",
                            "time": time.strftime("%H:%M %d-%m-%Y")
                        })
                        seen.add(title)
                if len(new_data[cat]) >= 100: # كل قسم 100 خبر
                    break
            new_data[cat] = new_data[cat][:100]

        CACHE["news"] = new_data
        CACHE["time"] = time.time()
    except: pass
    CACHE["loading"]=False

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>شامي نيوز</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{box-sizing:border-box} body{font-family:Tahoma;background:#f0f0f0;margin:0;padding-bottom:80px}
.top{background:#000;color:#fff;padding:8px 10px;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;font-size:12px}
.top span{background:#222;padding:6px 12px;border-radius:20px}
.header{background:#c40000;color:#fff;padding:14px 15px}
.cats{padding:10px;display:flex;gap:8px;overflow-x:auto;background:#f0f0f0;position:sticky;top:0;z-index:10}
.cats a{background:#fff;padding:10px 18px;border-radius:20px;text-decoration:none;color:#333;border:1px solid #ddd;font-weight:bold}
.cats a.active{background:#c40000;color:#fff;border-color:#c40000}
.section-title{background:#fff;margin:15px 10px 5px;padding:12px;border-radius:12px;font-weight:bold;border-right:5px solid #c40000}
.card{background:#fff;margin:10px;border-radius:16px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,.06);border-right:5px solid #c40000}
.card.رياضة{border-color:#0a7e07}.card.سياسة{border-color:#004aad}.card.اقتصاد{border-color:#ff9800}.card.فن{border-color:#9c27b0}
.inner{padding:14px}.inner h3{margin:0 0 6px;font-size:16px;line-height:1.4}.inner small{color:#888;font-size:11px}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:10px 0}
.nav a{color:#777;text-decoration:none;text-align:center;font-size:11px}.nav a i{display:block;font-size:20px}
.nav a.active{color:#c40000}
</style>
</head><body>
<div class="top"><span>{{ p.time }}</span><span>BTC {{ p.btc }}</span><span>ذهب {{ p.gold }}</span>{% if loading %}<span>جاري التحديث...</span>{% endif %}</div>
<div class="header"><h2 style="margin:0">شامي نيوز - {{ cat if cat else 'الكل' }}</h2></div>

<div class="cats">
<a href="/" class="{% if not cat %}active{% endif %}">الكل</a>
{% for c in cats %}<a href="/?cat={{ c }}" class="{% if cat==c %}active{% endif %}">{{ c }} ({{ counts[c] }})</a>{% endfor %}
</div>

<div style="max-width:700px;margin:auto">
{% if cat %}
  {# اذا داخل قسم معين - اعرض بس اخبار هالقسم #}
  {% for n in news %}
    <div class="card {{ n.category }}"><div class="inner"><h3>{{ n.title }}</h3><small>{{ n.category }} | {{ n.time }}</small></div></div>
  {% endfor %}
{% else %}
  {# اذا بالكل - اعرض كل قسم لحال مرتب #}
  {% for c in cats %}
    {% if all_news[c] %}
      <div class="section-title">{{ c }} - {{ all_news[c]|length }} خبر</div>
      {% for n in all_news[c][:20] %}
        <div class="card {{ n.category }}"><div class="inner"><h3>{{ n.title }}</h3><small>{{ n.category }} | {{ n.time }}</small></div></div>
      {% endfor %}
      <div style="text-align:center;margin:10px"><a href="/?cat={{ c }}" style="background:#c40000;color:#fff;padding:8px 20px;border-radius:20px;text-decoration:none">شوف كل اخبار {{ c }} ({{ all_news[c]|length }})</a></div>
    {% endif %}
  {% endfor %}
{% endif %}
</div>

<div class="nav">
<a href="/" class="{% if not cat %}active{% endif %}"><i class="fa-solid fa-house"></i>الرئيسية</a>
<a href="/?cat=عاجل"><i class="fa-solid fa-fire"></i>عاجل</a>
<a href="/?cat=رياضة" class="{% if cat=='رياضة' %}active{% endif %}"><i class="fa-solid fa-futbol"></i>رياضة</a>
<a href="/?cat=اقتصاد" class="{% if cat=='اقتصاد' %}active{% endif %}"><i class="fa-solid fa-chart-simple"></i>اقتصاد</a>
<a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a>
</div>

<script>
// حدث كل دقيقة بالخلفية
setTimeout(()=>{fetch('/api/update').then(r=>r.json()).then(d=>{ if(d.new>0) location.reload(); })}, 5000);
setInterval(()=>{fetch('/api/update')}, 60000);
</script>
</body></html>
"""

@app.route("/")
def home():
    # شغل التحميل بالخلفية بدون ما يعلق
    if not CACHE["news"]["سياسة"] and not CACHE["loading"]:
        threading.Thread(target=fetch_all, daemon=True).start()

    cat = request.args.get("cat")
    if cat:
        news = CACHE["news"].get(cat, [])[:200] # كل قسم 200 خبر
    else:
        news = [] # بالكل رح نعرض من all_news

    counts = {c: len(CACHE["news"].get(c,[])) for c in DEFAULT_CATS}
    return render_template_string(HTML, news=news, all_news=CACHE["news"], cat=cat, cats=DEFAULT_CATS, counts=counts, p=CACHE["prices"], loading=CACHE["loading"])

@app.route("/api/update")
def update():
    if time.time() - CACHE["time"] > 60 and not CACHE["loading"]:
        threading.Thread(target=fetch_all, daemon=True).start()
        return {"status":"updating"}
    return {"status":"ok", "new": sum(len(v) for v in CACHE["news"].values()), "time": CACHE["time"]}

@app.route("/admin", methods=["GET","POST"])
def admin():
    d=load()
    if request.method=="POST":
        title=request.form.get("title","").strip()
        if title:
            d["news"].insert(0,{"id":int(time.time()),"title":title,"content":request.form.get("content",""),"category":request.form.get("category","عاجل"),"image":"","time":time.strftime("%H:%M")})
            save(d)
        return redirect("/admin")
    return f'<div dir="rtl" style="padding:20px;font-family:Tahoma"><h3>تحكم</h3><p>الاخبار المحملة: {sum(len(v) for v in CACHE["news"].values())} - <a href="/api/update">تحديث الان</a></p><form method="post"><input name="title" placeholder="عنوان" required style="width:100%;padding:10px"><br><br><button>نشر</button></form><br><a href="/">رجوع</a></div>'

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
