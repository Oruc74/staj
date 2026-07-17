"""
Sonsuz Kaydırma (Infinite Scroll) Scraper - Selenium
=====================================================
Hedef Site : https://quotes.toscrape.com/scroll
Yöntem     : Selenium WebDriver (Chrome headless) + JavaScript scroll
Açıklama   : Sayfa sonuna kaydırarak dinamik olarak yüklenen alıntıları çeker.
             Yeni içerik gelmediğinde (sayfa yüksekliği değişmediğinde)
             kaydırmayı durdurur. Sonuçlar BS4 versiyonuyla karşılaştırılır.

NOT (BS4 Karşılaştırması):
    - BS4 ile sadece ilk sayfadaki statik HTML çekilebilir → ~0 alıntı
      (çünkü /scroll sayfası JavaScript ile içerik yükler).
    - Selenium ile sonsuz kaydırma yaparak TÜM alıntılar (~100 adet)
      başarıyla çekilebilir.
    - Sayfalama versiyonu (quotes.toscrape.com) BS4 ile 100 alıntı çeker
      ancak 10 ayrı sayfa isteği gerektirir.

NOT (Neden bu dosya İngilizce site hedefliyor):
    Bu projedeki diğer scraper'ların çoğu Türkçe kaynaklara (Vikipedi,
    Vikisöz) çevrildi. Bu dosya istisna — quotes.toscrape.com/scroll,
    scraping öğrenmek için özel olarak hazırlanmış, robots.txt kısıtlaması
    olmayan bir "sonsuz kaydırma" test sandbox'ıdır. Güvenli, engelsiz ve
    gerçek bir Türkçe "sonsuz kaydırma" pratik sitesi bulunamadığından
    (Vikipedi masaüstü arayüzünde infinite scroll yok), bu teknik gösterim
    için orijinal hedefte bırakıldı.
"""

import sys
import os
import time

# ---------- Proje yardımcı modülünü içe aktar ----------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, save_to_json, save_to_csv,
    print_summary, clean_text, ensure_dir
)

# ---------- Selenium bağımlılıkları ----------
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, StaleElementReferenceException
)

from colorama import Fore, Style, init

init(autoreset=True)

# ---------- Sabitler ----------
TARGET_URL = "https://quotes.toscrape.com/scroll"
SCRAPER_NAME = "InfiniteScrollScraper"

# Kaydırma sonrası yeni içeriği beklemek için maks süre (saniye)
SCROLL_WAIT_TIMEOUT = 5
# Aynı yükseklik kaç kere üst üste gelirse dur
MAX_SAME_HEIGHT_COUNT = 3

# Logger kur
logger = setup_logger(SCRAPER_NAME)


# ============================================================
# DRIVER OLUŞTURMA
# ============================================================

def create_driver() -> webdriver.Chrome:
    """
    Chrome tarayıcısını headless modda yapılandırır ve döndürür.
    Selenium >=4.6 dahili driver yöneticisini kullanır;
    başarısız olursa webdriver-manager'a geri düşer.

    Returns:
        Yapılandırılmış Chrome WebDriver örneği
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    try:
        # Selenium 4.6+ dahili driver yöneticisi
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        logger.info(f"{Fore.GREEN}Chrome WebDriver başarıyla oluşturuldu (dahili yönetici)")
    except WebDriverException:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options,
            )
            logger.info(f"{Fore.GREEN}Chrome WebDriver başarıyla oluşturuldu (webdriver-manager)")
        except Exception as e:
            logger.error(f"{Fore.RED}WebDriver oluşturulamadı: {e}")
            raise

    driver.implicitly_wait(5)
    return driver


# ============================================================
# KAYDIRMA VE İÇERİK TESPİTİ
# ============================================================

def get_page_height(driver: webdriver.Chrome) -> int:
    """
    Sayfanın toplam yüksekliğini JavaScript ile döndürür.

    Args:
        driver: Aktif WebDriver örneği

    Returns:
        Sayfa yüksekliği (piksel)
    """
    return driver.execute_script("return document.body.scrollHeight")


def scroll_to_bottom(driver: webdriver.Chrome) -> None:
    """
    Sayfanın en altına JavaScript ile kaydırır.

    Args:
        driver: Aktif WebDriver örneği
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")


def wait_for_new_content(driver: webdriver.Chrome,
                         old_height: int,
                         timeout: int = SCROLL_WAIT_TIMEOUT) -> bool:
    """
    Kaydırma sonrası yeni içeriğin yüklenmesini bekler.
    Sayfa yüksekliğinin değişip değişmediğini kontrol eder.

    Args:
        driver:     Aktif WebDriver örneği
        old_height: Kaydırma öncesi sayfa yüksekliği
        timeout:    Maksimum bekleme süresi (saniye)

    Returns:
        True → yeni içerik yüklendi, False → değişiklik yok
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.body.scrollHeight") > old_height
        )
        return True
    except TimeoutException:
        return False


def scroll_and_collect(driver: webdriver.Chrome) -> int:
    """
    Sonsuz kaydırma ile tüm içeriği yükler.
    Her kaydırmada sayfa yüksekliğini karşılaştırır;
    ardışık MAX_SAME_HEIGHT_COUNT kez aynı yükseklik ölçülürse durur.

    Args:
        driver: Aktif WebDriver örneği

    Returns:
        Toplam yapılan kaydırma sayısı
    """
    scroll_count = 0
    same_height_streak = 0

    logger.info(f"{Fore.CYAN}⬇️  Sonsuz kaydırma başlıyor...")

    while same_height_streak < MAX_SAME_HEIGHT_COUNT:
        old_height = get_page_height(driver)

        # Sayfanın en altına kaydır
        scroll_to_bottom(driver)
        scroll_count += 1

        # Yeni içeriğin yüklenmesini bekle
        content_loaded = wait_for_new_content(driver, old_height)

        if content_loaded:
            new_height = get_page_height(driver)
            same_height_streak = 0
            # Şu anki alıntı sayısını raporla
            current_quotes = len(
                driver.find_elements(By.CSS_SELECTOR, "div.quote")
            )
            logger.info(
                f"  📜 Kaydırma #{scroll_count}: yükseklik {old_height}→{new_height} | "
                f"Alıntı sayısı: {current_quotes}"
            )
        else:
            same_height_streak += 1
            logger.info(
                f"  ⏸️  Kaydırma #{scroll_count}: yeni içerik yok "
                f"(ardışık {same_height_streak}/{MAX_SAME_HEIGHT_COUNT})"
            )

    logger.info(
        f"{Fore.GREEN}✅ Kaydırma tamamlandı — toplam {scroll_count} kaydırma yapıldı"
    )
    return scroll_count


# ============================================================
# ALINTILARI AYRIŞTIRMA
# ============================================================

def parse_quotes(driver: webdriver.Chrome) -> list[dict]:
    """
    Sayfadaki tüm alıntı kartlarını ayrıştırır.

    Args:
        driver: Aktif WebDriver örneği

    Returns:
        Alıntı sözlüklerinin listesi
    """
    quotes: list[dict] = []

    cards = driver.find_elements(By.CSS_SELECTOR, "div.quote")
    logger.info(f"{Fore.CYAN}📖 {len(cards)} alıntı kartı bulundu, ayrıştırılıyor...")

    for idx, card in enumerate(cards, start=1):
        try:
            # Alıntı metni
            text_el = card.find_element(By.CSS_SELECTOR, "span.text")
            quote_text = clean_text(text_el.text)

            # Yazar
            author_el = card.find_element(By.CSS_SELECTOR, "small.author")
            author = clean_text(author_el.text)

            # Etiketler
            tag_els = card.find_elements(By.CSS_SELECTOR, "div.tags a.tag")
            tags = [clean_text(t.text) for t in tag_els]

            quote = {
                "sira":     idx,
                "alinti":   quote_text,
                "yazar":    author,
                "etiketler": ", ".join(tags),
            }
            quotes.append(quote)

        except StaleElementReferenceException:
            logger.warning(f"  {Fore.YELLOW}[{idx}] Kart referansı geçersiz, atlanıyor")
        except Exception as e:
            logger.warning(f"  {Fore.YELLOW}[{idx}] Ayrıştırma hatası: {e}")

    return quotes


# ============================================================
# ANA İŞLEV
# ============================================================

def main() -> None:
    """
    Sonsuz kaydırma ile tüm alıntıları çeker, JSON ve CSV olarak
    kaydeder ve BS4 versiyonuyla karşılaştırma notları yazdırır.
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"🌐 Sonsuz Kaydırma (Infinite Scroll) Scraper")
    print(f"   Hedef: {TARGET_URL}")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    start_time = time.time()
    all_quotes: list[dict] = []
    errors = 0
    scroll_count = 0
    driver = None

    try:
        # WebDriver oluştur
        driver = create_driver()
        logger.info(f"{Fore.GREEN}🚀 Tarayıcı başlatıldı")

        # Hedef sayfayı aç
        logger.info(f"{Fore.CYAN}📄 Sayfa açılıyor: {TARGET_URL}")
        driver.get(TARGET_URL)

        # İlk alıntıların yüklenmesini bekle (explicit wait)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.quote"))
        )
        logger.info(f"{Fore.GREEN}✅ Sayfa yüklendi, ilk alıntılar görünüyor")

        # Sonsuz kaydırma ile tüm içeriği yükle
        scroll_count = scroll_and_collect(driver)

        # Tüm alıntıları ayrıştır
        all_quotes = parse_quotes(driver)

        # İlk birkaç alıntıyı göster
        for q in all_quotes[:3]:
            logger.info(
                f"  {Fore.GREEN}📝 \"{q['alinti'][:60]}...\" — {q['yazar']}"
            )
        if len(all_quotes) > 3:
            logger.info(f"  ... ve {len(all_quotes) - 3} alıntı daha")

    except WebDriverException as e:
        logger.error(f"{Fore.RED}WebDriver hatası: {e}")
        errors += 1
    except Exception as e:
        logger.error(f"{Fore.RED}Beklenmeyen hata: {e}")
        errors += 1
    finally:
        if driver:
            driver.quit()
            logger.info(f"{Fore.YELLOW}🔒 Tarayıcı kapatıldı")

    elapsed = time.time() - start_time

    # ---------- Sonuçları kaydet ----------
    if all_quotes:
        save_to_json(all_quotes, "selenium_infinite_scroll_quotes", subdir="selenium")
        save_to_csv(all_quotes, "selenium_infinite_scroll_quotes", subdir="selenium")
    else:
        print(f"{Fore.RED}⚠️  Hiç alıntı çekilemedi!{Style.RESET_ALL}")

    # ---------- Özet yazdır ----------
    print_summary(
        scraper_name=SCRAPER_NAME,
        total_items=len(all_quotes),
        elapsed_time=elapsed,
        pages_scraped=scroll_count,
        errors=errors,
    )

    # ---------- BS4 Karşılaştırması ----------
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"📊 BS4 vs Selenium Karşılaştırması")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Selenium (Infinite Scroll):{Style.RESET_ALL}")
    print(f"    → Toplam {len(all_quotes)} alıntı çekildi")
    print(f"    → {scroll_count} kaydırma yapıldı")
    print(f"    → JavaScript render'ı destekler ✅")
    print()
    print(f"  {Fore.YELLOW}BeautifulSoup (BS4):{Style.RESET_ALL}")
    print(f"    → /scroll sayfasından ~0 alıntı çekilir (JS gerekli)")
    print(f"    → Sayfalama versiyonundan (/page/N) ~100 alıntı çekilir")
    print(f"    → JavaScript render'ı desteklemez ❌")
    print(f"    → Statik HTML için daha hızlı ve hafif 🚀")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
