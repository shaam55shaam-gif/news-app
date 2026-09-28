import os, json, time
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DATA_FILE = "shami_data.json"

DEFAULT = {
    "site_name": "شامي نيوز",
    "categories": ["عاجل", "سياسة", "اقتصاد", "رياضة", "محلي"],
    "news": [
        {"id": 1, "title": "انطلاق شامي نيوز بحلته الجديدة", "content": "تم تحديث الموقع مع كل الميزات", "category": "عاجل", "image": "", "time": "2026-09-28 16:00"},
        {"id": 2, "title": "خبر اقتصادي", "content": "الدولار مستقر", "category": "اقتصاد", "image": "", "time": "2026-09-28 15:00"},
        {"id": 3, "title": "خبر رياضي", "content": "فوز المنتخب", "category": "رياضة", "image": "", "time": "2026-09-28 14:00"}
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

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>شامي نيوز</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
body{font-family:Tahoma;background:#f2f2f2;margin:0;padding-bottom:70px}
.top{background:#000;color:#fff;padding:10px;display:flex;gap:8px;overflow:auto;font-size:13px}
.top span{background:#222;padding:7px 12px;border-radius:20px;white-space:nowrap}
.head{background:#c40000;color:#fff;padding:14px;display:flex;justify-content:space-between;align-items:center}
.urgent{background:red;color:#fff;padding:10px;text-align:center;font-weight:bold}
.card{background:#fff;margin:10px;padding:12px;border-radius:12px;border-right:6px solid #c40000}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:10px 0}
.nav a{color:#666;text-decoration:none;font-size:11px;text-align:center}
.nav a i{display:block;font-size:20px;margin-bottom:3px}
.nav a.active{color:#c40000}
</style></head><body>
<div class="top"><span>$ {{ p.syp }}</span><span>ذهب $4286</span><span>بتكوين $112k</span></div>
<div class="head"><div><i class="fa fa-bars"></i> <i class="fa fa-search" style="margin-right:10px"></i></div><h2 style="margin:0"><i class="fa fa-newspaper"></i> شامي نيوز</h2></div>
<div class="urgent">عاجل: {{ news[0].title if news else 'مرحبا' }}</div>
<div style="max-width:700px;margin:auto">
{% for n in news %}<div class="card"><h3>{{ n.title }}</h3><p>{{ n.content }}</p><small>{{ n.category }} | {{ n.time }} - <a href="/del/{{ n.id }}" style="color:red">حذف</a></small></div>{% else %}<div style="padding:40px;text-align:center">لا يوجد اخبار</div>{% endfor %}
</div>
<div class="nav">
<a href="/" class="{{ 'active' if not cat else '' }}"><i class="fa fa-home"></i>الرئيسية</a>
<a href="/?cat=عاجل" class="{{ 'active' if cat=='عاجل' else '' }}"><i class="fa fa-fire"></i>عاجل</a>
<a href="/?cat=اقتصاد" class="{{ 'active' if cat=='اقتصاد' else '' }}"><i class="fa fa-chart-line"></i>اقتصاد</a>
<a href="/?cat=رياضة" class="{{ 'active' if cat=='رياضة' else '' }}"><i class="fa fa-futbol"></i>رياضة</a>
<a href="/admin"><i class="fa fa-cog"></i>تحكم</a>
</div>
</body></html>
"""

@app.route("/")
def home():
    d = load()
    cat = request.args.get("cat")
    news = [x for x in d["news"] if x["category"]==cat] if cat else d["news"]
    return render_template_string(HTML, news=news, cat=cat, p={"syp": "13,350/13,450 ل.س"})

@app.route("/admin", methods=["GET","POST"])
def admin():
    d = load()
    if request.method=="POST":
        title = request.form.get("title","").strip()
        if title:
            d["news"].insert(0, {"id": int(time.time()), "title": title, "content": request.form.get("content",""), "category": request.form.get("category","عاجل"), "image": "", "time": time.strftime("%H:%M %d-%m")})
            save(d)
        return redirect("/admin")
    html = '<div dir="rtl" style="padding:20px;font-family:Tahoma;max-width:600px;margin:auto"><h2>لوحة التحكم</h2><form method="post"><input name="title" placeholder="عنوان" style="width:100%;padding:10px" required><br><br><textarea name="content" placeholder="محتوى" style="width:100%;height:80px"></textarea><br><br><select name="category"><option>عاجل</option><option>اقتصاد</option><option>رياضة</option><option>سياسة</option></select><br><br><button style="padding:10px 20px;background:#c40000;color:#fff;border:none">نشر</button></form><br><a href="/">رجوع</a><hr>'
    for n in d["news"]:
        html+= f'<div>{n["title"]} <a href="/del/{n["id"]}" style="color:red">حذف</a></div>'
    return html+'</div>'

@app.route("/del/<int:nid>")
def delete(nid):
    d = load()
    d["news"] = [x for x in d["news"] if x.get("id")!=nid]
    save(d)
    return redirect(request.referrer or "/")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
