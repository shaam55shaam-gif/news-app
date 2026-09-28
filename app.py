import os, json, time, requests
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"

DEFAULT_DATA = {
    "site_name": "شامي نيوز",
    "news": [
        {"title": "مرحبا بكم في شامي نيوز", "content": "تم استعادة جميع الميزات والايقونات", "category": "عاجل", "image": "", "time": "2026-09-26 16:42"}
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            j = json.load(f)
            if not j.get("news"): return DEFAULT_DATA
            return j
    except:
        return DEFAULT_DATA

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_prices():
    return {"usd_syp": 13350, "usd_syp_sell": 13425, "gold": "4286", "btc": "84,123"}

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>شامي نيوز</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.0/css/all.min.css">
<style>
body{font-family:Tahoma;background:#f5f5f5;margin:0;padding-bottom:70px}
.top-bar{background:#000;color:#fff;padding:10px;display:flex;gap:8px;overflow-x:auto}
.top-bar span{background:#222;padding:8px 12px;border-radius:20px;font-size:13px;white-space:nowrap}
.header{background:#c40000;color:#fff;padding:14px;display:flex;justify-content:space-between;align-items:center}
.urgent-bar{background:#ff0000;color:#fff;padding:12px;text-align:center;font-weight:bold}
.card{background:#fff;margin:12px;padding:14px;border-radius:12px;border-right:5px solid #c40000}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:8px 0}
.bottom-nav a{color:#666;text-decoration:none;text-align:center;font-size:11px}
.bottom-nav a i{display:block;font-size:20px;margin-bottom:3px}
.bottom-nav a.active{color:#c40000}
</style></head><body>
<div class="top-bar">
<span>$ دولار: {{ p.usd_syp }}/{{ p.usd_syp_sell }} ل.س</span>
<span>ذهب: {{ p.gold }}$</span>
<span>بيتكوين: {{ p.btc }}$</span>
</div>
<div class="header">
<div><i class="fa-solid fa-bars" style="margin-left:12px"></i><i class="fa-solid fa-magnifying-glass"></i></div>
<h2 style="margin:0"><i class="fa-solid fa-newspaper"></i> شامي نيوز</h2>
</div>
<div class="urgent-bar"><i class="fa-solid fa-bell"></i> عاجل: {{ data.news[0].title if data.news else 'مرحبا' }}</div>
<div style="max-width:700px;margin:auto">
{% for n in news %}
<div class="card">
<h3><i class="fa-solid fa-bolt" style="color:red"></i> {{ n.title }}</h3>
<p>{{ n.content }}</p>
<small style="color:#888"><i class="fa-solid fa-tag"></i> {{ n.category }} | {{ n.time }}</small>
</div>
{% else %}
<div style="padding:40px;text-align:center;color:#888">ما في أخبار بهالقسم</div>
{% endfor %}
</div>
<div class="bottom-nav">
<a href="/" class="{{ 'active' if not cat else '' }}"><i class="fa-solid fa-house"></i>الرئيسية</a>
<a href="/?cat=عاجل" class="{{ 'active' if cat=='عاجل' else '' }}"><i class="fa-solid fa-fire"></i>عاجل</a>
<a href="/?cat=اقتصاد" class="{{ 'active' if cat=='اقتصاد' else '' }}"><i class="fa-solid fa-chart-line"></i>اقتصاد</a>
<a href="/?cat=رياضة" class="{{ 'active' if cat=='رياضة' else '' }}"><i class="fa-solid fa-futbol"></i>رياضة</a>
<a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a>
</div>
</body></html>
"""

@app.route("/")
def home():
    d = load_data()
    cat = request.args.get("cat")
    news = [x for x in d["news"] if x["category"]==cat] if cat else d["news"]
    return render_template_string(HTML, data=d, news=news, p=get_prices(), cat=cat)

@app.route("/admin", methods=["GET","POST"])
def admin():
    d = load_data()
    if request.method=="POST":
        t = request.form.get("title","").strip()
        if t:
            d["news"].insert(0, {"title": t, "content": request.form.get("content",""), "category": request.form.get("category","عاجل"), "image": "", "time": time.strftime("%H:%M %d-%m-%Y")})
            save_data(d)
        return redirect("/")
    return '<div dir="rtl" style="padding:20px;font-family:Tahoma"><h2>نشر خبر</h2><form method="post"><input name="title" placeholder="عنوان" style="width:100%;padding:10px"><br><br><textarea name="content" placeholder="محتوى" style="width:100%;height:80px"></textarea><br><br><select name="category"><option>عاجل</option><option>اقتصاد</option><option>رياضة</option><option>سياسة</option></select><br><br><button>نشر</button></form></div>'

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
