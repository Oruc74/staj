"""
Dinamik Sayfa Scraper - Selenium ile Vikipedi Canlı Arama
=============================================================
Hedef Site : https://tr.wikipedia.org/wiki/Anasayfa
Yöntem     : Selenium WebDriver (Chrome headless) + explicit waits
Açıklama   : Vikipedi'nin arama kutusuna gerçek bir kullanıcı gibi
             yazarak (send_keys), arka planda JavaScript ile tetiklenen
             ve AJAX ile gelen "otomatik tamamlama" (typeahead) öneri
             listesini kazır. Bu öneriler sunucudan tarayıcı JS'i
             tarafından dinamik olarak yüklenir — sayfanın ilk HTML'inde
             yoktur, bu yüzden Selenium/tarayıcı otomasyonu gerektirir
             (düz requests+BeautifulSoup ile görülemez).
"""

import sys
import os
import time

# ---------- Proje yardımcı modülünü içe aktar ----------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, random_delay, save_to_json,
    save_to_csv, print_summary, clean_text, ensure_dir
)

# ---------- Selenium bağımlılıkları ----------
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

from colorama import Fore, Style, init

init(autoreset=True)

# ---------- Sabitler ----------
BASE_URL = "https://tr.wikipedia.org/wiki/Anasayfa"
SCRAPER_NAME = "DynamicSearchScraper"

# Denenecek arama terimleri
ARAMA_TERIMLERI = [
    "İstanbul", "Atatürk", "Türk edebiyatı", "Kapadokya", "Orhan Pamuk",
]

# Ekran görüntülerinin kaydedileceği klasör
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'screenshots')

# Logger kur
logger = setup_logger(SCRAPER_NAME)


# ============================================================
# DRIVER OLUŞTURMA
# ============================================================

def create_driver() -> webdriver.Chrome:
    """
    Chrome tarayıcısını headless modda yapılandırır ve döndürür.
    selenium >=4.6 sürümüyle birlikte gelen dahili driver
    yöneticisini kullanır; yoksa webdriver-manager'a düşer.

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
    chrome_options.add_argument("--lang=tr-TR")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    try:
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
# EKRAN GÖRÜNTÜSÜ ALMA
# ============================================================

def take_screenshot(driver: webdriver.Chrome, name: str) -> str:
    """Mevcut sayfanın ekran görüntüsünü kaydeder."""
    ensure_dir(SCREENSHOT_DIR)
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        driver.save_screenshot(filepath)
        logger.info(f"{Fore.CYAN}📸 Ekran görüntüsü kaydedildi: {filepath}")
    except Exception as e:
        logger.warning(f"{Fore.YELLOW}Ekran görüntüsü alınamadı: {e}")
        filepath = ""
    return filepath


# ============================================================
# CANLI ARAMA ÖNERİLERİNİ ÇEKME
# ============================================================

def arama_onerilerini_cek(driver: webdriver.Chrome, terim: str) -> list[dict]:
    """
    Arama sayfasını taze açar, arama kutusuna bir terim yazar,
    JavaScript ile gelen AJAX öneri dropdown'unun yüklenmesini bekler
    ve önerileri kazır.

    NOT: Vikipedi'nin arama widget'ı (Vue.js tabanlı), öneriler
    göründüğünde <input> elementini DOM'da yeniden oluşturuyor. Bu
    yüzden yazmadan önce alınan element referansı öneriler çıktıktan
    sonra kullanılırsa StaleElementReferenceException fırlatılıyor.
    Bunu önlemek için her terimde sayfa taze yükleniyor ve element
    referansı bir daha kullanılmıyor (tekrar aranmıyor).

    Args:
        driver: Aktif WebDriver örneği
        terim:  Arama kutusuna yazılacak terim

    Returns:
        {"arama_terimi", "baslik", "aciklama"} sözlüklerinden oluşan liste
    """
    oneriler: list[dict] = []

    try:
        driver.get(BASE_URL)
        arama_kutusu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchInput"))
        )
        arama_kutusu.click()
        # send_keys zaten karakter karakter tuş olayı üretir — JS'in
        # AJAX isteğini tetiklemesi için ekstra bir şey gerekmez
        arama_kutusu.send_keys(terim)

        # Öneri dropdown'unun (AJAX ile dolan) görünür olmasını bekle
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".cdx-menu-item")
            )
        )
        time.sleep(0.5)

        safe_name = "".join(c if c.isalnum() else "_" for c in terim).lower()
        take_screenshot(driver, f"arama_{safe_name}")

        oge_listesi = driver.find_elements(By.CSS_SELECTOR, ".cdx-menu-item")
        logger.info(f"  → '{terim}' için {len(oge_listesi)} öneri bulundu")

        for oge in oge_listesi:
            try:
                baslik_el = oge.find_element(
                    By.CSS_SELECTOR, ".cdx-menu-item__text__label"
                )
                baslik = clean_text(baslik_el.text)
            except NoSuchElementException:
                continue

            aciklama = ""
            try:
                aciklama_el = oge.find_element(
                    By.CSS_SELECTOR, ".cdx-menu-item__text__description"
                )
                aciklama = clean_text(aciklama_el.text)
            except NoSuchElementException:
                pass

            if baslik:
                oneriler.append({
                    "arama_terimi": terim,
                    "baslik": baslik,
                    "aciklama": aciklama,
                })

    except TimeoutException:
        logger.warning(f"{Fore.YELLOW}⏳ '{terim}' için öneri dropdown'u yüklenemedi{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}'{terim}' işlenirken hata: {e}")

    return oneriler


# ============================================================
# ANA İŞLEV
# ============================================================

def main() -> None:
    """
    Tüm arama terimleri için öneri listelerini çeker, JSON ve CSV
    olarak kaydeder ve özet istatistikleri yazdırır.
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"🔎 Dinamik Sayfa Scraper (Selenium) — Vikipedi Canlı Arama")
    print(f"   Hedef: {BASE_URL}")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    start_time = time.time()
    tum_oneriler: list[dict] = []
    errors = 0
    driver = None

    try:
        driver = create_driver()
        logger.info(f"{Fore.GREEN}🚀 Tarayıcı başlatıldı")

        for terim in ARAMA_TERIMLERI:
            logger.info(f"{Fore.CYAN}🔤 Aranıyor: '{terim}'")
            try:
                oneriler = arama_onerilerini_cek(driver, terim)
                tum_oneriler.extend(oneriler)
                random_delay(0.8, 1.5)
            except Exception as e:
                logger.error(f"{Fore.RED}❌ '{terim}' aramasında hata: {e}")
                errors += 1

    except WebDriverException as e:
        logger.error(f"{Fore.RED}WebDriver hatası: {e}")
        errors += 1
    except Exception as e:
        logger.error(f"{Fore.RED}Beklenmeyen hata: {e}")
        errors += 1
    finally:
        # driver.quit() bir tarayıcı çökmesinden sonra kendisi hata
        # fırlatabilir (ör. "tab crashed" sonrası bağlantı kopması).
        # Bunu yakalamazsak, o ana kadar toplanan tüm veriler hiç
        # kaydedilmeden script çöker.
        if driver:
            try:
                driver.quit()
                logger.info(f"{Fore.YELLOW}🔒 Tarayıcı kapatıldı")
            except Exception as e:
                logger.warning(f"{Fore.YELLOW}⚠️ Tarayıcı düzgün kapatılamadı: {e}")

    elapsed = time.time() - start_time

    if tum_oneriler:
        save_to_json(tum_oneriler, "selenium_arama_onerileri", subdir="selenium")
        save_to_csv(tum_oneriler, "selenium_arama_onerileri", subdir="selenium")

        print(f"\n{Fore.CYAN}📋 Örnek Öneriler (İlk 8):{Style.RESET_ALL}")
        print(f"{'─'*70}")
        for o in tum_oneriler[:8]:
            aciklama = o["aciklama"][:40] if o["aciklama"] else "(açıklama yok)"
            print(
                f"  {Fore.GREEN}[{o['arama_terimi']}]{Style.RESET_ALL} "
                f"{Fore.YELLOW}{o['baslik']:<25}{Style.RESET_ALL} — {aciklama}"
            )
    else:
        print(f"{Fore.RED}⚠️  Hiç öneri çekilemedi!{Style.RESET_ALL}")

    print_summary(
        scraper_name=SCRAPER_NAME,
        total_items=len(tum_oneriler),
        elapsed_time=elapsed,
        pages_scraped=len(ARAMA_TERIMLERI),
        errors=errors,
    )


if __name__ == "__main__":
    main()
