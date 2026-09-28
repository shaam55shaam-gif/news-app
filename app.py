import os, json, time, requests, re
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"
PRICE_CACHE = {"data": None, "time": 0}

DEFAULT_DATA = {
    "site_name": "شامي نيوز",
    "syp": 13350,
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي"],
    "news": [
        {"id": 1, "title": "انطلاق موقع شامي نيوز بحلته الجديدة", "content": "أطلقنا اليوم النسخة الجديدة من موقع شامي نيوز مع تحديثات لحظية لأسعار الصرف والذهب.", "category": "عاجل", "image": "", "time": "2026-09-28 15:00"},
        {"id": 2, "title": "الدولار يواصل الاستقرار في السوق السوداء", "content": "استقر سعر صرف الدولار في السوق السوداء بدمشق عند مستويات جديدة.", "category": "اقتصاد", "image": "", "time": "2026-09-28 14:30"},
        {"id": 3, "title": "فوز مهم للمنتخب السوري", "content": "حقق المنتخب السوري فوزاً مهماً في المباراة الودية الأخيرة.", "category": "رياضة", "image": "", "time": "2026-09-28 13:00"}
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            if not d.get("news"): d["news"] = DEFAULT_DATA["news"]
            return d
    except:
        return DEFAULT_DATA

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_real_prices():
    global PRICE_CACHE
    d = load_data()
    if time.time() - PRICE_CACHE["time"] < 900 and PRICE_CACHE["data"]:
        return PRICE_CACHE["data"]

    prices = {
        "usd_syp": d.get("syp", 13350),
        "usd_syp_sell": d.get("syp", 13350) + 100,
        "gold": "4286",
        "btc": "112450",
        "time": time.strftime("%H:%M", time.localtime())
    }
    # بيتكوين حقيقي
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=6).json()
        prices["btc"] = f"{r['bitcoin']['usd']:,}"
    except: pass
    # ذهب حقيقي
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=6).json()
        prices["gold"] = f"{int(r['price']):,}"
    except: pass
    # دولار سوري سوق سوداء (محاولة)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://liratoday.net/", headers=headers, timeout=8)
        m = re.search(r'(\d{2},\d{3})', r.text)
        if m:
            val = int(m.group(1).replace(",", ""))
            if 8000 < val < 30000:
                prices["usd_syp"] = val
                prices["usd_syp_sell"] = val + 100
    except: pass

    PRICE_CACHE = {"data": prices, "time": time.time()}
    return prices

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ data.site_name }}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.0/css/all.min.css">
<style>
*{box-sizing:border-box} body{font-family:Tahoma,Arial;background:#f2f2f2;margin:0;padding-bottom:75px}
.top-bar{background:#111;color:#fff;padding:8px;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;font-size:13px;position:sticky;top:0;z-index:20}
.top-bar span{background:#222;padding:6px 12px;border-radius:20px;display:flex;align-items:center;gap:5px}
.header{background:#c40000;color:#fff;padding:12px 15px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:42px;z-index:19}
.header h1{margin:0;font-size:22px}
.urgent-bar{background:#ff0000;color:#fff;padding:10px;text-align:center;font-weight:bold;animation:blink 1.2s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:.7}}
.container{max-width:700px;margin:auto}
.card{background:#fff;margin:10px;border-radius:12px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,.07);border-right:6px solid #ccc}
.card.o-urgent{border-color:#d00000;background:#fff5f5}.card.o-politics{border-color:#004aad}.card.o-economy{border-color:#ff9800}.card.o-sports{border-color:#0a7e07}
.card img{width:100%;max-height:300px;object-fit:cover;display:block}
.card-body{padding:12px}
.card h3{margin:5px 0 8px;font-size:17px;line-height:1.4}
.card p{color:#444;line-height:1.6;margin:0 0 8px}
.card small{color:#888}
.cat-filter{padding:10px 15px;display:flex;gap:8px;overflow-x:auto}
.cat-filter a{background:#fff;padding:6px 14px;border-radius:20px;text-decoration:none;color:#333;border:1px solid #ddd;font-size:13px;white-space:nowrap}
.cat-filter a.active{background:#c40000;color:#fff;border-color:#c40000}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:8px 0;z-index:100}
.bottom-nav a{color:#666;text-decoration:none;text-align:center;font-size:11px}
.bottom-nav a i{display:block;font-size:20px;margin-bottom:2px}
.bottom-nav a.active{color:#c40000;font-weight:bold}
.empty{text-align:center;padding:50px;color:#999}
.empty i{font-size:40px;margin-bottom:10px;display:block}
</style></head><body>
<div class="top-bar">
<span><i class="fa-solid fa-dollar-sign"></i> {{ prices.usd_syp }}/{{ prices.usd_syp_sell }} ل.س</span>
<span><i class="fa-solid fa-coins"></i> ذهب ${{ prices.gold }}</span>
<span><i class="fa-brands fa-bitcoin"></i> ${{ prices.btc }}</span>
<span><i class="fa-regular fa-clock"></i> {{ prices.time }}</span>
</div>
<div class="header">
<h1><i class="fa-solid fa-newspaper"></i> {{ data.site_name }}</h1>
<div><i class="fa-solid fa-magnifying-glass" style="margin-left:15px"></i><i class="fa-solid fa-bars"></i></div>
</div>
{% if not active_cat and urgents %}<div class="urgent-bar"><i class="fa-solid fa-triangle-exclamation"></i> عاجل: {{ urgents[0].title }}</div>{% endif %}

<div class="container">
<div class="cat-filter">
<a href="/" class="{% if not active_cat %}active{% endif %}">الكل</a>
{% for c in data.categories %}<a href="/?cat={{ c }}" class="{% if active_cat==c %}active{% endif %}">{{ c }}</a>{% endfor %}
</div>

{% for n in news %}
<div class="card o-{% if n.category=='عاجل' %}urgent{% elif n.category=='اقتصاد' %}economy{% elif n.category=='رياضة' %}sports{% elif n.category=='سياسة' %}politics{% else %}economy{% endif %}">
{% if n.image %}<img src="{{ n.image }}" loading="lazy">{% endif %}
<div class="card-body">
<h3><i class="fa-solid fa-bolt" style="color:#d00000"></i> {{ n.title }}</h3>
<p>{{ n.content }}</p>
<small><i class="fa-solid fa-tag"></i> {{ n.category }} | <i class="fa-regular fa-clock"></i> {{ n.time }} | <a href="/delete/{{ n.id }}" style="color:red;text-decoration:none"><i class="fa-solid fa-trash"></i> حذف</a></small>
</div></div>
{% else %}
<div class="empty"><i class="fa-solid fa-inbox"></i>لا يوجد أخبار في قسم {{ active_cat }}<br><br><a href="/" style="color:#c40000">العودة للرئيسية</a></div>
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

ADMIN_HTML = """
<div dir="rtl" style="max-width:600px;margin:auto;padding:20px;font-family:Tahoma;background:#fff;min-height:100vh">
<h2><i class="fa-solid fa-gear"></i> لوحة تحكم شامي نيوز</h2>
<form method="post" style="background:#f9f9f9;padding:15px;border-radius:10px">
<input name="title" placeholder="عنوان الخبر" required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px"><br><br>
<textarea name="content" placeholder="تفاصيل الخبر" required style="width:100%;height:100px;padding:12px;border:1px solid #ddd;border-radius:8px"></textarea><br><br>
<input name="image" placeholder="رابط الصورة (اختياري) https://..." style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px"><br><br>
<select name="category" style="width:100%;padding:12px;border-radius:8px">
{% for c in cats %}<option>{{ c }}</option>{% endfor %}
</select><br><br>
<button style="width:100%;padding:12px;background:#c40000;color:#fff;border:none;border-radius:8px;font-size:16px;cursor:pointer"><i class="fa-solid fa-paper-plane"></i> نشر الخبر</button>
</form><br>
<a href="/" style="text-decoration:none;color:#333"><i class="fa-solid fa-arrow-right"></i> العودة للموقع</a>
<hr><h3>الأخبار الحالية ({{ news|length }})</h3>
{% for n in news %}<div style="border:1px solid #eee;padding:8px;margin:5px 0;border-radius:6px">{{ n.title }} - {{ n.category }} <a href="/delete/{{ n.id }}" style="color:red;float:left">حذف</a></div>{% endfor %}
</div>
"""

@app.route("/")
def home():
    d = load_data()
    cat = request.args.get("cat")
    news = [x for x in d["news"] if x["category"] == cat] if cat else d["news"]
    urgents = [x for x in d["news"] if x["category"] == "عاجل"][:1]
    return render_template_string(HTML, data=d, news=news, prices=get_real_prices(), urgents=urgents, active_cat=cat)

@app.route("/admin", methods=["GET","POST"])
def admin():
    d = load_data()
    if request.method == "POST":
        title = request.form.get("title","").strip()
        if title:
            new_id = int(time.time())
            d["news"].insert(0, {
                "id": new_id,
                "title": title,
                "content": request.form.get("content",""),
                "category": request.form.get("category","عاجل"),
                "image": request.form.get("image","").strip(),
                "time": time.strftime("%Y-%m-%d %H:%M")
            })
            save_data(d)
        return redirect("/admin")
    return render_template_string(ADMIN_HTML, cats=d["categories"], news=d["news"])

@app.route("/delete/<int:nid>")
def delete_news(nid):
    d = load_data()
    d["news"] = [x for x in d["news"] if x.get("id")!= nid]
    save_data(d)
    return redirect(request.referrer or "/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
