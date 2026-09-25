def get_news(cat):
    # مصادر مضمونة لكل فئة - ما بترجع فاضي
    MULTI_FEEDS = {
        "الكل": [
            "https://news.google.com/rss?hl=ar&gl=SA&ceid=SA:ar",
            "https://feeds.bbci.co.uk/arabic/rss.xml"
        ],
        "عاجل 🔴": [
            "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=SA&ceid=SA:ar",
            "https://www.alarabiya.net/.mrss/ar.xml"
        ],
        "رياضة ⚽": [
            "https://news.google.com/rss/search?q=رياضة+كرة+قدم&hl=ar&gl=SA&ceid=SA:ar",
            "https://www.yallakora.com/rss",  # يلا كورة مباشر
            "https://news.google.com/rss/search?q=الدوري+السعودي+ريال+برشلونة&hl=ar&gl=SA&ceid=SA:ar"
        ],
        "اقتصاد 💰": [
            "https://news.google.com/rss/search?q=اقتصاد+اسهم+ذهب&hl=ar&gl=SA&ceid=SA:ar",
            "https://www.alarabiya.net/.mrss/ar/business.xml"
        ],
        "سياسة 🏛️": [
            "https://news.google.com/rss/search?q=سياسة+الشرق+الاوسط&hl=ar&gl=SA&ceid=SA:ar",
            "https://feeds.bbci.co.uk/arabic/topics/مصر/rss.xml"
        ],
        "ثقافية 🎭": [
            "https://news.google.com/rss/search?q=ثقافة+فن+كتب&hl=ar&gl=SA&ceid=SA:ar",
            "https://news.google.com/rss/search?q=افلام+مسلسلات+ثقافة&hl=ar&gl=SA&ceid=SA:ar"
        ]
    }
    
    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat or n.get("category")=="الكل"]
    
    all_news = []
    # جرب كل الروابط للفئة حتى تلاقي أخبار
    for feed_url in MULTI_FEEDS.get(cat, MULTI_FEEDS["الكل"]):
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                for e in feed.entries[:10]:
                    all_news.append({
                        "title": e.title,
                        "link": e.link,
                        "time": getattr(e,'published','')[:22] or datetime.now().strftime("%H:%M"),
                        "source": getattr(e.source,'title','Google') if hasattr(e,'source') else "شامي",
                        "image": get_image(e),
                        "wa": f"https://wa.me/?text={urllib.parse.quote(e.title+' '+e.link)}",
                        "is_custom": False,
                        "category": cat
                    })
                if len(all_news) >= 8: break
        except: continue
    
    # إذا لسا فاضي حط أخبار افتراضية مشان ما يبين فاضي
    if not all_news:
        all_news = [{"title": f"لا توجد أخبار {cat} حاليا - جاري التحديث...","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":"https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600","wa":"#","is_custom":False,"category":cat}]
    
    return cf + all_news
