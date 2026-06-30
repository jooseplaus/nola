# Nola → Meta tootefeed (Soome) — kasutusjuhend

Iga tund automaatselt uuenev Soome-keelne tootefeed Nola e-poele (WooCommerce), Meta (Facebook/Instagram) kataloogireklaamide jaoks.

## Failid
- `nola_meta_feed.py` — feedi generaator (Python 3.9+, ainsus sõltuvus: `requests`).
- `nola_meta_feed_fi.xml` — valmis feed (150 toodet, RSS 2.0 + `g:` namespace). Toodetud live Nola andmetest.

## Kuidas see töötab (ja miks see pole "lihtsalt CSV")
1. Tooted tulevad Nola **WooCommerce Store API-st** (avalik, ilma logimiseta) — hinnad, pildid, laoseis, SKU, ID.
2. **Toote ID feedis = `{SKU}_{tooteID}`** (nt `LILY-VLG_26851`). See klapib **täpselt** sellega, mida saidi PixelYourSite pixel saadab (`content_ids`). See ongi see osa, mis tagab, et Meta dünaamilised / Advantage+ kataloogireklaamid viivad õige toote õige inimesega kokku. Ilma selleta reklaam jookseb, aga retargeting ei matchi.
3. **Soomekeelne nimi + kirjeldus** loetakse `/fi/` lehe OG-tagidest (Store API tagastab ainult eestikeelse sisu).
4. **Maandumisleht** = soomekeelne `/fi/` URL.
5. Väljund = Meta-spetsile vastav XML: `id, title, description, link, image_link, additional_image_link, availability, condition, price, sale_price, brand, product_type, item_group_id`.

## Käivitamine
```bash
pip install requests
python3 nola_meta_feed.py        # -> kirjutab nola_meta_feed_fi.xml
```
(`products.json` ja `og_cache.json` on vahemälu — tootmises võib need enne igat jooksu kustutada, et andmed oleksid värsked.)

### Ainult osa tooteid Soome (valikuline)
Failis muuda `CATEGORY_SLUGS` — nt `{"kleidid"}` -> ainult kleidid. `None` = kogu kataloog.

## Automaatne iga-tunnine uuenemine (meiepoolne host, kliendiga rääkimist pole vaja)
Feed peab elama avalikul URL-il, mille Meta tunni tagant tõmbab. Meil pole vaja Nola WordPressi ligipääsu — jooksutame generaatorit oma serveris/cronis ja avaldame XML-i.

**Variant A — väike VPS / ser-ver cron:**
```cron
# iga tunni alguses: genereeri feed ja kopeeri veebikausta
0 * * * * cd /opt/nola-feed && rm -f products.json og_cache.json && python3 nola_meta_feed.py && cp nola_meta_feed_fi.xml /var/www/html/nola_meta_feed_fi.xml
```
Avalik URL: `https://sinu-host/nola_meta_feed_fi.xml`

**Variant B — serverless (GitHub Actions + Pages / Vercel cron / Cloudflare):** schedule iga tund, väljund staatilise failina. Sobib, kui ei taha serverit hallata.

## Meta Commerce Manager seadistus (ühekordne, ~5 min)
1. Commerce Manager → **Catalogs** → loo kataloog (tüüp: E-commerce).
2. **Data sources** → **Add items** → **Use a bulk upload** → **Scheduled feed**.
3. Kleebi feedi URL, vali **Hourly**, valuuta **EUR**, keel **Soome**.
4. Salvesta → Meta tõmbab esimese korra kohe, edaspidi iga tund.
5. Seo kataloog Pixeliga (Catalog → Settings → Connected pixel: Nola olemasolev pixel `516887102482798`) — siis töötab dünaamiline retargeting tänu ID-matchile.

## Märkused / leiud (vaba boonus kliendile)
- `/fi/` lehtedel on `og:locale` ekslikult `et_EE` (peaks olema `fi_FI`). Ei takista feedi, aga Soome SEO/jagamise jaoks tasuks SEO-pluginas parandada.
- `product_type` väljal on kategooriate nimed eesti keeles (Store API annab vaikekeele). See on Meta-sisene taksonoomia, kliendile nähtav pole — kosmeetiline.
- Variatiivsetel toodetel kasutatakse grupitaset (üks rida toote kohta), mis vastab pixeli `content_type=product_group`-ile.
