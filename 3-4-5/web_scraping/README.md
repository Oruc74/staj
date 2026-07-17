# Web Scraping — Nasıl Çalıştırılır?

Bu klasördeki her alt klasör, farklı bir web scraping yöntemini gösterir.
Hedefler ağırlıklı olarak Türkçe kaynaklardır (Vikipedi, Vikisöz, Wikimedia
API'leri). Aşağıdaki adımları takip ederek hepsini kendi bilgisayarında
çalıştırabilirsin.

## 1) Sanal ortamı aktive et

PowerShell'de bu klasöre gel ve sanal ortamı aktive et:

```powershell
cd "C:\Users\orucs\OneDrive\Desktop\staj\3-4-5\web_scraping"
.\venv\Scripts\Activate.ps1
```

Aktive olunca satır başında `(venv)` görürsün. "Script çalıştırma izni yok"
hatası alırsan önce şunu çalıştır, sonra tekrar dene:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Sanal ortam daha önce kurulmadıysa (`venv` klasörü yoksa):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

## 2) Scraper'ları çalıştır

Her scraper bağımsız bir script'tir, direkt `python <dosya>` ile çalışır.
Sonuçlar hem konsola yazdırılır hem de `data/` klasörü altına JSON+CSV
olarak kaydedilir.

### 01 — requests + BeautifulSoup (statik HTML)

```powershell
python 01_requests_beautifulsoup\wikipedia_scraper.py    # Türkiye'nin 81 ili — nüfus, bölge, yüzölçümü
python 01_requests_beautifulsoup\quotes_scraper.py        # Vikisöz — Türk yazar alıntıları
python 01_requests_beautifulsoup\books_scraper.py          # Türk romanları (Vikipedi)
```

### 02 — Selenium (tarayıcı otomasyonu)

```powershell
python 02_selenium\dynamic_page_scraper.py       # Vikipedi canlı arama otomatik-tamamlama
python 02_selenium\infinite_scroll_scraper.py    # Sonsuz kaydırma demosu (quotes.toscrape.com)
```

### 03 — Playwright (modern tarayıcı otomasyonu)

```powershell
python 03_playwright\spa_scraper.py            # Aynı canlı arama, DOM'dan kazıma
python 03_playwright\network_intercept.py      # Aynı arama, ağ trafiğini yakalayarak
```

### 04 — Scrapy (framework — farklı çalışır, bkz. aşağı)

### 05 — API Reverse Engineering

```powershell
python 05_api_reverse_engineering\hacker_news_api.py     # Wikimedia Pageviews + Özet API
python 05_api_reverse_engineering\hidden_api_scraper.py  # Vikipedi arama REST API keşfi
```

### 06 — İleri Düzey

```powershell
python 06_advanced\async_scraper.py       # Senkron (requests) vs asenkron (curl_cffi) hız karşılaştırması
python 06_advanced\anti_bot_bypass.py     # TLS parmak izi (JA3) farkındalık testi
```

## 3) Scrapy farklı çalışır — spider adıyla çağrılır

```powershell
cd 04_scrapy_project
scrapy crawl books
cd ..
```

Tüm siteyi taramadan hızlı test etmek istersen (ilk 20 öğede dursun):

```powershell
cd 04_scrapy_project
scrapy crawl books -s CLOSESPIDER_ITEMCOUNT=20
cd ..
```

## 4) Çıktıları görüntüle

```powershell
dir data\01_wikipedia
type data\01_wikipedia\turkiye_illeri.json
```

veya Dosya Gezgini'nden `data\` klasörüne bak. Her scraper kendi alt
klasörüne kaydeder:

| Klasör | İçerik |
|---|---|
| `data/01_wikipedia/` | Türkiye illeri |
| `data/01_vikisoz/` | Yazar alıntıları + yazar bilgileri |
| `data/01_romanlar/` | Türk romanları (requests+BS4) |
| `data/04_scrapy/` | Türk romanları (Scrapy, kategori taraması dahil) |
| `data/05_api_reverse/` | Pageviews + arama API sonuçları |
| `data/06_advanced/` | Async roman verisi + TLS karşılaştırması |
| `data/selenium/` | Selenium çıktıları |
| `data/playwright/` | Playwright çıktıları |
| `data/screenshots/` | Selenium/Playwright ekran görüntüleri |
| `data/logs/` | Her scraper'ın log dosyası |

## 5) Bitirince sanal ortamdan çık

```powershell
deactivate
```

## Notlar

- Selenium ve Playwright scriptleri arka planda (headless) bir Chrome
  tarayıcısı açar — ekranda bir şey görünmez, bu normaldir. Biraz daha
  uzun sürerler (10-90 saniye).
- Bazı scraper'lar internet bağlantısı gerektirir ve gerçek sitelere
  (tr.wikipedia.org, tr.wikiquote.org vb.) istek atar; nadiren rate-limit
  veya geçici ağ hatası görülebilir, script bunları loglayıp devam eder.
- `venv/` klasörü Git'e gönderilmez (`.gitignore`'da hariç tutuldu).
