HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ data.site_name }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
body{font-family:Tahoma,Arial;background:#f2f2f2;margin:0;padding-bottom:70px}
.top-bar{background:#111;color:#fff;padding:8px 10px;display:flex;gap:10px;font-size:13px;overflow:hidden}
.top-bar span{background:#222;padding:6px 12px;border-radius:20px;white-space:nowrap;flex-shrink:0}
.header{background:#c40000;color:#fff;padding:12px 15px;display:flex;justify-content:space-between;align-items:center}
.header h1{margin:0;font-size:20px}
.urgent-bar{background:#ff0000;color:#fff;padding:10px;text-align:center;font-weight:bold;animation:blink 1s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:0.6}}
.card{background:#fff;margin:10px;padding:12px;border-radius:12px;box-shadow:0 2px 5px rgba(0,0,0,.08)}
.card img{width:100%;border-radius:8px;max-height:300px;object-fit:cover;margin-bottom:8px}
.cat-urgent{border-right:6px solid #d00000;background:#fff5f5}
.cat-politics{border-right:6px solid #004aad}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;display:flex;justify-content:space-around;padding:8px 0;z-index:100}
.bottom-nav a{color:#666;text-decoration:none;text-align:center;font-size:12px}
.bottom-nav a i{display:block;font-size:20px;margin-bottom:3px}
.bottom-nav a.active{color:#c40000}
</style>
</head>
<body>
<div class="top-bar">
<span><i class="fa-solid fa-dollar-sign"></i> دولار: {{ prices.usd_syp }} / {{ prices.usd_syp_sell }}</span>
<span><i class="fa-solid fa-coins"></i> ذهب: ${{ prices.gold }}</span>
<span><i class="fa-brands fa-bitcoin"></i> بيتكوين: ${{ prices.btc }}</span>
<span><i class="fa-regular fa-clock"></i> {{ prices.time }}</span>
</div>

<div class="header">
<h1><i class="fa-solid fa-newspaper"></i> {{ data.site_name }}</h1>
<div>
<i class="fa-solid fa-magnifying-glass" style="margin-left:15px"></i>
<i class="fa-solid fa-bars"></i>
</div>
</div>

{% if urgents %}
<div class="urgent-bar"><i class="fa-solid fa-circle-exclamation"></i> عاجل: {{ urgents[0].title }}</div>
{% endif %}

<div style="max-width:700px;margin:auto">
{% for n in data.news %}
<div class="card {% if n.category=='عاجل' %}cat-urgent{% elif n.category=='سياسة' %}cat-politics{% endif %}">
{% if n.image %}<img src="{{ n.image }}">{% endif %}
<h3 style="margin:5px 0"><i class="fa-solid fa-bolt" style="color:#d00000"></i> {{ n.title }}</h3>
<p style="color:#444;line-height:1.6">{{ n.content }}</p>
<small style="color:#888"><i class="fa-solid fa-tag"></i> {{ n.category }} | <i class="fa-regular fa-clock"></i> {{ n.time }}</small>
</div>
{% endfor %}
</div>

<div class="bottom-nav">
<a href="/" class="active"><i class="fa-solid fa-house"></i>الرئيسية</a>
<a href="#"><i class="fa-solid fa-fire"></i>عاجل</a>
<a href="#"><i class="fa-solid fa-chart-line"></i>اقتصاد</a>
<a href="#"><i class="fa-solid fa-futbol"></i>رياضة</a>
<a href="/admin"><i class="fa-solid fa-gear"></i>تحكم</a>
</div>
</body>
</html>
"""
