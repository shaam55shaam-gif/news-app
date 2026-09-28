import os, json, time
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"
CACHE = {"data": None, "time": 0}

DEFAULT = {
    "site_name": "شامي نيوز",
    "syp": 13350,
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي"],
    "news": [
        {"id": 1, "title": "انطلاق شامي نيوز بحلته الجديدة", "content": "تم تحديث الموقع مع كل الميزات والمصادر الحقيقية", "category": "عاجل", "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600", "time": "2026-09-28 16:00"},
        {"id": 2, "title": "الدولار مستقر في السوق السوداء", "content": "استقرار نسبي لسعر الصرف في دمشق", "category": "اقتصاد", "image": "", "time": "2026-09-28 15:00"},
        {"id": 3, "title": "فوز المنتخب السوري", "content": "حقق المنتخب فوزاً مهماً", "category": "رياضة", "image": "", "time": "2026-09-28 14:00"}
    ]
}

def load():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT, f, ensure_ascii=False, indent=2)
        return DEFAULT
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            if not d.get("news"): d["news"] = DEFAULT["news"]
            return d
    except:
        return DEFAULT

def save(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_prices():
    global CACHE
    # كاش 15 دقيقة مشان ما يعلق Render
    if CACHE["data"] and time.time() - CACHE["time"] < 900:
        return CACHE["data"]

    prices = {"syp": "13,350/13,450", "syp_sell": "13,450", "gold": "4,286", "btc": "112", "time": time.strftime("%H:%M")}

    # المصادر الحقيقية - مع حماية كاملة
    try:
        import requests
        # 1. بيتكوين - CoinGecko
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=4).json()
        if "bitcoin" in r:
            prices["btc"] = str(r["bitcoin"]["usd"] // 1000) # بالآلاف
    except: pass

    try:
        import requests
        # 2. ذهب - Gold API
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=4).json()
        if "price" in r:
            prices["gold"] = f"{int(r['price']):,}"
    except: pass

    try:
        import requests, re
        # 3. دولار سوري سوق سوداء - Liratoday
        r = requests.get("https://liratoday.net/", timeout=5, headers={"User-Agent":"Mozilla/5.0"}).text
        m = re.search(r'(\d{2},\d{3})', r)
        if m:
            val = m.group(1)
            prices["syp"] = f"{val}/{int(val.replace(',',''))+100}"
    except: pass

    CACHE = {"data": prices, "time": time.time()}
    return prices

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ data.site_name }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{box-sizing:border-box} body{font-family:Tahoma,Arial;background:#f0f0f0;margin:0;padding-bottom:75px}
.top-bar{background:#000;color:#fff;padding:8px 10px;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;font-size:13px;position:sticky;top:0;z-index:30}
.top-bar span{background:#222;padding:7px 12px;border-radius:20px;display:flex;align-items:center;gap:6px}
.header{background:#c40000;color:#fff;padding:14px 15px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:40px;z-index:20}
.urgent-bar{background:#ff0000;color:#fff;padding:11px;text-align:center;font-weight:bold}
.container{max-width:700px;margin:auto}
.cat-bar{padding:10px;display:flex;gap:8px;overflow-x:auto}
.cat-bar a{background:#fff;padding:6px 14px;border-radius:20px;text-decoration:none;color:#333;border:1px solid #ddd;font-size:13px;white-space:nowrap}
.cat-bar a.active{background:#c40000;color:#fff;border-color:#c40000}
.card{background:#fff;margin:10px;border-radius:12px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,.08);border-right:6px solid #ccc}
.card.urgent{border-color:#d00000;background:#fff5f5}.card.economy{border-color:#ff9800}.card.sports{border-color:#0a7e07}.card.politics{border-color:#004aad}
.card img{width:100%;max-height:320px;object-fit:cover}
.body{padding:12px}
.body h3{margin:0 0 8px;font-size:17px;line-height:1.4}
.body p{color:#444;line-height:1.7;margin:0 0 8px;font-size:14px}
.body small{color:#888}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:9px 0;z-index:100}
.bottom-nav a{color:#777;text-decoration:none;text-align:center;font-size:11px}
.bottom-nav a i{display:block;font-size:21px;margin-bottom:3px}
.bottom-nav a.active{color:#c40000;font-weight:bold}
.empty{text-align:center;padding:60px;color:#999}
</style></head><body>
<div class="top-bar">
<span><i class="fa-solid fa-dollar-sign"></i> $ {{ p.syp }} ل.س</span>
<span><i class="fa-solid fa-coins"></i> ذهب ${{ p.gold }}</span>
<span><i class="fa-brands fa-bitcoin"></i> {{ p.btc }}k$</span>
<span><i class="fa-regular fa-clock"></i> {{ p.time }}</span>
</div>
<div class="header">
<h1 style="margin:0;font-size:21px"><i class="fa-solid fa-newspaper"></i> {{ data.site_name }}</h1>
<div><i class="fa-solid fa-magnifying-glass" style="margin-left:14px"></i><i class="fa-solid fa-bars"></i></div>
</div>
{% if not cat and urgents %}<div class="urgent-bar"><i class="fa-solid fa-bell"></i> عاجل: {{ urgents[0].title }}</div>{% endif %}
<div class="container">
<div class="cat-bar">
<a href="/" class="{% if not cat %}active{% endif %}">الكل</a>
{% for c in data.categories %}<a href="/?cat={{ c }}" class="{% if cat==c %}active{% endif %}">{{ c }}</a>{% endfor %}
</div>
{% for n in news %}
<div class="card {% if n.category=='عاجل' %}urgent{% elif n.category=='اقتصاد' %}economy{% elif n.category=='رياضة' %}sports{% else %}politics{% endif %}">
{% if n.image %}<img src="{{ n.image }}">{% endif %}
<div class="body">
<h3>{{ n.title }}</h3>
<p>{{ n.content }}</p>
<small><i class="fa-solid fa-tag"></i> {{ n.category }} | <i class="fa-regular fa-clock"></i> {{ n.time }}</small>
</div></div>
{% else %}
<div class="empty"><i class="fa-solid fa-inbox"></i><br>لا يوجد أخبار في {{ cat }}<br><br><a href="/" style="color:#c40000">العودة للرئيسية</a></div>
{% endfor %}
</div>
<div class="bottom-nav">
<a href="/" class="{% if not cat %}active{% endif %}"><i class="fa-solid fa-house"></i>الرئيسية</a>
<a href="/?cat=عاجل" class="{% if cat=='عاجل' %}active{% endif %}"><i class="fa-solid fa-fire"></i>عاجل</a>
<a href="/?cat=اقتصاد" class="{% if cat=='اقتصاد' %}active{% endif %}"><i class="fa-solid fa-chart-line"></i>اقتصاد</a>
<a href="/?cat=رياضة" class="{% if cat=='رياضة' %}active{% endif %}"><i class="fa-solid fa-futbol"></i>رياضة</a>
<a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a>
</div>
</body></html>
"""

ADMIN = """
<div dir="rtl" style="max-width:650px;margin:auto;padding:20px;font-family:Tahoma;background:#f5f5f5;min-height:100vh">
<h2><i class="fa-solid fa-gear"></i> لوحة التحكم</h2>
<form method="post" style="background:#fff;padding:15px;border-radius:12px;box-shadow:0 2px 5px rgba(0,0,0,.05)">
<input name="title" placeholder="عنوان الخبر" required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px"><br><br>
<textarea name="content" placeholder="تفاصيل الخبر" required style="width:100%;height:100px;padding:12px;border:1px solid #ddd;border-radius:8px"></textarea><br><br>
<input name="image" placeholder="رابط الصورة https://... (اختياري)" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px"><br><br>
<select name="category" style="width:100%;padding:12px;border-radius:8px;border:1px solid #ddd">
{% for c in cats %}<option>{{ c }}</option>{% endfor %}
</select><br><br>
<button style="width:100%;padding:12px;background:#c40000;color:#fff;border:none;border-radius:8px;font-size:16px">نشر الخبر</button>
</form><br><a href="/" style="text-decoration:none;color:#333">← العودة للموقع</a><hr>
<h3>الأخبار ({{ news|length }})</h3>
{% for n in news %}<div style="background:#fff;padding:10px;margin:6px 0;border-radius:8px;display:flex;justify-content:space-between"><span>{{ n.title }} - {{ n.category }}</span><a href="/del/{{ n.id }}" style="color:red;text-decoration:none">حذف</a></div>{% endfor %}
</div>
"""

@app.route("/")
def home():
    d = load()
    cat = request.args.get("cat")
    news = [x for x in d["news"] if x["category"]==cat] if cat else d["news"]
    urgents = [x for x in d["news"] if x["category"]=="عاجل"][:1]
    return render_template_string(HTML, data=d, news=news, urgents=urgents, cat=cat, p=get_prices())

@app.route("/admin", methods=["GET","POST"])
def admin_page():
    d = load()
    if request.method=="POST":
        title = request.form.get("title","").strip()
        if title:
            d["news"].insert(0, {"id": int(time.time()), "title": title, "content": request.form.get("content",""), "category": request.form.get("category","عاجل"), "image": request.form.get("image","").strip(), "time": time.strftime("%Y-%m-%d %H:%M")})
            save(d)
        return redirect("/admin")
    return render_template_string(ADMIN, cats=d["categories"], news=d["news"])

@app.route("/del/<int:nid>")
def delete_news(nid):
    d = load()
    d["news"] = [x for x in d["news"] if x.get("id")!=nid]
    save(d)
    return redirect(request.referrer or "/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
