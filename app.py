import os, json, time, requests
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"
PRICE_CACHE = {"data": None, "time": 0}

DEFAULT_DATA = {
    "site_name": "شامي نيوز",
    "syp": 13350,
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي"],
    "news": [
        {"title": "مرحبا بكم في شامي نيوز", "content": "تم استعادة جميع الميزات", "category": "عاجل", "image": "", "time": "2026-09-26 16:42"},
        {"title": "خبر رياضي تجريبي", "content": "هذا خبر رياضة", "category": "رياضة", "image": "", "time": "2026-09-26 16:40"},
        {"title": "خبر اقتصادي تجريبي", "content": "هذا خبر اقتصاد", "category": "اقتصاد", "image": "", "time": "2026-09-26 16:30"}
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data.get("news"): data["news"] = DEFAULT_DATA["news"]
            return data
    except: return DEFAULT_DATA

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_prices():
    global PRICE_CACHE
    if time.time() - PRICE_CACHE["time"] < 600 and PRICE_CACHE["data"]:
        return PRICE_CACHE["data"]
    d = load_data()
    prices = {"usd_syp": d.get("syp",13350), "usd_syp_sell": d.get("syp",13350)+75, "gold":"4286", "btc":"84,123", "time": time.strftime("%H:%M")}
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
        prices["btc"] = str(r["bitcoin"]["usd"])
    except: pass
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        prices["gold"] = str(int(r["price"]))
    except: pass
    PRICE_CACHE = {"data": prices, "time": time.time()}
    return prices

HTML_PAGE = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ data.site_name }} - {{ active_cat if active_cat else 'الرئيسية' }}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.0/css/all.min.css">
<style>
body{font-family:Tahoma;background:#f2f2f2;margin:0;padding-bottom:70px}
.top-bar{background:#111;color:#fff;padding:8px 10px;display:flex;gap:8px;font-size:12px;overflow-x:auto;white-space:nowrap}
.top-bar span{background:#222;padding:6px 10px;border-radius:20px}
.header{background:#c40000;color:#fff;padding:12px 15px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}
.urgent-bar{background:#ff0000;color:#fff;padding:10px;text-align:center;font-weight:bold}
.card{background:#fff;margin:10px;padding:12px;border-radius:12px;box-shadow:0 2px 5px rgba(0,0,0,.08)}
.cat-urgent{border-right:6px solid #d00000;background:#fff5f5}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:8px 0;z-index:100}
.bottom-nav a{color:#666;text-decoration:none;text-align:center;font-size:11px}
.bottom-nav a i{display:block;font-size:18px;margin-bottom:2px}
.bottom-nav a.active{color:#c40000;font-weight:bold}
.empty{padding:50px;text-align:center;color:#888}
.empty i{font-size:40px;margin-bottom:10px;display:block}
</style></head><body>
<div class="top-bar">
<span><i class="fa-solid fa-dollar-sign"></i> دولار: {{ prices.usd_syp }}/{{ prices.usd_syp_sell }}</span>
<span><i class="fa-solid fa-coins"></i> ذهب: ${{ prices.gold }}</span>
<span><i class="fa-brands fa-bitcoin"></i> بيتكوين: ${{ prices.btc }}</span>
</div>
<div class="header"><h1 style="margin:0;font-size:20px"><i class="fa-solid fa-newspaper"></i> {{ data.site_name }}</h1><div><i class="fa-solid fa-magnifying-glass" style="margin-left:12px"></i><i class="fa-solid fa-bars"></i></div></div>
{% if urgents and not active_cat %}<div class="urgent-bar"><i class="fa-solid fa-bell"></i> عاجل: {{ urgents[0].title }}</div>{% endif %}
<div style="max-width:700px;margin:auto">
{% if active_cat %}<h3 style="padding:10px 15px"><i class="fa-solid fa-filter"></i> قسم: {{ active_cat }} ({{ news|length }})</h3>{% endif %}
{% for n in news %}
<div class="card {% if n.category=='عاجل' %}cat-urgent{% endif %}">
{% if n.image %}<img src="{{ n.image }}" style="width:100%;border-radius:8px;max-height:250px;object-fit:cover;margin-bottom:8px">{% endif %}
<h3><i class="fa-solid fa-bolt" style="color:#d00000"></i> {{ n.title }}</h3>
<p style="color:#444">{{ n.content }}</p>
<small style="color:#888"><i class="fa-solid fa-tag"></i> {{ n.category }} | {{ n.time }}</small>
</div>
{% else %}
<div class="empty"><i class="fa-solid fa-inbox"></i>ما في أخبار بقسم {{ active_cat }}<br><br><a href="/" style="color:#c40000">رجوع للرئيسية</a></div>
{% endfor %}
</div>
<div class="bottom-nav">
<a href="/" class="{% if not active_cat %}active{% endif %}"><i class="fa-solid fa-house"></i>الرئيسية</a>
<a href="/?cat=عاجل" class="{% if active_cat=='عاجل' %}active{% endif %}"><i class="fa-solid fa-fire"></i>عاجل</a>
<a href="/?cat=اقتصاد" class="{% if active_cat=='اقتصاد' %}active{% endif %}"><i class="fa-solid fa-chart-line"></i>اقتصاد</a>
<a href="/?cat=رياضة" class="{% if active_cat=='رياضة' %}active{% endif %}"><i class="fa-solid fa-futbol"></i>رياضة</a>
<a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a>
</div>
</body></html>
"""

@app.route("/")
def home():
    d = load_data()
    cat = request.args.get("cat")
    if cat:
        filtered = [x for x in d["news"] if x["category"] == cat]
    else:
        filtered = d["news"]
    urgents = [x for x in d["news"] if x["category"] == "عاجل"][:1]
    return render_template_string(HTML_PAGE, data=d, news=filtered, prices=get_prices(), urgents=urgents, active_cat=cat)

@app.route("/admin", methods=["GET","POST"])
def admin():
    d = load_data()
    if request.method == "POST":
        title = request.form.get("title","").strip()
        if title:
            d["news"].insert(0, {"title": title, "content": request.form.get("content",""), "category": request.form.get("category","عاجل"), "image": request.form.get("image",""), "time": time.strftime("%Y-%m-%d %H:%M")})
            save_data(d)
        return redirect("/")
    return '<div dir="rtl" style="padding:20px;font-family:Tahoma"><h2>تحكم شامي</h2><form method="post"><input name="title" placeholder="العنوان" style="width:100%;padding:10px"><br><br><textarea name="content" placeholder="المحتوى" style="width:100%;height:80px"></textarea><br><br><input name="image" placeholder="رابط الصورة" style="width:100%;padding:10px"><br><br><select name="category"><option>عاجل</option><option>سياسة</option><option>اقتصاد</option><option>رياضة</option><option>محلي</option></select><br><br><button>نشر</button></form></div>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
