from flask import Flask, request
import feedparser
from datetime import datetime
import urllib.parse

app = Flask(__name__)

FEEDS = {
    "الكل": "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=EG&ceid=EG:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة&hl=ar&gl=EG&ceid=EG:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=EG&ceid=EG:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة&hl=ar&gl=EG&ceid=EG:ar"
}

def get_news(category="الكل"):
    url = FEEDS.get(category, FEEDS["الكل"])
    try:
        feed = feedparser.parse(url)
        news = []
        for i, entry in enumerate(feed.entries[:20]):
            # صورة وهمية حلوة حسب الخبر
            img_id = 100 + i
            image = f"https://picsum.photos/seed/{urllib.parse.quote(entry.title[:10])}/600/350"
            
            # رابط مشاركة واتساب
            share_text = f"{entry.title} - عبر موقع أخبار شامي {entry.link}"
            wa_link = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
            
            news.append({
                "title": entry.title,
                "link": entry.link,
                "time": entry.published[:22] if hasattr(entry, 'published') else "",
                "source": entry.source.title if hasattr(entry, 'source') else "Google News",
                "image": image,
                "wa": wa_link
            })
        return news
    except Exception as e:
        return []

@app.route('/')
def home():
    cat = request.args.get('cat', 'الكل')
    news_list = get_news(cat)
    
    # ازرار الأقسام
    tabs = ""
    for name in FEEDS.keys():
        active = "active" if name==cat else ""
        tabs += f'<a href="/?cat={urllib.parse.quote(name)}" class="tab {active}">{name}</a>'

    cards = ""
    for idx, n in enumerate(news_list):
        # اعلان بعد كل 5 اخبار
        ad = ""
        if idx==4:
            ad = """
            <div class="card ad">
                <small>إعلان</small>
                <p>📢 مساحة إعلانية - هنا بتحط كود Google AdSense وبتصير تربح مصاري</p>
                <code>ضع كود AdSense هنا</code>
            </div>
            """
        
        cards += f"""
        <div class="card">
            <img src="{n['image']}" loading="lazy">
            <div class="card-body">
                <span class="source">{n['source']} | {n['time']}</span>
                <h2><a href="{n['link']}" target="_blank">{n['title']}</a></h2>
                <div class="actions">
                    <a href="{n['link']}" target="_blank" class="btn read">اقرأ الخبر ↗</a>
                    <a href="{n['wa']}" target="_blank" class="btn wa">شارك واتساب 💬</a>
                </div>
            </div>
        </div>
        """ + ad

    return f"""
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>أخبار شامي - {cat} مباشر</title>
        <meta name="description" content="موقع أخبار شامي - أخبار مباشرة 24 ساعة">
        <style>
            *{{box-sizing:border-box}} 
            body{{font-family:Tahoma,Arial;background:#f0f2f5;margin:0}}
            .header{{background:#b71c1c;color:white;padding:18px;text-align:center;position:sticky;top:0;z-index:10}}
            .header h1{{margin:0;font-size:26px}}
            .tabs{{display:flex;gap:8px;overflow-x:auto;padding:12px;background:white;position:sticky;top:76px;z-index:9;box-shadow:0 2px 5px rgba(0,0,0,0.1)}}
            .tab{{white-space:nowrap;padding:8px 16px;border-radius:20px;background:#eee;text-decoration:none;color:#333;font-weight:bold}}
            .tab.active{{background:#d32f2f;color:white}}
            .container{{max-width:750px;margin:auto;padding:10px}}
            .card{{background:white;border-radius:14px;overflow:hidden;margin:14px 0;box-shadow:0 3px 10px rgba(0,0,0,0.08)}}
            .card img{{width:100%;height:200px;object-fit:cover;background:#ddd}}
            .card-body{{padding:14px}}
            .source{{color:#888;font-size:12px}}
            .card h2{{margin:8px 0 12px;font-size:18px;line-height:1.6}}
            .card h2 a{{text-decoration:none;color:#111}}
            .actions{{display:flex;gap:10px}}
            .btn{{flex:1;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px}}
            .btn.read{{background:#111;color:white}}
            .btn.wa{{background:#25D366;color:white}}
            .card.ad{{background:#fff9c4;border:2px dashed #fbc02d;padding:15px;text-align:center}}
            .footer{{text-align:center;padding:30px;color:#888;line-height:1.8}}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 أخبار شامي</h1>
            <p style="margin:5px 0 0">مباشر الآن - {datetime.now().strftime('%H:%M')} - {cat}</p>
        </div>
        <div class="tabs">{tabs}</div>
        <div class="container">{cards}</div>
        <div class="footer">
            ✅ موقعك شغال 24/7<br>
            💰 للربح: سجل في Google AdSense وحط الكود مكان الإعلان<br>
            صنع بواسطة شامي و Meta AI ❤️
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run()
