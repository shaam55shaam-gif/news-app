import os, json, time, re, requests
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"
PRICE_CACHE = {"data": None, "time": 0}

DEFAULT_DATA = {
    "site_name": "شامي نيوز",
    "syp": 13350,
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي"],
    "news": [
        {"title": "مرحبا بكم في شامي نيوز", "content": "تم استعادة جميع الميزات", "category": "عاجل", "image": "", "time": "2026-09-26 12:00"}
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_DATA

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_prices():
    global PRICE_CACHE
    d = load_data()
    if time.time() - PRICE_CACHE["time"] < 600 and PRICE_CACHE["data"]:
        return PRICE_CACHE["data"]

    prices = {
        "usd_syp": d.get("syp", 13350),
        "usd_syp_sell": d.get("syp", 13350) + 75,
        "gold": "4,286",
        "btc": "84,123",
        "time": time.strftime("%H:%M", time.localtime())
    }

    # 1. دولار سوري سوق سوداء حقيقي من الليرة اليوم
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://liratoday.net/en/latest/usd-syp-sy", headers=headers, timeout=8)
        text = r.text
        # يبحث عن رقم مثل 13,350
        m = re.search(r'Buy Price[^0-9]*([\d,]+)', text)
        if not m:
            m = re.search(r'USD.*?([\d,]{4,6})', text)
        if m:
            val = m.group(1).replace(',', '').replace('.', '')
            # تصحيح لو جاب رقم كبير
            num = int(val)
            if 5000 < num < 30000:
                prices["usd_syp"] = num
                prices["usd_syp_sell"] = num + 75
    except Exception as e:
        print("SYP error:", e)

    # 2. بيتكوين حقيقي لحظي
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
        if "bitcoin" in r:
            prices["btc"] = "{:,}".format(r["bitcoin"]["usd"])
    except: pass

    # 3. ذهب حقيقي عالمي
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        if "price" in r:
            prices["gold"] = "{:,.0f}".format(r["price"])
    except: pass

    PRICE_CACHE = {"data": prices, "time": time.time()}
    return prices

HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ data.site_name }}</title>
<style>
body{font-family:Tahoma,Arial;background:#f2f2f2;margin:0}
.top-bar{background:#111;color:#fff;padding:9px 12px;display:flex;gap:18px;font-size:13px;overflow:auto;white-space:nowrap}
.top-bar span{background:#222;padding:4px 10px;border-radius:20px}
.urgent-bar{background:#d00000;color:#fff;padding:10px;text-align:center;font-weight:bold;letter-spacing:0.5px}
.card{background:#fff;margin:10px;padding:12px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,.08)}
.card img{width:100%;border-radius:8px;max-height:300px;object-fit:cover;margin-bottom:8px}
.cat-urgent{border-right:6px solid #d00000;background:#fff5f5}
.cat-politics{border-right:6px solid #004aad}
.cat-sports{border-right:6px solid #0a7e07}
.cat-economy{border-right:6px solid #ff9800}
</style>
</head>
<body>
<div class="top-bar">
<span>💵 دولار: {{ prices.usd_syp }} / {{ prices.usd_syp_sell }} ل.س سوداء</span>
<span>🥇 ذهب: ${{ prices.gold }}</span>
<span>₿ بيتكوين: ${{ prices.btc }}</span>
<span>🕒 {{ prices.time }}</span>
</div>
{% if urgents %}
<div class="urgent-bar">🔴 عاجل: {{ urgents[0].title }}</div>
{% endif %}
<div style="max-width:700px;margin:auto">
{% for n in data.news %}
<div class="card {% if n.category=='عاجل' %}cat-urgent{% elif n.category=='سياسة' %}cat-politics{% elif n.category=='رياضة' %}cat-sports{% elif n.category=='اقتصاد' %}cat-economy{% endif %}">
{% if n.image %}<img src="{{ n.image }}">{% endif %}
<h3 style="margin:5px 0">{{ n.title }}</h3>
<p style="color:#444;line-height:1.6">{{ n.content }}</p>
<small style="color:#888">{{ n.category }} | {{ n.time }}</small>
</div>
{% endfor %}
</div>
</body>
</html>
"""

@app.route("/")
def home():
    d = load_data()
    urgents = [x for x in d["news"] if x["category"] == "عاجل"][:3]
    return render_template_string(HTML_PAGE, data=d, prices=get_prices(), urgents=urgents)

@app.route("/admin", methods=["GET","POST"])
def admin():
    d = load_data()
    if request.method == "POST":
        title = request.form.get("title","").strip()
        if title:
            d["news"].insert(0, {
                "title": title,
                "content": request.form.get("content",""),
                "category": request.form.get("category","عاجل"),
                "image": request.form.get("image",""),
                "time": time.strftime("%Y-%m-%d %H:%M")
            })
            save_data(d)
        return redirect("/admin")
    return '''
    <div dir="rtl" style="padding:20px;font-family:Tahoma;max-width:600px;margin:auto">
    <h2>لوحة تحكم شامي نيوز</h2>
    <form method="post">
    <input name="title" placeholder="العنوان" style="width:100%;padding:10px"><br><br>
    <textarea name="content" placeholder="المحتوى" style="width:100%;height:90px;padding:10px"></textarea><br><br>
    <input name="image" placeholder="رابط الصورة" style="width:100%;padding:10px"><br><br>
    <select name="category" style="padding:8px"><option>عاجل</option><option>سياسة</option><option>اقتصاد</option><option>رياضة</option><option>محلي</option></select><br><br>
    <button style="padding:10px 20px;background:#000;color:#fff;border:none;border-radius:6px">نشر الخبر</button>
    </form><br><a href="/">⬅ العودة للموقع</a></div>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
