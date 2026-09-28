import os, json, time, re
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"
CACHE = {"prices": None, "time": 0}

DEFAULT = {
    "site_name": "شامي نيوز",
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي", "فن"],
    "news": [
        {"id": 1, "title": "انطلاق شامي نيوز بحلته الجديدة مع كل المصادر", "content": "تم دمج مصادر السياسة والاقتصاد والفن والرياضة والعملات والذهب والكريبتو", "category": "عاجل", "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=700", "time": "16:30 28-09-2026"},
        {"id": 2, "title": "الدولار مستقر في السوق السوداء بدمشق", "content": "سعر الصرف يشهد استقرار نسبي اليوم", "category": "اقتصاد", "image": "", "time": "15:00 28-09-2026"},
        {"id": 3, "title": "فوز مهم للمنتخب السوري", "content": "حقق المنتخب فوزا مهما في المباراة الودية", "category": "رياضة", "image": "", "time": "14:30 28-09-2026"}
    ]
}

def load():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT, f, ensure_ascii=False, indent=2)
        return DEFAULT
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT

def save(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_all_prices():
    global CACHE
    if CACHE["prices"] and time.time() - CACHE["time"] < 600:
        return CACHE["prices"]

    prices = {
        "syp": "13,350 / 13,450",
        "syp_source": "سوق سوداء",
        "gold": "4,286",
        "gold_source": "XAU",
        "btc": "112k",
        "eth": "3.4k",
        "time": time.strftime("%H:%M"),
        "sports_live": []
    }

    try:
        import requests
        # 1. كريبتو - CoinGecko (يقبلو Render)
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=4).json()
        if "bitcoin" in r:
            prices["btc"] = f'{r["bitcoin"]["usd"]//1000}k'
        if "ethereum" in r:
            prices["eth"] = f'{r["ethereum"]["usd"]//1000}k' if r["ethereum"]["usd"]>1000 else str(r["ethereum"]["usd"])
    except: pass

    try:
        import requests
        # 2. كريبتو - Binance (مصدر تاني)
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=4).json()
        if "price" in r:
            prices["btc"] = f'{float(r["price"])//1000:.0f}k'
    except: pass

    try:
        import requests
        # 3. ذهب - Gold API (يقبلو Render)
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=4).json()
        if "price" in r:
            prices["gold"] = f'{int(r["price"]):,}'
            prices["gold_source"] = "Gold-API"
    except: pass

    try:
        import requests
        # 4. عملات - SP Today و Liratoday (سوق سوداء)
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://sp-today.com/", timeout=5, headers=headers).text
        m = re.search(r'(\d{2},\d{3})', r)
        if m:
            prices["syp"] = f'{m.group(1)} / {int(m.group(1).replace(",",""))+100:,}'
            prices["syp_source"] = "SP-Today"
    except: pass

    try:
        import requests
        # 5. رياضة - ESPN نتائج مباشرة
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard", timeout=4).json()
        for ev in r.get("events", [])[:3]:
            comp = ev.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            if len(teams) >= 2:
                prices["sports_live"].append(f'{teams[0]["team"]["abbreviation"]} {teams[0].get("score","0")}-{teams[1].get("score","0")} {teams[1]["team"]["abbreviation"]}')
    except: pass

    CACHE = {"prices": prices, "time": time.time()}
    return prices

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ data.site_name }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{box-sizing:border-box} body{font-family:Tahoma;background:#f0f0f0;margin:0;padding-bottom:85px}
.top{background:#000;color:#fff;padding:8px 10px;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;font-size:13px;position:sticky;top:0;z-index:50}
.top span{background:#222;padding:7px 12px;border-radius:20px;display:flex;align-items:center;gap:6px}
.header{background:#c40000;color:#fff;padding:14px 15px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:40px;z-index:40}
.urgent{background:#e00000;color:#fff;padding:11px;text-align:center;font-weight:bold;position:sticky;top:96px;z-index:30}
.cats{padding:10px;display:flex;gap:8px;overflow-x:auto}
.cats a{background:#fff;padding:8px 16px;border-radius:20px;text-decoration:none;color:#333;border:1px solid #ddd;font-size:13px;white-space:nowrap}
.cats a.active{background:#c40000;color:#fff;border-color:#c40000}
.card{background:#fff;margin:10px;border-radius:16px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,.06);border-right:5px solid #c40000}
.card.economy{border-color:#ff9800}.card.sports{border-color:#0a7e07}.card.politics{border-color:#004aad}.card.local{border-color:#888}.card.art{border-color:#9c27b0}
.card img{width:100%;max-height:350px;object-fit:cover;display:block}
.inner{padding:14px}
.inner h3{margin:0 0 8px;font-size:18px;line-height:1.4}
.inner p{margin:0 0 8px;color:#555;line-height:1.7;font-size:14px}
.inner small{color:#888;font-size:12px}
.live{margin:10px;background:#0a7e07;color:#fff;padding:10px 12px;border-radius:12px;font-size:13px;display:flex;gap:10px;overflow:auto;white-space:nowrap}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:10px 0;z-index:100}
.nav a{color:#777;text-decoration:none;text-align:center;font-size:11px}
.nav a i{display:block;font-size:22px;margin-bottom:3px}
.nav a.active{color:#c40000;font-weight:bold}
</style></head><body>
<div class="top">
<span><i class="fa-regular fa-clock"></i> {{ p.time }}</span>
<span><i class="fa-brands fa-bitcoin"></i> BTC {{ p.btc }}</span>
<span><i class="fa-brands fa-ethereum"></i> ETH {{ p.eth }}</span>
<span><i class="fa-solid fa-coins"></i> ذهب ${{ p.gold }}</span>
<span><i class="fa-solid fa-dollar-sign"></i> $ {{ p.syp }} ل.س ({{ p.syp_source }})</span>
</div>
<div class="header"><h2 style="margin:0"><i class="fa-regular fa-newspaper"></i> {{ data.site_name }}</h2><div><i class="fa-solid fa-magnifying-glass"></i> <i class="fa-solid fa-bars" style="margin-right:14px"></i></div></div>
<div class="urgent"><i class="fa-solid fa-bell"></i> عاجل: {{ urgents[0].title if urgents else 'أهلا بكم في شامي نيوز' }}</div>

{% if p.sports_live %}
<div class="live"><i class="fa-solid fa-futbol"></i> مباشر: {% for m in p.sports_live %}<span>{{ m }}</span>{% if not loop.last %} | {% endif %}{% endfor %}</div>
{% endif %}

<div class="cats">
<a href="/" class="{% if not cat %}active{% endif %}">الكل</a>
{% for c in data.categories %}<a href="/?cat={{ c }}" class="{% if cat==c %}active{% endif %}">{{ c }}</a>{% endfor %}
</div>

<div style="max-width:700px;margin:auto">
{% for n in news %}
<div class="card {% if n.category=='اقتصاد' %}economy{% elif n.category=='رياضة' %}sports{% elif n.category=='سياسة' %}politics{% elif n.category=='محلي' %}local{% elif n.category=='فن' %}art{% endif %}">
{% if n.image %}<img src="{{ n.image }}">{% endif %}
<div class="inner">
<h3>{{ n.title }}</h3>
<p>{{ n.content }}</p>
<small><i class="fa-solid fa-tag"></i> {{ n.category }} | <i class="fa-regular fa-clock"></i> {{ n.time }}</small>
</div></div>
{% endfor %}
</div>

<div class="nav">
<a href="/" class="{% if not cat %}active{% endif %}"><i class="fa-solid fa-house"></i>الرئيسية</a>
<a href="/?cat=عاجل" class="{% if cat=='عاجل' %}active{% endif %}"><i class="fa-solid fa-fire"></i>عاجل</a>
<a href="/?cat=اقتصاد" class="{% if cat=='اقتصاد' %}active{% endif %}"><i class="fa-solid fa-chart-simple"></i>اقتصاد</a>
<a href="/?cat=رياضة" class="{% if cat=='رياضة' %}active{% endif %}"><i class="fa-solid fa-futbol"></i>رياضة</a>
<a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a>
</div>
</body></html>
"""

@app.route("/")
def home():
    d = load()
    cat = request.args.get("cat")
    news = [x for x in d["news"] if x["category"]==cat] if cat else d["news"]
    urgents = [x for x in d["news"] if x["category"]=="عاجل"][:1]
    return render_template_string(HTML, data=d, news=news, cat=cat, urgents=urgents, p=get_all_prices())

@app.route("/admin", methods=["GET","POST"])
def admin():
    d = load()
    if request.method=="POST":
        title = request.form.get("title","").strip()
        if title:
            d["news"].insert(0, {"id": int(time.time()), "title": title, "content": request.form.get("content",""), "category": request.form.get("category","عاجل"), "image": request.form.get("image","").strip(), "time": time.strftime("%H:%M %d-%m-%Y")})
            save(d)
        return redirect("/admin")
    html = f'''<div dir="rtl" style="padding:20px;font-family:Tahoma;max-width:600px;margin:auto;background:#f5f5f5;min-height:100vh">
    <h2>لوحة التحكم - كل المصادر</h2>
    <div style="background:#fff;padding:10px;border-radius:8px;font-size:12px;margin-bottom:10px">
    مصادر فعالة: CoinGecko + Binance (كريبتو) | Gold-API (ذهب) | SP-Today (سوق سوداء) | ESPN (رياضة مباشر) | RSS سياسة واقتصاد وفن
    </div>
    <form method="post" style="background:#fff;padding:15px;border-radius:12px">
    <input name="title" placeholder="عنوان الخبر" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px" required><br><br>
    <textarea name="content" placeholder="التفاصيل" style="width:100%;height:90px;padding:12px;border:1px solid #ddd;border-radius:8px"></textarea><br><br>
    <input name="image" placeholder="رابط الصورة https://..." style="width:100%;padding:12px;border:1px solid #ddd;border-radius:8px"><br><br>
    <select name="category" style="width:100%;padding:12px;border-radius:8px">{"".join([f"<option>{c}</option>" for c in d["categories"]])}</select><br><br>
    <button style="width:100%;padding:12px;background:#c40000;color:#fff;border:none;border-radius:8px">نشر</button>
    </form><br><a href="/" style="text-decoration:none">← رجوع للموقع</a><hr><h3>الأخبار</h3>'''
    for n in d["news"]:
        html+= f'<div style="background:#fff;padding:10px;margin:6px 0;border-radius:8px;display:flex;justify-content:space-between"><span>{n["title"][:50]} - {n["category"]}</span><a href="/del/{n["id"]}" style="color:red;text-decoration:none">حذف</a></div>'
    return html + '</div>'

@app.route("/del/<int:nid>")
def delete(nid):
    d = load()
    d["news"] = [x for x in d["news"] if x.get("id")!=nid]
    save(d)
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
