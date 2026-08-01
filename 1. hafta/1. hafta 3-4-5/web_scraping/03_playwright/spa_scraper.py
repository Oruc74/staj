"""
Playwright ile Vikipedi Canlı Arama Scraper
==============================================
Hedef Site: https://tr.wikipedia.org/wiki/Anasayfa
Yöntem: Playwright sync_api ile tarayıcı otomasyonu

Bu script, Vikipedi'nin arama kutusuna yazarken JavaScript ile
tetiklenen AJAX "otomatik tamamlama" (typeahead) öneri dropdown'unu
kazır. 02_selenium/dynamic_page_scraper.py ile aynı hedefi ve aynı
öneri listesini kullanır — iki farklı otomasyon aracının aynı dinamik
içerikle nasıl başa çıktığını karşılaştırmak için.

Playwright vs Selenium Karşılaştırması (bu script özelinde):
================================================================
1. AUTO-WAITING (Otomatik Bekleme):
   - Selenium: WebDriverWait + expected_conditions gerektirir
   - Playwright: locator.click()/type() otomatik olarak elementin
     hazır olmasını bekler

2. STALE ELEMENT SORUNU YOK:
   - Selenium: Vikipedi'nin arama widget'ı (Vue.js) öneriler
     göründüğünde <input> elementini DOM'da yeniden oluşturuyor;
     önceden alınmış bir WebElement referansı bu noktadan sonra
     StaleElementReferenceException fırlatıyor (bu projede
     02_selenium/dynamic_page_scraper.py yazılırken gerçekten
     karşılaşılan bir hataydı).
   - Playwright: page.locator(...) bir "canlı sorgu" tanımıdır,
     önbelleğe alınmış bir element referansı değildir — her
     action'da DOM'da yeniden aranır. Bu yüzden DOM'un JS
     tarafından yeniden oluşturulması Playwright'ı etkilemez.

3. API BASİTLİĞİ:
   - Selenium: find_element(By.CSS_SELECTOR, ...) + explicit wait
   - Playwright: page.locator() - daha az kod, zincirleme API

4. TARAYICI DESTEĞİ:
   - Selenium: Ayrı driver indirmek gerekir (chromedriver vs.)
   - Playwright: `playwright install` komutu ile tüm tarayıcılar hazır
"""

import sys
import os
import time
from datetime import datetime

# --- Proje utils modülünü import et ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, save_to_json, save_to_csv, print_summary,
    clean_text, ensure_dir, random_delay
)

from colorama import Fore, Style, init

init(autoreset=True)

# Playwright import
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(f"{Fore.RED}❌ Playwright yüklü değil!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Yüklemek için: pip install playwright && playwright install{Style.RESET_ALL}")
    sys.exit(1)

# ============================================================
# KONFİGÜRASYON
# ============================================================

HEADLESS_MODE = True

BASE_URL = "https://tr.wikipedia.org/wiki/Anasayfa"

# Denenecek arama terimleri (02_selenium ile aynı liste — karşılaştırma için)
ARAMA_TERIMLERI = [
    "İstanbul", "Atatürk", "Türk edebiyatı", "Kapadokya", "Orhan Pamuk",
]

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'screenshots')

logger = setup_logger("playwright_arama_scraper")


def take_screenshot(page, name: str) -> str:
    """Sayfanın ekran görüntüsünü alır ve kaydeder."""
    ensure_dir(SCREENSHOT_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}_{timestamp}.png")
    page.screenshot(path=filepath)
    logger.info(f"📸 Ekran görüntüsü kaydedildi: {filepath}")
    return filepath


def arama_onerilerini_cek(page, terim: str) -> list[dict]:
    """
    Arama kutusuna bir terim yazar, AJAX öneri dropdown'unun
    yüklenmesini bekler (Playwright otomatik bekler) ve önerileri
    kazır.

    Args:
        page: Playwright sayfa nesnesi
        terim: Arama kutusuna yazılacak terim

    Returns:
        {"arama_terimi", "baslik", "aciklama"} sözlüklerinden oluşan liste
    """
    oneriler = []

    try:
        # Aynı sayfada art arda arama yapmak, Vikipedi'nin Vue.js tabanlı
        # arama widget'ını kararsız hale getirebiliyor (bazı terimlerde
        # dropdown hiç açılmıyor). Selenium sürümünde de aynı sorun
        # yaşandı ve orada da aynı çözüm kullanıldı: her terimde sayfayı
        # taze yükle.
        page.goto(BASE_URL, wait_until="domcontentloaded")

        arama_kutusu = page.locator("#searchInput")
        arama_kutusu.click()
        # .type() her karakteri ayrı ayrı yazar — gerçek kullanıcı
        # yazması gibi JS'in AJAX isteğini tetiklemesini sağlar
        arama_kutusu.type(terim, delay=60)

        # Playwright auto-waiting: öneri öğesi DOM'a eklenip görünür
        # olana kadar bekler — Selenium'daki gibi ayrı bir
        # WebDriverWait/expected_conditions yazmaya gerek yok
        page.locator(".cdx-menu-item").first.wait_for(
            state="visible", timeout=10000
        )
        page.wait_for_timeout(400)

        safe_name = "".join(c if c.isalnum() else "_" for c in terim).lower()
        take_screenshot(page, f"arama_{safe_name}")

        oge_listesi = page.locator(".cdx-menu-item").all()
        logger.info(f"  → '{terim}' için {len(oge_listesi)} öneri bulundu")

        for oge in oge_listesi:
            baslik_el = oge.locator(".cdx-menu-item__text__label")
            if baslik_el.count() == 0:
                continue
            baslik = clean_text(baslik_el.inner_text())

            aciklama = ""
            aciklama_el = oge.locator(".cdx-menu-item__text__description")
            if aciklama_el.count() > 0:
                aciklama = clean_text(aciklama_el.inner_text())

            if baslik:
                oneriler.append({
                    "arama_terimi": terim,
                    "baslik": baslik,
                    "aciklama": aciklama,
                })

    except PlaywrightTimeout:
        logger.warning(f"{Fore.YELLOW}⏳ '{terim}' için öneri dropdown'u yüklenemedi{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}'{terim}' işlenirken hata: {e}")

    return oneriler


def run_scraper():
    """Ana scraper fonksiyonu. Playwright'ı başlatır ve tüm terimleri dener."""
    tum_oneriler = []
    errors = 0

    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🎭 Playwright — Vikipedi Canlı Arama Scraper{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"  Hedef: {Fore.YELLOW}{BASE_URL}{Style.RESET_ALL}")
    print(f"  Mod  : {Fore.YELLOW}{'Headless' if HEADLESS_MODE else 'Headed (Görünür)'}{Style.RESET_ALL}")
    print()

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_MODE)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            for terim in ARAMA_TERIMLERI:
                logger.info(f"🔤 Aranıyor: '{terim}'")
                try:
                    oneriler = arama_onerilerini_cek(page, terim)
                    tum_oneriler.extend(oneriler)
                    random_delay(0.5, 1.0)
                except Exception as e:
                    logger.error(f"❌ '{terim}' aramasında hata: {e}")
                    errors += 1

        except PlaywrightTimeout:
            logger.error("❌ Ana sayfa yüklenirken zaman aşımı!")
            errors += 1
        except Exception as e:
            logger.error(f"❌ Beklenmeyen hata: {e}")
            errors += 1
        finally:
            # Bir tarayıcı sekmesi çökmesinden sonra context/browser.close()
            # de hata fırlatabilir; yakalamazsak o ana kadar toplanan tüm
            # veriler hiç kaydedilmeden script çöker.
            try:
                context.close()
                browser.close()
                logger.info("🔒 Tarayıcı kapatıldı")
            except Exception as e:
                logger.warning(f"⚠️ Tarayıcı düzgün kapatılamadı: {e}")

    elapsed_time = time.time() - start_time

    if tum_oneriler:
        save_to_json(tum_oneriler, "playwright_arama_onerileri", subdir="playwright")
        save_to_csv(tum_oneriler, "playwright_arama_onerileri", subdir="playwright")

        print(f"\n{Fore.CYAN}📋 Örnek Öneriler (İlk 8):{Style.RESET_ALL}")
        print(f"{'─'*70}")
        for o in tum_oneriler[:8]:
            aciklama = o["aciklama"][:40] if o["aciklama"] else "(açıklama yok)"
            print(
                f"  {Fore.GREEN}[{o['arama_terimi']}]{Style.RESET_ALL} "
                f"{Fore.YELLOW}{o['baslik']:<25}{Style.RESET_ALL} — {aciklama}"
            )

        print_summary(
            scraper_name="Playwright — Vikipedi Canlı Arama",
            total_items=len(tum_oneriler),
            elapsed_time=elapsed_time,
            pages_scraped=len(ARAMA_TERIMLERI),
            errors=errors,
        )
    else:
        print(f"\n{Fore.RED}❌ Hiç öneri çekilemedi!{Style.RESET_ALL}")
        print_summary(
            scraper_name="Playwright — Vikipedi Canlı Arama",
            total_items=0,
            elapsed_time=elapsed_time,
            pages_scraped=len(ARAMA_TERIMLERI),
            errors=errors,
        )


if __name__ == "__main__":
    print(f"{Fore.MAGENTA}🎭 Playwright arama scraper başlatılıyor...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}   Mod: {'HEADLESS' if HEADLESS_MODE else 'HEADED'}{Style.RESET_ALL}")
    print()

    try:
        run_scraper()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Kullanıcı tarafından durduruldu.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Kritik hata: {e}{Style.RESET_ALL}")
        logger.exception("Kritik hata oluştu")
