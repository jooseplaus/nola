# Nola Meta Feed — Tegevusplaan

## Eesmärk
Soome Meta (Facebook/Instagram) reklaamide jaoks automaatselt iga tund uuenev tootekataloog XML-formaadis. Klient: Nola turundaja.

---

## Kuidas süsteem töötab (lõplik lahendus)

```
nola.ee WooCommerce          GitHub Actions               Meta
─────────────────────        ──────────────────           ────────────────
Store API (tooted,     →     Iga tunni alguses      →     Commerce Manager
hinnad, pildid,              käivitab Python              tõmbab XML-i iga
laoseis, SKU)                skripti. Skript              tund automaatselt
                             küsib iga toote              ja uuendab
/fi/toode/... lehed   →     soome lehe JSON-LD     →     kataloogireklaamid
(soome tõlked               andmeid (nimi +               reaalajas.
JSON-LD formaadis)          kirjeldus soome k.)
                             Kirjutab XML-i ja
                             push'ib GitHubi.
```

**Avalik feed URL (turundajale anda):**
```
https://jooseplaus.github.io/nola/nola_meta_feed_fi.xml
```

**Feed uueneb:** iga tund automaatselt, ilma et keegi midagi tegema peaks.

**Repo:** `github.com/jooseplaus/nola`

---

## Leitud probleemid ja lahendused

- [x] **Sisu oli eesti keeles** — Nola sait kasutab OG-tagide asemel JSON-LD formaati. Skript kirjutati ümber JSON-LD parseriga → 150/150 toodet soome keeles.
- [x] **Double-escaping `product_type` väljas** — lisati `html.unescape()` kategooriate nimedele.
- [x] **`TIME_BUDGET = 28 sek` limiit** — eemaldatud, skript käib kõik tooted lõpuni läbi.
- [x] **Impordid faili keskel** — koondatud faili ülaossa.
- [x] **`/fi/toode/` lingid** — kontrollitud, töötavad (eestikeelne "toode" slug toimib soome lehel).
- [x] **24 paralleelset threadi throttle'is serveri** — vähendatud 6-le, timeout 15s → 30s. Cache proovib `None` tulemusi uuesti järgmisel käivitusel.

---

## Sammud

### ✅ Samm 1 — Soome tõlgete olemasolu kontrollimine
Nola saidil on soome tõlked olemas. `/fi/toode/kleit-alice/` → "Mekko Alice", kirjeldus soome keeles.
Tõlked on JSON-LD `<script type="application/ld+json">` blokkides, mitte OG-tagides.

### ✅ Samm 2 — Koodivigade parandamine
Kõik vead parandatud. Skript genereerib 150 toodet soome keeles õigete hindade ja linkidega.

### ✅ Samm 3 — Testimine live andmetega
150/150 toodet soome keeles. Hinnad, soodushinnad, pildid, lingid — kõik korras.

### ✅ Samm 4 — Hosting seadistatud
- GitHub Actions workflow (`.github/workflows/feed.yml`) käivitab skripti iga tund
- GitHub Pages serveerib XML-i avalikul URL-il
- Feed aadress: `https://jooseplaus.github.io/nola/nola_meta_feed_fi.xml`

### Samm 5 — Meta Commerce Manager seadistus (turundaja teeb)
1. Commerce Manager → **Catalogs** → loo kataloog (tüüp: E-commerce, nimi: "Nola Studio - Suomi")
2. **Data sources** → **Add items** → **Use a bulk upload** → **Scheduled feed**
3. Sisesta URL: `https://jooseplaus.github.io/nola/nola_meta_feed_fi.xml`
4. Vali: **Hourly**, valuuta **EUR**, keel **Finnish**
5. Salvesta → Meta tõmbab esimese korra kohe
6. Seo kataloog Nola Pixeliga (`516887102482798`) → töötab dünaamiline retargeting

---

## Lahtised küsimused

- [x] Kas Nola saidil on soome tõlked? — **Jah, on olemas**
- [x] Hosting — **GitHub Actions + Pages, tasuta**
- [ ] Eesti turg: kas Eesti tooted ka kataloogi? *(Soovitus: eraldi kataloog, eraldi skripti käivitus)*

---

## Staatuse jälgimine

| Samm | Staatus |
|------|---------|
| Soome tõlgete olemasolu kontrollimine | ✅ Valmis |
| Koodivigade parandamine | ✅ Valmis |
| Testimine live andmetega | ✅ Valmis |
| Hosting seadistamine (GitHub Actions + Pages) | ✅ Valmis |
| Meta Commerce Manager seadistus | Turundaja teeb |
