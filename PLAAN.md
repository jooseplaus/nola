# Nola Meta Feed — Tegevusplaan

## Eesmärk
Soome Meta (Facebook/Instagram) reklaamide jaoks automaatselt iga tund uuenev tootekataloog XML-formaadis. Klient: Nola turundaja.

---

## Leitud probleemid (lahendada enne hostingut)

- [ ] **Sisu on eesti keeles, mitte soome keeles** — `/fi/` lehe OG-tagide tõmbamine kas ei tööta või saidil puuduvad soome tõlked. Kriitilisem probleem.
- [ ] **Double-escaping `product_type` väljas** — WooCommerce API tagastab kategooriate nimed HTML-encoded kujul (`&amp;`), kood teeb neile veel korra escape'i → Meta saab `&amp;amp;`. Lahendus: lisada `html.unescape()` enne XML-i kirjutamist.
- [ ] **`TIME_BUDGET = 28 sek` limiit tuleb eemaldada** — praegu katkestab OG-tagide tõmbamise 28 sekundi järel (oli sandbox-limiit). Tootmises peab kogu kataloog läbi käima.
- [ ] **Impordid on faili keskel (rida 210)** — `import json, os, time` peaks olema faili alguses.
- [ ] **`/fi/toode/` vs `/fi/tuote/`** — kontrollida kas soome lingid töötavad (eesti "toode" vs soome "tuote").

---

## Sammud

### Samm 1 — Uurime kas soome tõlked on olemas
- Käivita skript ja vaata mis `og_cache.json` sisse tuleb
- Kui `title` ja `desc` on `null` enamike toodete juures, siis saidil pole tõlkeid

**Kolm varianti:**
- **A) Kasutame eestikeelset sisu** — lihtsaim, aga ei ole ideaalne Soome turule
- **B) Klient lisab soome tõlked WooCommerce'i** — parim lahendus, aga nõuab kliendipoolset tööd
- **C) Automaattõlge (nt DeepL API)** — kesktee, lisab kulu ja keerukust

### Samm 2 — Parandame koodivead
- Fix `product_type` double-escaping
- Eemalda `TIME_BUDGET` piirang
- Kogu impordid faili ülaossa
- Kontrolli `/fi/toode/` linkide toimimist

### Samm 3 — Testimine
- Käivita skript päriselt vastu Nola live API-t
- Kontrolli: mitu toodet tuleb välja, kas hinnad on õiged, kas lingid töötavad
- Vaata genereeritud XML läbi Meta feedivalidaatoriga

### Samm 4 — Hosting (avalik URL Meta jaoks)
Feed peab olema avalikul URL-il, mida Meta iga tund tõmbab.

**Soovitus: GitHub Actions + GitHub Pages** (tasuta, serverit pole vaja)
- GitHub Action käivitab skripti iga tund (`cron: '0 * * * *'`)
- Genereeritud XML push'itakse GitHub Pages'i → avalik URL

**Alternatiiv: VPS cron**
```cron
0 * * * * cd /opt/nola-feed && rm -f products.json og_cache.json && python3 nola_meta_feed.py && cp nola_meta_feed_fi.xml /var/www/html/nola_meta_feed_fi.xml
```

### Samm 5 — Meta Commerce Manager seadistus (ühekordne, ~5 min)
1. Commerce Manager → **Catalogs** → loo kataloog (tüüp: E-commerce)
2. **Data sources** → **Add items** → **Use a bulk upload** → **Scheduled feed**
3. Kleebi feedi URL, vali **Hourly**, valuuta **EUR**, keel **Soome**
4. Salvesta → Meta tõmbab esimese korra kohe, edaspidi iga tund
5. Seo kataloog Nola Pixeliga (`516887102482798`) → töötab dünaamiline retargeting

---

## Lahtised küsimused

- [ ] Kas Nola saidil on soome tõlked WooCommerce'is olemas?
- [ ] Eesti turg: kas Eesti tooted ka samasse kataloogi või eraldi? *(Soovitus: eraldi kataloogid)*
- [ ] Hosting: kas on olemas VPS/server või eelistame serverless lahendust (GitHub Actions)?

---

## Staatuse jälgimine

| Samm | Staatus |
|------|---------|
| Soome tõlgete olemasolu kontrollimine | Tegemata |
| Koodivigade parandamine | Tegemata |
| Testimine live andmetega | Tegemata |
| Hosting seadistamine | Tegemata |
| Meta Commerce Manager seadistus | Tegemata |
