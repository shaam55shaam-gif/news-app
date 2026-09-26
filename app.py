from flask import Flask,request,jsonify,Response,redirect
import feedparser,requests,os,json,time,concurrent.futures,urllib.parse,re
app=Flask(__name__)
HEADERS={'User-Agent':'Mozilla/5.0'}
DATA="shami_data.json"
def load():
 try:
  with open(DATA,"r")as f:return json.load(f)
 except:return{"syp":15250}
def save(d):
 open(DATA,"w").write(json.dumps(d))
FEEDS=["الكل","عاجل 🔴","رياضة ⚽","سياسة 🏛️","اقتصاد 💰","فن 🎭","أسعار 💱"]
# مصادر شغالة 100% على Render
SRC={
 "رياضة ⚽":[
  {"u":"https://www.yallakora.com/rss/rss.aspx","n":"يلا كورة"},
  {"u":"https://www.bbc.com/arabic/sport/rss.xml","n":"BBC رياضة"},
  {"u":"https://www.france24.com/ar/tag/رياضة/rss","n":"France24"},
  {"u":"https://www.kooora.com/rss.aspx","n":"كووورة"},
 ],
 "سياسة 🏛️":[
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.france24.com/ar/rss","n":"France24"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي"},
  {"u":"https://arabic.cnn.com/rss","n":"CNN"},
  {"u":"https://www.aljazeera.net/xml/rss/all.xml","n":"الجزيرة"},
 ],
 "اقتصاد 💰":[
  {"u":"https://www.cnbcarabia.com/rss","n":"CNBC"},
  {"u":"https://www.alarabiya.net/.mrss/ar/business.xml","n":"العربية"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي اقتصاد"},
 ],
 "فن 🎭":[
  {"u":"https://www.bbc.com/arabic/art-and-culture/rss.xml","n":"BBC فن"},
  {"u":"https://www.france24.com/ar/tag/ثقافة/rss","n":"ثقافة"},
  {"u":"https://www.skynewsarabia.com/web/rss","n":"سكاي فن"},
 ],
 "عاجل 🔴":[
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
  {"u":"https://www.aljazeera.net/xml/rss/all.xml","n":"الجزيرة"},
 ],
 "الكل":[
  {"u":"https://www.bbc.com/arabic/index.xml","n":"BBC"},
 ]
}
CACHE={}
def get_img(e):
 try:
  if hasattr(e,'media_content'):return e.media_content[0]['url']
 except:pass
 m=re.search(r'src="([^"]+)"',getattr(e,'description',''))
 return m.group(1) if m else "https://images.unsplash.com/photo-1495020689067?w=600"
def fetch_one(s):
 try:
  r=requests.get(s["u"],headers=HEADERS,timeout=7)
  f=feedparser.parse(r.content)
  out=[]
  for en in f.entries[:5]:
   out.append({"title":en.title,"link":en.link,"time":en.get("published","")[:16],"source":s["n"],"image":get_img(en)})
  return out
 except:return []
def get_news(cat):
 k=cat
 if k in CACHE and time.time()-CACHE[k][0]<180:return CACHE[k][1]
 srcs=SRC.get(cat,SRC["الكل"])[:4]
 all_n=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for res in ex.map(fetch_one,srcs):all_n.extend(res)
 CACHE[k]=(time.time(),all_n[:25])
 return all_n[:25]
def prices():
 d=load()
 return {"syp":d["syp"],"btc":"$84k","gold":"$4286","updated":time.strftime("%H:%M")}
@app.route('/')
def home():
 cat=request.args.get('cat','الكل')
 if cat=="أسعار 💱":
  p=prices()
  return f"<h1>الاسعار {p['syp']}</h1>"
 news=get_news(cat)
 tabs="".join([f'<a href="/?cat={urllib.parse.quote(c)}">{c}</a> ' for c in FEEDS])
 cards
