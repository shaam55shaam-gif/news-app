from flask import Flask
import feedparser
from datetime import datetime

app = Flask(__name__)

def get_news():
    try:
        # جوجل نيوز عربي - أخبار عاجلة
        url = "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar"
        feed = feedparser.parse(url)
        news = []
        for entry in feed.entries[:15]:
            news.append({
                "title": entry.title,
                "link": entry.link,
                "time": entry.published[:16] if hasattr(entry, 'published') else ""
            })
        return news
    except:
        return [{"title":"حدث خطأ في جلب الأخبار - جرب تحديث الصفحة","link":"#","time":""}]

@app.route('/')
def home():
    news_list = get_news()
    cards = ""
    for n in news_list:
        cards += f"""
        <div class="card">
            <h2><a href="{n['link']}" target="_blank" style="text-decoration:none;color:#111">{n['title']}</a></h2>
            <small style="color:gray">{n['time']} | Google News</small>
        </div>
        """

    return f"""
    <html dir="rtl">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>أخبار شامي - مباشر</title>
        <style>
            body{{font-family:Tahoma,Arial;background:#f0f2f5;margin:0;padding:0}}
            .header{{background:#d32f2f;color:white;padding:20px;text-align:center;position:sticky;top:0}}
            .container{{max-width:700px;margin:auto;padding:15px}}
            .card{{background:white;padding:15px;margin:12px 0;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}}
            .card h2{{margin:0 0 5px;font-size:18px;line-height:1.5}}
            .card:hover{{transform:scale(1.01);transition:0.2s}}
            .footer{{text-align:center;padding:20px;color:gray}}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 أخبار شامي - مباشر الآن</h1>
            <p>آخر تحديث: {datetime.now().strftime('%H:%M:%S')} - يتحدث تلقائيا</p>
        </div>
        <div class="container">
            {cards}
        </div>
        <div class="footer">✅ موقعك شغال 24/7 على Render | تم التحديث بواسطة Meta AI</div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run()
