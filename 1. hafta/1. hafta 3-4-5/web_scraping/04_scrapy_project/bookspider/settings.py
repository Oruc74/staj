# Scrapy settings for bookspider project
import os
import sys

# Windows konsolu varsayılan olarak cp1254/cp1252 gibi kod sayfaları kullanır,
# bu da Scrapy'nin Türkçe karakterli log satırlarını (İ, ı, ş, ğ vb.) bozuk
# gösterip UnicodeEncodeError riskine yol açar. Kaydedilen JSON/CSV dosyaları
# zaten UTF-8'dir (FEED_EXPORT_ENCODING); bu sadece terminal görünümünü düzeltir.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

BOT_NAME = "bookspider"

SPIDER_MODULES = ["bookspider.spiders"]
NEWSPIDER_MODULE = "bookspider.spiders"

# --- Kibar scraping ayarları ---
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 4

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

ITEM_PIPELINES = {
    "bookspider.pipelines.CleanTextPipeline": 300,
    "bookspider.pipelines.DropMissingTitlePipeline": 400,
    "bookspider.pipelines.DuplicatesPipeline": 500,
}

# Çıktıyı projenin ortak data/ klasörüne yaz (utils/helpers.py'nin
# diğer scraper'lar için kullandığı klasörle aynı yer).
_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "04_scrapy"
)
os.makedirs(_DATA_DIR, exist_ok=True)

FEEDS = {
    os.path.join(_DATA_DIR, "turk_romanlari.json"): {
        "format": "json",
        "encoding": "utf8",
        "overwrite": True,
    },
    os.path.join(_DATA_DIR, "turk_romanlari.csv"): {
        "format": "csv",
        "encoding": "utf-8-sig",
        "overwrite": True,
    },
}

LOG_LEVEL = "INFO"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
