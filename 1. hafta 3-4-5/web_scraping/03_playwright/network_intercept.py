"""
Playwright Ağ Yakalama (Network Interception) Scraper — Vikipedi Arama
==========================================================================
Hedef Site: https://tr.wikipedia.org/wiki/Anasayfa
Yöntem: Playwright page.on('response') ile ağ trafiğini dinleme

Bu script, Playwright'ın ağ yakalama (network interception) özelliğini
kullanarak Vikipedi'nin arama kutusunu analiz eder. Arama kutusuna
yazıldıkça arka planda tetiklenen AJAX isteklerini yakalar ve JSON
verilerini doğrudan API yanıtlarından çıkarır — 03_playwright/
spa_scraper.py'nin aynı hedefi DOM'dan kazımasıyla karşılaştırma
yapılabilsin diye aynı arama terimleri kullanılır.

Bu yaklaşım, API tersine mühendisliğine (reverse engineering) bir
köprü oluşturur:
1. İlk adım: Ağ trafiğini dinleyerek hangi API endpoint'lerinin
   kullanıldığını keşfederiz (bu script bunu yapıyor).
2. İkinci adım: Bu endpoint'leri doğrudan çağırarak tarayıcıya
   ihtiyaç duymadan veri çekebiliriz (bkz.
   05_api_reverse_engineering/hidden_api_scraper.py — orada bu
   script'te keşfedilen /w/rest.php/v1/search/title endpoint'i
   doğrudan requests ile çağrılıyor).

Avantajları:
- JavaScript ile render edilen verilere erişim
- Sayfa DOM'unu parse etmeye gerek yok
- API endpoint'lerini otomatik keşfetme
- Ham JSON verisi — daha temiz ve yapılandırılmış
"""

import sys
import os
import time
import json
from datetime import datetime

# --- Proje utils modülünü import et ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, save_to_json, save_to_csv, print_summary,
    clean_text, random_delay
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

BASE_URL = "https://tr.wikipedia.org/wiki/Anasayfa"
HEADLESS_MODE = True

# spa_scraper.py ile aynı terimler — DOM vs API karşılaştırması için
ARAMA_TERIMLERI = [
    "İstanbul", "Atatürk", "Türk edebiyatı", "Kapadokya", "Orhan Pamuk",
]

logger = setup_logger("playwright_network_intercept")


class NetworkInterceptor:
    """
    Playwright ağ trafiğini dinleyip analiz eden sınıf.

    Sayfa yüklenirken ve arama kutusuna yazarken yapılan tüm ağ
    isteklerini yakalar, filtreler ve API yanıtlarını depolar.
    """

    def __init__(self):
        self.all_requests = []
        self.api_requests = []
        self.intercepted_data = []
        self.discovered_endpoints = set()
        self.request_count = 0
        self.ignored_resource_types = {
            "image", "stylesheet", "font", "media",
            "manifest", "other", "websocket",
        }

    def handle_response(self, response) -> None:
        """
        Playwright'ın her ağ yanıtı için çağırdığı callback fonksiyonu.
        page.on('response', handler) ile bağlanır.

        Args:
            response: Playwright response nesnesi
        """
        self.request_count += 1
        request = response.request

        request_info = {
            "url": response.url,
            "status": response.status,
            "method": request.method,
            "resource_type": request.resource_type,
            "timestamp": datetime.now().isoformat(),
        }
        self.all_requests.append(request_info)

        # Kaynak türüne göre filtrele — sadece XHR ve fetch isteklerini al
        # Bu, API reverse engineering'in ilk adımıdır:
        # Hangi endpoint'ler çağrılıyor? Hangi veriler dönüyor?
        if request.resource_type in ("xhr", "fetch"):
            logger.info(
                f"  🌐 API İsteği: {Fore.GREEN}{request.method}{Style.RESET_ALL} "
                f"{Fore.CYAN}{response.url}{Style.RESET_ALL} "
                f"[{response.status}]"
            )

            self.api_requests.append(request_info)
            self.discovered_endpoints.add(response.url.split("?")[0])
            self._extract_json_data(response)

        elif request.resource_type not in self.ignored_resource_types:
            logger.debug(
                f"  📄 {request.resource_type}: {response.url[:80]}... [{response.status}]"
            )

    def _extract_json_data(self, response) -> None:
        """
        API yanıtından JSON verisini çıkarır.

        Args:
            response: Playwright response nesnesi
        """
        try:
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type:
                return

            body = response.text()
            if not body:
                return

            json_data = json.loads(body)

            intercepted_item = {
                "endpoint": response.url,
                "method": response.request.method,
                "status": response.status,
                "response_data": json_data,
                "captured_at": datetime.now().isoformat(),
            }
            self.intercepted_data.append(intercepted_item)

            # Vikipedi arama API'sine özel: sonuçları çıkar
            if isinstance(json_data, dict) and "pages" in json_data:
                sonuc_sayisi = len(json_data["pages"])
                logger.info(
                    f"  📝 API'den {Fore.GREEN}{sonuc_sayisi}{Style.RESET_ALL} arama sonucu yakalandı"
                )

        except json.JSONDecodeError:
            logger.debug(f"  ⚠️ JSON parse edilemedi: {response.url[:60]}...")
        except Exception as e:
            logger.warning(f"  ⚠️ Veri çıkarma hatası: {e}")

    def get_all_results_from_api(self) -> list[dict]:
        """
        Yakalanan API yanıtlarından tüm arama sonuçlarını birleştirir.

        Returns:
            Arama sonuçlarının listesi
        """
        sonuclar = []
        for item in self.intercepted_data:
            data = item.get("response_data", {})
            if isinstance(data, dict) and "pages" in data:
                for sayfa in data["pages"]:
                    sonuclar.append({
                        "baslik": clean_text(sayfa.get("title", "")),
                        "aciklama": clean_text(sayfa.get("description") or ""),
                        "kaynak": "API Interception",
                    })
        return sonuclar

    def print_network_summary(self) -> None:
        """Ağ trafiği özetini yazdırır."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌐 AĞ TRAFİĞİ ÖZETİ{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"  {'📊 Toplam İstek:':<30} {Fore.GREEN}{self.request_count}{Style.RESET_ALL}")
        print(f"  {'🔌 API İsteği (XHR/Fetch):':<30} {Fore.GREEN}{len(self.api_requests)}{Style.RESET_ALL}")
        print(f"  {'📡 Keşfedilen Endpoint:':<30} {Fore.GREEN}{len(self.discovered_endpoints)}{Style.RESET_ALL}")
        print(f"  {'📦 JSON Yanıt:':<30} {Fore.GREEN}{len(self.intercepted_data)}{Style.RESET_ALL}")

        resource_types = {}
        for req in self.all_requests:
            rt = req["resource_type"]
            resource_types[rt] = resource_types.get(rt, 0) + 1

        print(f"\n  {Fore.YELLOW}📂 Kaynak Türü Dağılımı:{Style.RESET_ALL}")
        for rt, count in sorted(resource_types.items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 30)
            icon = "🔌" if rt in ("xhr", "fetch") else "📄"
            print(f"    {icon} {rt:<15} {count:>4}  {Fore.BLUE}{bar}{Style.RESET_ALL}")

        if self.discovered_endpoints:
            print(f"\n  {Fore.YELLOW}🔗 Keşfedilen API Endpoint'leri:{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}   (Bu endpoint'ler doğrudan requests ile çağrılabilir!){Style.RESET_ALL}")
            for i, endpoint in enumerate(sorted(self.discovered_endpoints), 1):
                print(f"    {i}. {Fore.GREEN}{endpoint}{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def scrape_dropdown_dom(page) -> list[dict]:
    """
    Arama öneri dropdown'undaki sonuçları DOM'dan geleneksel yöntemle
    toplar (karşılaştırma için — bkz. spa_scraper.py).

    Args:
        page: Playwright sayfa nesnesi

    Returns:
        Öneri sonuçlarının listesi
    """
    sonuclar = []
    ogeler = page.locator(".cdx-menu-item").all()

    for oge in ogeler:
        try:
            baslik_el = oge.locator(".cdx-menu-item__text__label")
            if baslik_el.count() == 0:
                continue
            baslik = clean_text(baslik_el.inner_text())

            aciklama = ""
            aciklama_el = oge.locator(".cdx-menu-item__text__description")
            if aciklama_el.count() > 0:
                aciklama = clean_text(aciklama_el.inner_text())

            sonuclar.append({
                "baslik": baslik,
                "aciklama": aciklama,
                "kaynak": "DOM Parsing",
            })
        except Exception as e:
            logger.warning(f"  ⚠️ DOM parse hatası: {e}")

    return sonuclar


def aramalari_calistir(page, terimler: list[str]) -> list[dict]:
    """
    Her arama terimi için sayfayı taze yükler, terimi yazar ve
    dropdown'un DOM'dan sonuçlarını toplar. Ağ dinleyicisi zaten
    page.on('response', ...) ile bağlı olduğundan, bu sırada
    tetiklenen API istekleri otomatik olarak yakalanır.

    Args:
        page: Playwright sayfa nesnesi
        terimler: Denenecek arama terimlerinin listesi

    Returns:
        DOM'dan toplanan tüm sonuçların listesi
    """
    tum_dom_sonuclari = []

    for terim in terimler:
        logger.info(f"\n🔤 Aranıyor: '{terim}'")
        try:
            # Aynı sayfada art arda arama, Vikipedi'nin Vue.js tabanlı
            # widget'ını kararsız hale getirebiliyor (bkz. spa_scraper.py'daki not)
            page.goto(BASE_URL, wait_until="domcontentloaded")

            arama_kutusu = page.locator("#searchInput")
            arama_kutusu.click()
            arama_kutusu.type(terim, delay=60)

            page.locator(".cdx-menu-item").first.wait_for(
                state="visible", timeout=10000
            )
            page.wait_for_timeout(400)

            dom_sonuclari = scrape_dropdown_dom(page)
            for s in dom_sonuclari:
                s["arama_terimi"] = terim
            tum_dom_sonuclari.extend(dom_sonuclari)
            logger.info(f"  DOM'dan {len(dom_sonuclari)} sonuç toplandı")

            random_delay(0.3, 0.7)

        except PlaywrightTimeout:
            logger.warning(f"⏳ '{terim}' için dropdown yüklenemedi")
        except Exception as e:
            logger.error(f"❌ '{terim}' işlenirken hata: {e}")

    return tum_dom_sonuclari


def run_network_intercept_scraper():
    """
    Ana scraper fonksiyonu.
    Ağ trafiğini dinleyerek ve DOM'u parse ederek veri toplar,
    sonuçları karşılaştırır.
    """
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🌐 Playwright Ağ Yakalama — Vikipedi Arama{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"  Hedef: {Fore.YELLOW}{BASE_URL}{Style.RESET_ALL}")
    print(f"  Mod  : {Fore.YELLOW}{'Headless' if HEADLESS_MODE else 'Headed'}{Style.RESET_ALL}")
    print()

    start_time = time.time()
    interceptor = NetworkInterceptor()
    errors = 0
    dom_sonuclari = []

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

        # ── Ağ dinleyicisini bağla ──
        # Bu, tüm ağ trafiğini yakalamamızı sağlar — DevTools Network
        # sekmesini programatik olarak izlemek gibidir.
        page.on("response", interceptor.handle_response)
        logger.info("🔌 Ağ dinleyicisi bağlandı — tüm trafik izleniyor")

        try:
            dom_sonuclari = aramalari_calistir(page, ARAMA_TERIMLERI)
        except Exception as e:
            logger.error(f"❌ Beklenmeyen hata: {e}")
            errors += 1
        finally:
            try:
                context.close()
                browser.close()
                logger.info("🔒 Tarayıcı kapatıldı")
            except Exception as e:
                logger.warning(f"⚠️ Tarayıcı düzgün kapatılamadı: {e}")

    elapsed_time = time.time() - start_time

    interceptor.print_network_summary()

    api_sonuclari = interceptor.get_all_results_from_api()
    logger.info(f"🔌 API'den toplam {len(api_sonuclari)} sonuç yakalandı")

    # ── Karşılaştırma: API vs DOM ──
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔄 VERİ KARŞILAŞTIRMASI: API Interception vs DOM Parsing{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"  {'📡 API Interception ile:':<35} {Fore.GREEN}{len(api_sonuclari)}{Style.RESET_ALL} sonuç")
    print(f"  {'📄 DOM Parsing ile:':<35} {Fore.GREEN}{len(dom_sonuclari)}{Style.RESET_ALL} sonuç")

    if api_sonuclari and dom_sonuclari:
        api_basliklar = {s["baslik"] for s in api_sonuclari if s["baslik"]}
        dom_basliklar = {s["baslik"] for s in dom_sonuclari if s["baslik"]}
        ortak = api_basliklar & dom_basliklar
        print(f"  {'👥 Ortak Başlıklar:':<35} {Fore.GREEN}{len(ortak)}{Style.RESET_ALL}")
        print(f"\n  {Fore.YELLOW}💡 Her iki yöntem de aynı veriye ulaştı!{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}   API Interception, DOM parsing'e göre daha temiz ve hızlı veri sağlar.{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}   Keşfedilen endpoint'ler doğrudan requests ile çağrılabilir.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

    if api_sonuclari:
        save_to_json(api_sonuclari, "network_intercept_api_sonuclari", subdir="playwright")
        save_to_csv(api_sonuclari, "network_intercept_api_sonuclari", subdir="playwright")

    if dom_sonuclari:
        save_to_json(dom_sonuclari, "network_intercept_dom_sonuclari", subdir="playwright")
        save_to_csv(dom_sonuclari, "network_intercept_dom_sonuclari", subdir="playwright")

    if interceptor.discovered_endpoints:
        endpoint_data = [
            {
                "endpoint": ep,
                "type": "XHR/Fetch",
                "note": "Bu endpoint doğrudan requests kütüphanesiyle çağrılabilir",
            }
            for ep in sorted(interceptor.discovered_endpoints)
        ]
        save_to_json(endpoint_data, "discovered_api_endpoints", subdir="playwright")

    if interceptor.api_requests:
        save_to_json(interceptor.api_requests, "api_request_log", subdir="playwright")

    display_sonuclari = api_sonuclari if api_sonuclari else dom_sonuclari
    if display_sonuclari:
        print(f"\n{Fore.CYAN}📋 İlk 5 Sonuç (Önizleme):{Style.RESET_ALL}")
        print(f"{'─'*70}")
        for i, s in enumerate(display_sonuclari[:5], 1):
            aciklama = s["aciklama"][:50] if s["aciklama"] else "(açıklama yok)"
            print(
                f"  {i}. {Fore.GREEN}{s['baslik']}{Style.RESET_ALL} "
                f"— {aciklama} | Kaynak: {s['kaynak']}"
            )

    total = len(api_sonuclari) + len(dom_sonuclari)
    print_summary(
        scraper_name="Playwright Network Intercept — Vikipedi Arama",
        total_items=total,
        elapsed_time=elapsed_time,
        pages_scraped=len(ARAMA_TERIMLERI),
        errors=errors,
    )

    if interceptor.discovered_endpoints:
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}🔧 API REVERSE ENGINEERING REHBERİ{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"  Yukarıda keşfedilen API endpoint'leri doğrudan")
        print(f"  Python requests kütüphanesiyle çağrılabilir:")
        print()
        print(f"  {Fore.GREEN}import requests{Style.RESET_ALL}")
        for ep in sorted(interceptor.discovered_endpoints):
            print(f"  {Fore.GREEN}response = requests.get(\"{ep}\", params={{'q': 'İstanbul'}}){Style.RESET_ALL}")
            print(f"  {Fore.GREEN}data = response.json(){Style.RESET_ALL}")
        print()
        print(f"  {Fore.YELLOW}Bu sayede tarayıcıya ihtiyaç duymadan,{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}çok daha hızlı veri çekebilirsiniz!{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")


# ============================================================
# ANA GİRİŞ NOKTASI
# ============================================================
if __name__ == "__main__":
    print(f"{Fore.MAGENTA}🌐 Playwright Network Intercept Scraper başlatılıyor...{Style.RESET_ALL}")
    print()

    try:
        run_network_intercept_scraper()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Kullanıcı tarafından durduruldu.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Kritik hata: {e}{Style.RESET_ALL}")
        logger.exception("Kritik hata oluştu")
