#!/usr/bin/env python3
"""
Nola -> Meta (Facebook/Instagram) tootefeed, Soome turg.

Loogika:
  1. Tooted tulevad WooCommerce Store API-st (avalik, ilma autentimiseta).
     API annab hinnad, pildid, laoseisu, SKU ja toote ID (vaikekeel = eesti).
  2. Toote ID feedis = "{SKU}_{id}" -> KLAPIB PixelYourSite content_id-ga
     ({SKU}_{post_id}), mis on dünaamiliste kataloogireklaamide jaoks kriitiline.
  3. Soomekeelne nimi + kirjeldus tulevad /fi/ lehe JSON-LD (Schema.org) andmetest
     (Store API ei tagasta tõlkeid; sait ei kasuta OG meta-tagsid).
  4. Maandumisleht = /fi/ permalink.
  5. Väljund: Meta-ühilduv RSS 2.0 XML (g: namespace).

Käivita: python3 nola_meta_feed.py  ->  kirjutab nola_meta_feed_fi.xml
"""

import html
import json
import os
import re
import sys
import time
import xml.sax.saxutils as sx
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

BASE = "https://nola.ee"
STORE_API = f"{BASE}/wp-json/wc/store/v1/products"
BRAND = "Nola"
OUTPUT = "nola_meta_feed_fi.xml"
WORKERS = 6
TIMEOUT = 30

# --- valikuline filter: lisa feedi ainult need tooted, mida Soomes reklaamitakse.
# Jäta None-ks -> kogu kataloog. Või pane kategooria-slug'id, nt {"kleidid"}.
CATEGORY_SLUGS = None

session = requests.Session()
session.headers.update({"User-Agent": "Nola-Meta-Feed/1.0 (+timeffect)"})

NUM_RE = re.compile(r"(\d[\d\s.,]*\d|\d)")


def fetch_all_products():
    """Lehekülgede kaupa kõik tooted Store API-st."""
    products, page = [], 1
    while True:
        r = session.get(STORE_API, params={"per_page": 100, "page": page}, timeout=TIMEOUT)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return products


def parse_price_html(price_html, prices):
    """Tagastab (regular, sale|None) kümnendarvuna stringina."""
    def first_num(text):
        m = NUM_RE.search(re.sub(r"&nbsp;| ", " ", text))
        if not m:
            return None
        raw = m.group(1).replace(" ", "").replace(",", "")
        try:
            return f"{float(raw):.2f}"
        except ValueError:
            return None

    if price_html:
        clean = html.unescape(price_html)
        dele = re.search(r"<del>(.*?)</del>", clean, re.S)
        ins = re.search(r"<ins>(.*?)</ins>", clean, re.S)
        if dele and ins:
            reg = first_num(re.sub(r"<.*?>", "", dele.group(1)))
            sale = first_num(re.sub(r"<.*?>", "", ins.group(1)))
            if reg and sale:
                return reg, sale
        only = first_num(re.sub(r"<.*?>", "", clean))
        if only:
            return only, None

    # fallback: Store API minor units
    try:
        unit = 10 ** prices.get("currency_minor_unit", 2)
        reg = f"{int(prices['regular_price'])/unit:.2f}"
        sale_raw = prices.get("sale_price")
        sale = f"{int(sale_raw)/unit:.2f}" if sale_raw and sale_raw != prices["regular_price"] else None
        return reg, sale
    except Exception:
        return None, None


def fi_link(permalink):
    return permalink.replace(f"{BASE}/", f"{BASE}/fi/", 1)


JSONLD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)


def fetch_fi_meta(slug, permalink):
    """Soomekeelne nimi + kirjeldus /fi/ lehe JSON-LD andmetest.

    Nola sait ei kasuta OG meta-tagsid — kasutab Schema.org JSON-LD formaati.
    Otsime WebPage või Product objektist name ja description.
    """
    url = fi_link(permalink)
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, None
        title, desc = None, None
        for m in JSONLD_RE.finditer(r.text):
            try:
                data = json.loads(m.group(1))
            except (json.JSONDecodeError, ValueError):
                continue
            # @graph nimekirjas võib olla mitu objekti
            objects = data.get("@graph", [data])
            for obj in objects:
                obj_type = obj.get("@type", "")
                if not title and obj_type in ("WebPage", "Product", "ItemPage"):
                    raw = obj.get("name") or obj.get("headline")
                    if raw:
                        title = re.sub(r"\s*[-–]\s*Nola Studio\s*$", "", str(raw).strip())
                if not desc and obj_type == "Product":
                    raw = obj.get("description")
                    if raw:
                        desc = strip_html(str(raw))
            if title and desc:
                break
        return title or None, desc or None
    except requests.RequestException:
        return None, None


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<.*?>", " ", html.unescape(s or ""))).strip()


def build_item(p, fi_title=None, fi_desc=None):
    if CATEGORY_SLUGS is not None:
        slugs = {c["slug"] for c in p.get("categories", [])}
        if not (slugs & CATEGORY_SLUGS):
            return None

    sku = (p.get("sku") or "").strip()
    pid = p["id"]
    item_id = f"{sku}_{pid}" if sku else str(pid)

    reg, sale = parse_price_html(p.get("price_html", ""), p.get("prices", {}))
    if not reg:
        return None

    title = fi_title or p["name"]
    desc = fi_desc or strip_html(p.get("short_description")) or title

    images = [im["src"] for im in p.get("images", []) if im.get("src")]
    if not images:
        return None

    availability = "in stock" if p.get("is_in_stock") else "out of stock"
    product_type = " > ".join(html.unescape(c["name"]) for c in p.get("categories", [])[:3])

    return {
        "id": item_id,
        "title": title,
        "description": desc[:9000],
        "link": fi_link(p["permalink"]),
        "image_link": images[0],
        "additional_image_link": images[1:10],
        "availability": availability,
        "condition": "new",
        "price": f"{reg} EUR",
        "sale_price": f"{sale} EUR" if sale else None,
        "brand": BRAND,
        "product_type": product_type,
        "item_group_id": item_id,
    }


def x(s):
    return sx.escape(str(s)) if s is not None else ""


def render_xml(items):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">',
           '<channel>',
           '<title>Nola Studio - Suomi</title>',
           f'<link>{BASE}/fi/</link>',
           '<description>Nola Studio tuotesyote Meta-mainontaa varten (Suomi)</description>',
           f'<lastBuildDate>{now}</lastBuildDate>']
    for it in items:
        out.append('<item>')
        out.append(f'<g:id>{x(it["id"])}</g:id>')
        out.append(f'<g:title>{x(it["title"])}</g:title>')
        out.append(f'<g:description>{x(it["description"])}</g:description>')
        out.append(f'<g:link>{x(it["link"])}</g:link>')
        out.append(f'<g:image_link>{x(it["image_link"])}</g:image_link>')
        for img in it["additional_image_link"]:
            out.append(f'<g:additional_image_link>{x(img)}</g:additional_image_link>')
        out.append(f'<g:availability>{x(it["availability"])}</g:availability>')
        out.append(f'<g:condition>{x(it["condition"])}</g:condition>')
        out.append(f'<g:price>{x(it["price"])}</g:price>')
        if it["sale_price"]:
            out.append(f'<g:sale_price>{x(it["sale_price"])}</g:sale_price>')
        out.append(f'<g:brand>{x(it["brand"])}</g:brand>')
        if it["product_type"]:
            out.append(f'<g:product_type>{x(it["product_type"])}</g:product_type>')
        out.append(f'<g:item_group_id>{x(it["item_group_id"])}</g:item_group_id>')
        out.append('</item>')
    out.append('</channel></rss>')
    return "\n".join(out)


PRODUCTS_CACHE = "products.json"
OG_CACHE = "og_cache.json"


def main():
    # 1) Tooted (cache, et reruns oleks kiire)
    if os.path.exists(PRODUCTS_CACHE):
        products = json.load(open(PRODUCTS_CACHE, encoding="utf-8"))
    else:
        print("Laen tooted Store API-st ...", file=sys.stderr)
        products = fetch_all_products()
        json.dump(products, open(PRODUCTS_CACHE, "w", encoding="utf-8"))
    print(f"{len(products)} toodet.", file=sys.stderr)

    # 2) Soomekeelne OG-sisu (resumable cache)
    og = json.load(open(OG_CACHE, encoding="utf-8")) if os.path.exists(OG_CACHE) else {}
    todo = [p for p in products if og.get(str(p["id"]), {}).get("title") is None]
    print(f"OG puudu: {len(todo)}", file=sys.stderr)

    ex = ThreadPoolExecutor(max_workers=WORKERS)
    futs = {ex.submit(fetch_fi_meta, p["slug"], p["permalink"]): p for p in todo}
    n = 0
    for f in as_completed(futs):
        p = futs[f]
        try:
            t, d = f.result()
        except Exception:
            t, d = None, None
        og[str(p["id"])] = {"title": t, "desc": d}
        n += 1
        if n % 20 == 0:  # vahesalvestus
            json.dump(og, open(OG_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    ex.shutdown(wait=True)
    json.dump(og, open(OG_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    done = sum(1 for p in products if str(p["id"]) in og)
    print(f"OG valmis: {done}/{len(products)}", file=sys.stderr)

    # 3) Renderda feed olemasolevast (osaline või täielik)
    items = []
    for p in products:
        meta = og.get(str(p["id"]), {})
        it = build_item(p, meta.get("title"), meta.get("desc"))
        if it:
            items.append(it)
    items.sort(key=lambda i: i["id"])
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(render_xml(items))
    print(f"Valmis: {OUTPUT} ({len(items)} toodet feedis)", file=sys.stderr)


if __name__ == "__main__":
    main()
