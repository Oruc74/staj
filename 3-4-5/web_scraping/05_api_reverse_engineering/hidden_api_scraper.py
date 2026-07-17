"""
Gizli API Keşfi ile Vikipedi Arama Kazıyıcı (Hidden API Scraper)
====================================================================
Hedef Site  : https://tr.wikipedia.org
API Endpoint: https://tr.wikipedia.org/w/rest.php/v1/search/title?q={sorgu}
Yöntem      : API Reverse Engineering (Tersine Mühendislik)

Bu script, Vikipedi'nin arama kutusuna yazarken tetiklenen "otomatik
tamamlama" (typeahead) API'sini keşfedip doğrudan bu API'ye istek
atarak veri çekmeyi, aynı sonuçları klasik arama HTML sayfasını
(Özel:Ara) BeautifulSoup ile ayrıştırmakla karşılaştırır.

API Tersine Mühendislik Adımları (bu proje için gerçekten uygulandı):
=========================================================================
1. Tarayıcıda https://tr.wikipedia.org/wiki/Anasayfa aç
2. F12 veya Ctrl+Shift+I ile DevTools (Geliştirici Araçları) aç
3. "Network" (Ağ) sekmesine geç, filtreyi "Fetch/XHR" yap
4. Sayfanın üstündeki arama kutusuna bir şeyler yazmaya başla
   (ör. "İstanbul")
5. Network sekmesinde yeni istekler belirir:
   - https://tr.wikipedia.org/w/rest.php/v1/search/title?q=İst&limit=10
   - https://tr.wikipedia.org/w/rest.php/v1/search/title?q=İstanbul&limit=10
   Bu, arama kutusunun her tuş vuruşunda arka planda çağırdığı,
   sayfanın kendi JavaScript'inin kullandığı REST API'sidir.
6. İsteğe tıkla, Response sekmesinden JSON yapısını incele:
   {"pages": [{"title": ..., "description": ..., "excerpt": ...}, ...]}
7. Bu URL'yi doğrudan Python'dan da çağırabilirsin — tarayıcıya
   veya HTML parse etmeye gerek kalmaz.

Not: Bu, MediaWiki'nin resmi ve belgeli bir REST API'sidir (tamamen
"gizli"/belgelenmemiş değildir) — ancak keşif yöntemi (DevTools Network
sekmesinden bir sayfanın kendi JS'inin hangi endpoint'i çağırdığını
bulmak) belgesiz/iç API'ler için birebir aynı şekilde işler.

Avantajları:
- HTML parse etmeye gerek yok (BeautifulSoup gereksiz)
- Daha hızlı (sadece JSON verisi, HTML/CSS/JS yok)
- Daha güvenilir (HTML yapısı değişse bile API genelde aynı kalır)
- Daha az bant genişliği kullanır

Dezavantajları:
- Her site API sunmaz
- API endpoint'leri değişebilir
- Bazı API'ler kimlik doğrulama (auth token) gerektirir
- Rate limiting daha katı olabilir
"""

import sys
import os
import time
import requests

# Proje kök dizinini Python path'ine ekle (utils modülüne erişim için)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, random_delay, save_to_json, save_to_csv,
    print_summary, clean_text
)

from colorama import Fore, Style, init

# Colorama Windows uyumluluğu
init(autoreset=True)

# Logger kurulumu
logger = setup_logger("hidden_api_scraper")

# ============================================================
# SABİTLER
# ============================================================
# DevTools > Network sekmesinden keşfedilen arama API'si
SEARCH_API_URL = "https://tr.wikipedia.org/w/rest.php/v1/search/title"
# Klasik (JS'siz) arama sonucu HTML sayfası — BS4 karşılaştırması için
SEARCH_HTML_URL = "https://tr.wikipedia.org/w/index.php"

API_HEADERS = {"User-Agent": "staj-web-scraping-egitim/1.0"}

# Karşılaştırma için örnek arama sorguları
ARAMA_SORGULARI = [
    "İstanbul", "Atatürk", "Türk edebiyatı", "Yapay zeka",
    "Osmanlı İmparatorluğu", "Nazım Hikmet", "Boğaziçi Üniversitesi",
    "Kapadokya", "Orhan Pamuk", "Türk mutfağı", "İzmir", "Ankara",
]

SONUC_LIMIT = 5


def api_ile_arama(sorgu: str) -> list[dict]:
    """
    Vikipedi'nin arama-otomatik-tamamlama REST API'sine doğrudan
    istek atarak sonuçları çeker.

    API Yanıt Yapısı:
    {"pages": [{"title": ..., "description": ..., "excerpt": ...}, ...]}

    Args:
        sorgu: Arama terimi

    Returns:
        Sonuç sözlüklerinden oluşan liste
    """
    try:
        response = requests.get(
            SEARCH_API_URL,
            params={"q": sorgu, "limit": SONUC_LIMIT},
            headers=API_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        veri = response.json()

        return [
            {
                "sorgu": sorgu,
                "baslik": sayfa.get("title", ""),
                "aciklama": clean_text(sayfa.get("description") or ""),
                "yontem": "API",
            }
            for sayfa in veri.get("pages", [])
        ]
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ API araması başarısız ({sorgu}): {e}")
        return []


def bs4_ile_arama(sorgu: str) -> list[dict]:
    """
    Aynı arama sonuçlarını klasik HTML arama sayfasından
    (Özel:Ara) BeautifulSoup ile ayrıştırarak çeker.

    Args:
        sorgu: Arama terimi

    Returns:
        Sonuç sözlüklerinden oluşan liste
    """
    from bs4 import BeautifulSoup

    try:
        response = requests.get(
            SEARCH_HTML_URL,
            params={"search": sorgu, "title": "Özel:Ara", "fulltext": 1},
            headers=API_HEADERS,
            timeout=15,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        basliklar = soup.select(".mw-search-result-heading a")
        snippetler = soup.select(".searchresult")

        sonuclar = []
        for i, baslik_el in enumerate(basliklar[:SONUC_LIMIT]):
            snippet = clean_text(snippetler[i].get_text()) if i < len(snippetler) else ""
            sonuclar.append({
                "sorgu": sorgu,
                "baslik": clean_text(baslik_el.get_text()),
                "aciklama": snippet[:150],
                "yontem": "BS4",
            })
        return sonuclar
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ BS4 araması başarısız ({sorgu}): {e}")
        return []


def karsilastirma_calistir() -> tuple[list[dict], list[dict], float, float]:
    """
    Tüm örnek sorguları hem API hem de BS4 yöntemiyle çalıştırıp
    süre ölçer.

    Returns:
        (api_sonuclari, bs4_sonuclari, api_sure, bs4_sure) tuple'ı
    """
    logger.info(f"{Fore.CYAN}🔍 API yöntemiyle {len(ARAMA_SORGULARI)} sorgu çalıştırılıyor...{Style.RESET_ALL}")
    api_baslangic = time.time()
    api_sonuclari = []
    for sorgu in ARAMA_SORGULARI:
        api_sonuclari.extend(api_ile_arama(sorgu))
        random_delay(0.1, 0.3)
    api_sure = time.time() - api_baslangic
    logger.info(f"  ✅ API: {len(api_sonuclari)} sonuç, {api_sure:.2f} saniye")

    logger.info(f"\n{Fore.CYAN}🔍 BS4 yöntemiyle {len(ARAMA_SORGULARI)} sorgu çalıştırılıyor...{Style.RESET_ALL}")
    bs4_baslangic = time.time()
    bs4_sonuclari = []
    for sorgu in ARAMA_SORGULARI:
        bs4_sonuclari.extend(bs4_ile_arama(sorgu))
        random_delay(0.1, 0.3)
    bs4_sure = time.time() - bs4_baslangic
    logger.info(f"  ✅ BS4: {len(bs4_sonuclari)} sonuç, {bs4_sure:.2f} saniye")

    return api_sonuclari, bs4_sonuclari, api_sure, bs4_sure


def performans_karsilastirmasi(api_sure: float, bs4_sure: float,
                                api_adet: int, bs4_adet: int) -> None:
    """API ve BS4 yöntemlerinin süresini karşılaştıran tablo yazdırır."""
    print(f"\n{'='*65}")
    print(f"{Fore.CYAN}⚡ PERFORMANS KARŞILAŞTIRMASI: API vs BS4{Style.RESET_ALL}")
    print(f"{'='*65}")
    print(f"  {'Metrik':<30} │ {'API':>12} │ {'BS4':>12}")
    print(f"  {'─'*30} │ {'─'*12} │ {'─'*12}")
    print(
        f"  {'Sorgu Sayısı':<30} │ "
        f"{Fore.GREEN}{len(ARAMA_SORGULARI):>12}{Style.RESET_ALL} │ "
        f"{Fore.YELLOW}{len(ARAMA_SORGULARI):>12}{Style.RESET_ALL}"
    )
    print(
        f"  {'Toplam Sonuç':<30} │ "
        f"{Fore.GREEN}{api_adet:>12}{Style.RESET_ALL} │ "
        f"{Fore.YELLOW}{bs4_adet:>12}{Style.RESET_ALL}"
    )
    print(
        f"  {'Geçen Süre (saniye)':<30} │ "
        f"{Fore.GREEN}{api_sure:>11.2f}s{Style.RESET_ALL} │ "
        f"{Fore.YELLOW}{bs4_sure:>11.2f}s{Style.RESET_ALL}"
    )
    if api_sure > 0:
        oran = bs4_sure / api_sure
        print(f"  {'─'*30} │ {'─'*12} │ {'─'*12}")
        print(
            f"  {Fore.GREEN}{'🚀 API kaç kat hızlı':<30}{Style.RESET_ALL} │ "
            f"{Fore.GREEN}{f'{oran:.1f}x':>27}{Style.RESET_ALL}"
        )
    print(f"{'='*65}\n")


def ozellik_karsilastirma_tablosu() -> None:
    """API yaklaşımının BS4 yaklaşımına göre avantajlarını gösteren tablo."""
    print(f"\n{'='*70}")
    print(f"{Fore.CYAN}📊 API vs BeautifulSoup ÖZELLİK KARŞILAŞTIRMASI{Style.RESET_ALL}")
    print(f"{'='*70}")

    satirlar = [
        ("Özellik", "BS4 (HTML Parse)", "API (JSON)"),
        ("─" * 22, "─" * 22, "─" * 22),
        ("Veri Formatı", "HTML → Parse", "JSON → Direkt"),
        ("Hız", "Yavaş (HTML ağır)", "Hızlı (sadece veri)"),
        ("Bant Genişliği", "Yüksek (CSS/JS/HTML)", "Düşük (sadece JSON)"),
        ("Kırılganlık", "HTML değişirse bozulur", "API stabil"),
        ("Ekstra Kütüphane", "beautifulsoup4, lxml", "Yok (requests yeter)"),
        ("Sonuç Limiti", "Sayfa başına ~20", "Parametreyle esnek"),
        ("Kod Karmaşıklığı", "Yüksek (selector'lar)", "Düşük (key erişimi)"),
        ("Keşif Zorluğu", "Kolay (sayfa görünür)", "Orta (DevTools gerekli)"),
    ]

    for ozellik, bs4, api in satirlar:
        print(
            f"  {Fore.YELLOW}{ozellik:<22}{Style.RESET_ALL} │ "
            f"{bs4:<22} │ {Fore.GREEN}{api:<22}{Style.RESET_ALL}"
        )

    print(f"{'='*70}")

    print(f"\n{Fore.CYAN}📝 Kod Karşılaştırması:{Style.RESET_ALL}")
    print(f"\n  {Fore.RED}BS4 Yaklaşımı (daha karmaşık):{Style.RESET_ALL}")
    print("  ─────────────────────────────")
    print("  soup = BeautifulSoup(html, 'lxml')")
    print("  basliklar = soup.select('.mw-search-result-heading a')")
    print("  snippetler = soup.select('.searchresult')")
    print("  for b, s in zip(basliklar, snippetler):")
    print("      title = b.get_text()")
    print("      aciklama = s.get_text()")

    print(f"\n  {Fore.GREEN}API Yaklaşımı (daha basit):{Style.RESET_ALL}")
    print("  ─────────────────────────")
    print("  data = requests.get(api_url, params={'q': sorgu}).json()")
    print("  for sayfa in data['pages']:")
    print("      title = sayfa['title']")
    print("      aciklama = sayfa['description']")
    print()


def main():
    """
    Ana çalıştırma fonksiyonu.
    API reverse engineering ile Vikipedi aramasını çeker, BS4 ile
    karşılaştırır ve kaydeder.
    """
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔓 GİZLİ API KEŞFİ - VİKİPEDİ ARAMA KAZIYICI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Hedef: tr.wikipedia.org arama otomatik-tamamlama API'si{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Yöntem: API Reverse Engineering vs BeautifulSoup{Style.RESET_ALL}\n")

    baslangic = time.time()

    api_sonuclari, bs4_sonuclari, api_sure, bs4_sure = karsilastirma_calistir()

    performans_karsilastirmasi(
        api_sure, bs4_sure, len(api_sonuclari), len(bs4_sonuclari)
    )

    if api_sonuclari:
        print(f"{Fore.CYAN}📋 Örnek API Sonuçları (İlk 8):{Style.RESET_ALL}")
        print(f"{'─'*70}")
        for r in api_sonuclari[:8]:
            aciklama = r["aciklama"][:45] if r["aciklama"] else "(açıklama yok)"
            print(
                f"  {Fore.GREEN}[{r['sorgu']}]{Style.RESET_ALL} "
                f"{Fore.YELLOW}{r['baslik']:<25}{Style.RESET_ALL} "
                f"— {aciklama}"
            )

        try:
            save_to_json(api_sonuclari, "wikipedia_arama_api", subdir="05_api_reverse")
            save_to_csv(api_sonuclari, "wikipedia_arama_api", subdir="05_api_reverse")
        except Exception as e:
            logger.error(f"💾 Kaydetme hatası: {e}")

    ozellik_karsilastirma_tablosu()

    basarili_sorgu_sayisi = len({r["sorgu"] for r in api_sonuclari})
    gecen_sure = time.time() - baslangic
    print_summary(
        scraper_name="Hidden API Scraper — Vikipedi Arama",
        total_items=len(api_sonuclari),
        elapsed_time=gecen_sure,
        pages_scraped=len(ARAMA_SORGULARI),
        errors=len(ARAMA_SORGULARI) - basarili_sorgu_sayisi,
    )


if __name__ == "__main__":
    main()
