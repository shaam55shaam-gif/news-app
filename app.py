from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html dir="rtl">
    <head><title>أخبار - جديد</title>
    <style>
    body{font-family:Arial;background:#f5f5f5;padding:20px}
    .card{background:white;padding:15px;margin:10px;border-radius:10px;box-shadow:0 2px 5px #ccc}
    h1{color:#d32f2f}
    </style>
    </head>
    <body>
    <h1>🔥 موقع أخبار شامي - جديد</h1>
    <div class="card"><h2>عاجل: تطورات جديدة في المنطقة</h2><p>هذا خبر تجريبي - الموقع شغال 100%</p></div>
    <div class="card"><h2>اقتصاد: أسعار الذهب ترتفع</h2><p>شهدت الأسواق ارتفاعا كبيرا اليوم</p></div>
    <div class="card"><h2>رياضة: مباراة نارية الليلة</h2><p>الكل ينتظر المباراة النهائية</p></div>
    <p style="text-align:center;margin-top:30px">✅ موقعك شغال على Render</p>
    </body></html>
    """

if __name__ == '__main__':
    app.run()
