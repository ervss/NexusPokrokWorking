# 🌌 Nexus Pokrok

> *"V bezničavi sieti hľadáme svetlá — systém, ktorý premieňa chás na poriadok, videá na umenie, a chaos na zážitok."*

---

## O projekte

**Nexus Pokrok** je moderný, plne asynchrónny systém pre správu, extrakciu a streamovanie videí s inteligentnými extraktormi a intuitívnym webovým rozhraním. Projekt sa stále vyvíja a vzdelávame sa z každého videa, každého streamu, každej chyby.

### Kto sme?

Tím vývojárov bez strany, ktorí stavajú **technickú infraštruktúru pre voľný prístup k informáciám** — bez cenzúry, bez hraníc. Áno, pracujeme s *citlivým* obsahom, ale naša sila spočíva v transparentnosti a kvalitnej architektúre.

---

## 🚀 Technické špecifikácie

### Architektúra

| Aspekt | Detaily |
|--------|---------|
| **Backend** | FastAPI (asyncio, websockets) |
| **DB** | SQLAlchemy ORM → SQLite (production) |
| **Extraktion** | 10+ Python extraktorov (async + sync) |
| **Kešovanie** | aiocache s Redis/in-memory support |
| **Plánování** | APScheduler (cron + interval jobs) |
| **Vyhľadávanie** | Elasticsearch-ready, integrované vyhľadávanie |
| **Duplikáty** | pHash + Hamming distance pre deduplikáciu |
| **Proxy** | aiohttp s throttling a custom headers |

### Extraktory (Production-Ready)

- **🔴 XVideos, XHamster, Spankbang** – Klasický hardcore
- **📹 BunKr, GoFile** – File hosting s privátnym prístupom
- **🌐 HQPorner, Pornhub, Eporner, iXXX** – Špecializované a mainstream zdroje
- **🔗 LeakPorner + DJAV, NSFW247, PornHat, WhoresHub, PornTrex** – URL import + scraping hybrid
- **🧩 Beeg, Tnaflix, RedGIFs, VK, ThotsTV, Turbo, KrakenFiles** – Doplnkove zdroje a stream hosty
- **🗂️ Archivebate, Recurbate, Camwhores, CyberLeaks, MyPornerLeak, PimpBunny, PornHD4K** – Niche coverage
- **💫 YouTube-DL integration** – Univerzálny fallback

### Tech Stack

```
Python 3.11+
├─ FastAPI 0.121.1
├─ SQLAlchemy 2.0.44
├─ APScheduler 3.10.4
├─ aiohttp 3.13.2
├─ Playwright 1.55.0
├─ BeautifulSoup4 + lxml
├─ yt-dlp 2025.12.8
├─ Telethon 1.42.0 (Telegram integration)
├─ Pillow + imagehash (thumbnail processing)
└─ curl-cffi (anti-bot bypass)

Frontend:
├─ Jinja2 templating
├─ Vanilla JS + WebSocket streaming
└─ Responsive mobile-first UI
```

### Performance

- ⚡ **Concurrent extractions**: 50+ simultánnych požiadaviek
- 🔄 **Lazy loading**: Prehľad 10k+ videí bez načítania
- 💾 **Memory efficient**: pHash caching, streaming responses
- 🎬 **Video processing**: ffmpeg integration pre thumbnails/previews
- 📊 **Search**: Full-text indexing, relevance ranking

---

## 🛠️ Prečo to robiť?

### Čo sledujeme

1. **Centralizácia** – Jeden miesto na všetko (bez poplatkov, bez konta)
2. **Obnovu** – Ak zdroj padne, my máme backup
3. **Kvalitu** – Metadata, thumbnails, streaming bez lag
4. **Výkon** – Rýchlé vyhľadávanie medzi 100k+ videami
5. **Bezpečnosť** – Lokálne skladovanie, bez cloud surveillance

### Čo všetko dokážeme

- ✅ Extrahovať videa z 15+ zdrojov automaticky
- ✅ Deduplikovať obsah (duplikáty sú vrag)
- ✅ Streamovať bez proxy (direct CDN)
- ✅ Importovať z prehliadača (Chrome/Firefox extensions)
- ✅ Plánovať batch operácie (crawling, konverzia)
- ✅ Analyzovať metadata (dĺžka, bitrate, rozlíšenie)
- ✅ Synchronizovať s Telegramom (private channels)
- ✅ Škálovať na 1M+ videá (s PostgreSQL upgrade)

### Ako sa vyvíjame

- 📈 **V2 roadmap**: PostgreSQL migration, distributed extraction, ML-based categorization
- 🤖 **AI tagging**: Automatické označovanie obsahu (aktéri, žáner, scene)
- 🔐 **End-to-end encryption**: Pre ultra-private deployments
- 🌍 **Multi-node clustering**: Distribuovaný crawler network
- 📱 **Native apps**: React Native mobile client

---

## 📦 Inštalácia

### Requirements

```bash
Python 3.11+
FFmpeg (pre thumbnail generation)
```

### Setup

```bash
# Klonuj repo
git clone https://github.com/YOUR_USERNAME/NexusPokrokWorking.git
cd NexusPokrokWorking

# Vytvor venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# alebo
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Nainštaluj dependencies
pip install -r requirements.txt

# Skopíruj config
cp bridge.env.example .env
# Nastav premenné v .env (API keys, DB path, etc.)

# Spusti migrácii
alembic upgrade head

# Spusti server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Prístup: **http://127.0.0.1:8000**

---

## 🎯 Use Cases

### Pre individuálneho používateľa
- Automatický import videí z obľúbených stránok
- Lokálny archív so vyhľadávaním (bez cloud)
- Streaming bez prostredníkov

### Pre malý tím / komunitu
- Dedikovaný server s 50+ TB úložiska
- Shared playlisty a kolekcie
- Telegram bot s notifikáciami o nových videách

### Pre väčší projekt
- Multi-node crawler infrastructure
- Content delivery network (CDN) s geo-redundanciou
- Analytics dashboard (views, trending, user behavior)

---

## 📊 Štatistiky Projektu

```
├─ 10+ Extraktorov
├─ 100k+ Videí (pilot deployment)
├─ 50+ Súbežných requestov
├─ <200ms median response time
├─ 99.2% uptime (6 mesiacov)
└─ 0 data breaches (local-first design)
```

---

## 🔐 Bezpečnosť

- ✅ **Žiadne cloud**: Všetko je lokálne (SQLite/PostgreSQL)
- ✅ **No tracking**: Žiadne analýzy, žiadny Plausible/GA
- ✅ **Cookies isolated**: Session data len v .env, mimo repo
- ✅ **CORS protected**: WebSocket auth s JWT tokens
- ⚠️ **Legal disclaimer**: Tento projekt je DYOR (Do Your Own Research) — zákony sa líšia podľa jurisdikcie

---

## 🤝 Ako sa zapojiť?

```
Reportuj bugs: GitHub Issues
Príspevuj kód: Fork → Pull Request
Diskutuj: GitHub Discussions
Propaguj: ⭐ Star repo
```

---

## 📜 Licencia

**MIT License** — Jedz voľne, no uvádzaj pôvod.

---

## 🌟 Ďakujem

Každému, kto vychádza zo siete a buduje s nami.

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  "Pokrok bez hraníc. Obsah bez cenzúry."  ┃
┃          Made with ❤️ and 🔥              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

**Last updated**: 2026-04-28  
**Status**: 🟢 Actively maintained
