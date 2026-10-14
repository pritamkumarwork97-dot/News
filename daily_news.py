#!/usr/bin/env python3
"""Builds news.html with ONLY yesterday's (IST) stories. Finite, no scroll-feed.
Run each morning:  python3 daily_news.py   then open news.html
No installs needed (Python 3 standard library only)."""
import json, re, html, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

IST = timezone(timedelta(hours=5, minutes=30))
TARGET = (datetime.now(IST) - timedelta(days=1)).date()   # yesterday
MAX_PER_CAT = 50

# category: (word limit, feeds)  -- edit/add feeds freely
CATS = {
 "India":    (100, ["https://www.thehindu.com/news/national/feeder/default.rss",
                    "https://indianexpress.com/section/india/feed/",
                    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
                    "https://feeds.feedburner.com/ndtvnews-india-news",
                    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
                    "https://www.livemint.com/rss/news"]),
 "World":    (100, ["https://feeds.bbci.co.uk/news/world/rss.xml",
                    "https://www.thehindu.com/news/international/feeder/default.rss",
                    "https://www.aljazeera.com/xml/rss/all.xml",
                    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                    "https://www.theguardian.com/world/rss",
                    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"]),
 "Business": (180, ["https://www.thehindu.com/business/feeder/default.rss",
                    "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
                    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
                    "https://www.livemint.com/rss/companies",
                    "https://www.livemint.com/rss/markets",
                    "https://feeds.bbci.co.uk/news/business/rss.xml",
                    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"]),
 "Science":  (180, ["https://www.thehindu.com/sci-tech/science/feeder/default.rss",
                    "https://www.sciencedaily.com/rss/top/science.xml",
                    "https://phys.org/rss-feed/",
                    "https://www.nature.com/nature.rss",
                    "https://www.theguardian.com/science/rss",
                    "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
                    "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"]),
}

def clean(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    return re.sub(r"\s+", " ", t).strip()

def trim(t, limit):
    w = t.split()
    if len(w) <= limit: return t
    cut = " ".join(w[:limit])
    i = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[:i+1] if i > len(cut)*0.5 else cut.rstrip(",;") + "…"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return ET.fromstring(r.read())

def items(url):
    root = fetch(url)
    src = clean(getattr(root.find("./channel/title"), "text", "")) or url
    for it in root.iter("item"):
        d = it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")
        try: dt = parsedate_to_datetime(d).astimezone(IST)
        except Exception:
            try: dt = datetime.fromisoformat(d.replace("Z", "+00:00")).astimezone(IST)
            except Exception: continue
        if dt.date() != TARGET: continue          # <-- the "only yesterday" rule
        body = clean(it.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
                     or it.findtext("description"))
        yield dict(t=clean(it.findtext("title")), b=body, s=src, l=it.findtext("link"), ts=dt.timestamp())

data = {}
for cat, (limit, feeds) in CATS.items():
    seen, out = set(), []
    for f in feeds:
        try:
            for x in items(f):
                k = x["t"].lower()[:60]
                if k in seen or not x["t"]: continue
                body = x["b"]
                if body.lower().startswith(x["t"].lower()): body = body[len(x["t"]):].lstrip(" -:–—.")
                seen.add(k); x["b"] = trim(body or x["t"], limit); out.append(x)   # limit counts body only, not heading
        except Exception as e:
            print(f"[skip] {f}: {e}")
    out.sort(key=lambda x: -x["ts"])
    data[cat] = out[:MAX_PER_CAT]
    print(cat, len(data[cat]), "stories")

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="theme-color" content="#c2410c">
<title>Yesterday's News</title><style>
:root{--bg:#f6f4ef;--card:#fff;--tx:#1c1c1c;--mu:#6b6b6b;--ac:#c2410c}
@media(prefers-color-scheme:dark){:root{--bg:#121212;--card:#1d1d1d;--tx:#eee;--mu:#9a9a9a;--ac:#fb923c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:Georgia,serif;
display:flex;flex-direction:column;height:100vh;height:100dvh}
header{padding:14px 16px 6px;font:600 13px system-ui;color:var(--mu);text-align:center}
nav{display:flex;gap:8px;justify-content:center;padding:6px;font:600 14px system-ui}
nav button{border:0;padding:7px 14px;border-radius:99px;background:var(--card);color:var(--tx);cursor:pointer}
nav button.on{background:var(--ac);color:#fff}
main{flex:1;display:flex;align-items:center;justify-content:center;padding:12px;min-height:0}
.card{background:var(--card);border-radius:18px;padding:24px;max-width:560px;width:100%;max-height:100%;
overflow:auto;box-shadow:0 4px 24px #0002}
.card h2{margin:0 0 14px;font-size:22px;line-height:1.3}.card p{font-size:18px;line-height:1.6;margin:0 0 16px}
.meta{font:13px system-ui;color:var(--mu)}.meta a{color:var(--ac)}
.done{text-align:center}.done h2{font-size:26px}
footer{display:flex;justify-content:space-between;align-items:center;padding:10px 20px 18px;font:14px system-ui;color:var(--mu)}
footer button{border:0;background:var(--card);color:var(--tx);padding:10px 20px;border-radius:12px;font-size:16px;cursor:pointer}
</style></head><body>
<header id="h"></header><nav id="n"></nav><main><div class="card" id="c"></div></main>
<footer><button id="p">‹ Prev</button><span id="k"></span><button id="x">Next ›</button></footer>
<script>
const D=__DATA__,DATE="__DATE__",cats=Object.keys(D);let cat=cats[0],i=0,sx=0;
const $=id=>document.getElementById(id);
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
function render(){
 $('h').textContent="News of "+DATE+" · nothing more, nothing less";
 $('n').innerHTML=cats.map(c=>`<button class="${c==cat?'on':''}" onclick="cat='${c}';i=0;render()">${c} (${D[c].length})</button>`).join('');
 const L=D[cat],c=$('c');
 if(i>=L.length){c.innerHTML=`<div class="done"><h2>✓ You're all caught up on ${cat}</h2><p class="meta">That was every story for ${DATE}. See you tomorrow.</p></div>`;$('k').textContent="done";return}
 const s=L[i];c.innerHTML=`<div class="meta">${esc(s.s)}</div><h2>${esc(s.t)}</h2><p>${esc(s.b)}</p><div class="meta"><a href="${esc(s.l||'#')}" target="_blank" rel="noopener">Read full story ↗</a></div>`;
 $('k').textContent=(i+1)+" / "+L.length;c.scrollTop=0}
const go=d=>{i=Math.max(0,Math.min(D[cat].length,i+d));render()};
$('p').onclick=()=>go(-1);$('x').onclick=()=>go(1);
document.onkeydown=e=>{if(e.key=='ArrowRight')go(1);if(e.key=='ArrowLeft')go(-1)};
document.ontouchstart=e=>sx=e.touches[0].clientX;
document.ontouchend=e=>{const d=e.changedTouches[0].clientX-sx;if(Math.abs(d)>50)go(d<0?1:-1)};
render();
</script></body></html>"""

out = PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")) \
          .replace("__DATE__", TARGET.strftime("%d %B %Y"))
for fn in ("news.html", "index.html"):
    open(fn, "w", encoding="utf-8").write(out)
print("Done -> news.html (stories for", TARGET, ")")
