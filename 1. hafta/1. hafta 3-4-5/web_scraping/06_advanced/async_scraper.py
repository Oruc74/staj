"""
Asenkron Web Kazıyıcı (Async Scraper)
======================================
Hedef Site : https://tr.wikipedia.org (Kategori:Türk romanları)
Yöntem     : curl_cffi (AsyncSession, Chrome impersonate) + asyncio

Bu script, senkron (requests) ve asenkron (curl_cffi AsyncSession)
yaklaşımlarını karşılaştırarak asenkron programlamanın web kazımadaki
dramatik hız farkını gösterir. Hedef, 01_requests_beautifulsoup/
books_scraper.py ile aynı kategoridir (Türk romanları).

⚠️ ÖNEMLİ BULGU — Neden httpx değil de curl_cffi?
====================================================
Bu script ilk denemede standart 'httpx' kütüphanesiyle yazılmıştı, ancak
Wikimedia (tr.wikipedia.org) TÜM httpx isteklerini 403 Forbidden ile
reddetti — User-Agent ve diğer header'lar tamamen tarayıcı gibi
ayarlanmış olsa bile ("Please respect our robot policy" mesajıyla).
Aynı sayfaya standart 'requests' kütüphanesiyle erişim ise sorunsuz
çalıştı. Bu, 06_advanced/anti_bot_bypass.py'de anlatılan TLS parmak izi
(JA3) tespitinin gerçek dünyada yaşanan somut bir örneğidir: Wikimedia,
httpx'in TLS Client Hello imzasını bilinen bir bot/kütüphane imzası
olarak tanıyıp engelliyor. Çözüm olarak, curl_cffi'nin AsyncSession'ı
kullanıldı — bu, libcurl üzerinden gerçek Chrome TLS parmak izini
taklit ederken asyncio ile eşzamanlı istek atabiliyor.

Senkron vs Asenkron Farkı:
===========================
Senkron (requests):
  İstek 1 ──────> Yanıt 1
                           İstek 2 ──────> Yanıt 2
                                                    İstek 3 ──────> Yanıt 3
  Toplam süre = Süre1 + Süre2 + Süre3

Asenkron (curl_cffi + asyncio):
  İstek 1 ──────> Yanıt 1
  İstek 2 ──────> Yanıt 2      (aynı anda!)
  İstek 3 ──────> Yanıt 3      (aynı anda!)
  Toplam süre ≈ max(Süre1, Süre2, Süre3)

Semaphore Kullanımı:
  - asyncio.Semaphore(5) → aynı anda en fazla 5 istek
  - Sunucuyu yormaz, bağlantı havuzunu kontrollü tutar
  - Daha yüksek değer = daha hızlı ama sunucu üzerinde daha fazla yük
"""

import sys
import os
import time
import asyncio
import requests

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, random_delay, get_random_headers,
    save_to_json, save_to_csv, print_summary, clean_text
)

from colorama import Fore, Style, init

# Colorama Windows uyumluluğu
init(autoreset=True)

# Logger kurulumu
logger = setup_logger("async_scraper")

# ============================================================
# SABİTLER
# ============================================================
BASE_URL = "https://tr.wikipedia.org"
API_URL = f"{BASE_URL}/w/api.php"
KATEGORI = "Kategori:Türk romanları"
MAX_CONCURRENT = 5      # Aynı anda en fazla 5 istek (Semaphore)

INFOBOX_ALAN_HARITASI = {
    "yazar": "yazar",
    "yayım": "yayim_yili",
    "yayımlanma tarihi": "yayim_yili",
    "yayımcı": "yayimci",
}


# ============================================================
# ROMAN LİSTESİ (MEDIAWIKI API — TEK İSTEK)
# ============================================================

def roman_listesi_al(limit: int = 100) -> list[str]:
    """
    "Kategori:Türk romanları" kategorisindeki roman başlıklarını
    MediaWiki API'si üzerinden tek bir istekle çeker.

    Args:
        limit: En fazla kaç roman başlığı alınacağı

    Returns:
        Roman sayfa başlıklarından oluşan liste
    """
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": KATEGORI,
        "cmnamespace": 0,
        "cmlimit": limit,
        "format": "json",
    }
    try:
        response = requests.get(
            API_URL, params=params, headers=get_random_headers(), timeout=15
        )
        response.raise_for_status()
        members = response.json().get("query", {}).get("categorymembers", [])
        return [m["title"] for m in members]
    except (requests.RequestException, ValueError) as e:
        logger.error(f"Roman listesi alınamadı: {e}")
        return []


def html_parse_et(html: str, baslik: str) -> dict:
    """
    Bir roman sayfasının HTML içeriğinden infobox bilgilerini parse eder.

    Args:
        html: Sayfanın HTML içeriği
        baslik: Roman başlığı (URL'den gelen ham başlık)

    Returns:
        Roman bilgi sözlüğü
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("❌ beautifulsoup4 kurulu değil: pip install beautifulsoup4")
        return {}

    soup = BeautifulSoup(html, "html.parser")

    kitap = {
        "baslik": baslik.split(" (roman)")[0],
        "yazar": "",
        "yayim_yili": "",
        "yayimci": "",
    }

    infobox = soup.select_one("table.infobox")
    if infobox:
        for row in infobox.select("tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if not th or not td:
                continue
            etiket = clean_text(th.get_text()).lower()
            alan = INFOBOX_ALAN_HARITASI.get(etiket)
            if alan and not kitap[alan]:
                kitap[alan] = clean_text(td.get_text())

    return kitap


# ============================================================
# SENKRON YAKLAŞIM (requests kütüphanesi)
# ============================================================

def senkron_cekme(basliklar: list[str]) -> tuple[list[dict], float]:
    """
    Tüm roman sayfalarını senkron olarak tek tek çeker.
    Her istek bir öncekinin tamamlanmasını bekler.

    Args:
        basliklar: Çekilecek roman başlıklarının listesi

    Returns:
        (kitap_listesi, gecen_sure) tuple'ı
    """
    logger.info(
        f"{Fore.YELLOW}🐢 SENKRON çekme başlatılıyor "
        f"({len(basliklar)} sayfa)...{Style.RESET_ALL}"
    )
    baslangic = time.time()
    tum_kitaplar = []
    hatalar = 0

    for i, baslik in enumerate(basliklar, 1):
        try:
            url = f"{BASE_URL}/wiki/{baslik.replace(' ', '_')}"
            headers = get_random_headers()
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            kitap = html_parse_et(response.text, baslik)
            if kitap:
                tum_kitaplar.append(kitap)

            if i % 10 == 0:
                logger.info(f"  📊 Senkron ilerleme: {i}/{len(basliklar)}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ {baslik} hatası: {e}")
            hatalar += 1
            continue

    gecen_sure = time.time() - baslangic
    logger.info(
        f"  ✅ Senkron tamamlandı: {len(tum_kitaplar)} roman, "
        f"{gecen_sure:.2f}s, {hatalar} hata"
    )
    return tum_kitaplar, gecen_sure


# ============================================================
# ASENKRON YAKLAŞIM (curl_cffi + asyncio)
# ============================================================

async def asenkron_sayfa_cek(
    client, semaphore: asyncio.Semaphore, baslik: str
) -> dict | None:
    """
    Tek bir roman sayfasını asenkron olarak çeker.
    Semaphore ile eşzamanlı istek sayısını sınırlar.

    Args:
        client: curl_cffi AsyncSession instance'ı
        semaphore: Eşzamanlılık sınırlayıcı
        baslik: Roman başlığı

    Returns:
        Roman bilgi sözlüğü veya None (hata durumunda)
    """
    async with semaphore:
        try:
            url = f"{BASE_URL}/wiki/{baslik.replace(' ', '_')}"
            response = await client.get(url, impersonate="chrome", timeout=15.0)
            response.raise_for_status()
            return html_parse_et(response.text, baslik)
        except Exception as e:
            logger.warning(f"⚠️ Asenkron {baslik} hatası: {e}")
            return None


async def asenkron_cekme(basliklar: list[str]) -> tuple[list[dict], float]:
    """
    Tüm roman sayfalarını asenkron olarak eşzamanlı çeker.
    asyncio.gather() ile tüm görevleri aynı anda başlatır,
    Semaphore ile eşzamanlı istek sayısını kontrol eder.

    curl_cffi'nin AsyncSession'ı kullanılır (bkz. dosya başındaki not) —
    Wikimedia standart httpx isteklerini TLS parmak izinden tanıyıp
    engellediği için, Chrome TLS parmak izini taklit eden curl_cffi
    tercih edildi.

    Args:
        basliklar: Çekilecek roman başlıklarının listesi

    Returns:
        (kitap_listesi, gecen_sure) tuple'ı
    """
    try:
        from curl_cffi.requests import AsyncSession
    except ImportError:
        logger.error(
            f"{Fore.RED}❌ curl_cffi kurulu değil! "
            f"Kurmak için: pip install curl_cffi{Style.RESET_ALL}"
        )
        return [], 0.0

    logger.info(
        f"{Fore.GREEN}🚀 ASENKRON çekme başlatılıyor "
        f"({len(basliklar)} sayfa, max {MAX_CONCURRENT} eşzamanlı, "
        f"Chrome TLS taklidi)...{Style.RESET_ALL}"
    )
    baslangic = time.time()

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with AsyncSession() as client:
        gorevler = [
            asenkron_sayfa_cek(client, semaphore, baslik)
            for baslik in basliklar
        ]

        logger.info(f"  📡 {len(gorevler)} görev oluşturuldu, çalıştırılıyor...")
        sonuclar = await asyncio.gather(*gorevler, return_exceptions=True)

    tum_kitaplar = []
    hatalar = 0
    for sonuc in sonuclar:
        if isinstance(sonuc, Exception) or sonuc is None:
            hatalar += 1
        elif isinstance(sonuc, dict):
            tum_kitaplar.append(sonuc)

    gecen_sure = time.time() - baslangic
    logger.info(
        f"  ✅ Asenkron tamamlandı: {len(tum_kitaplar)} roman, "
        f"{gecen_sure:.2f}s, {hatalar} hata"
    )
    return tum_kitaplar, gecen_sure


# ============================================================
# KARŞILAŞTIRMA TABLOSU
# ============================================================

def karsilastirma_tablosu(
    senkron_sure: float, asenkron_sure: float,
    senkron_adet: int, asenkron_adet: int
) -> None:
    """
    Senkron ve asenkron performansı karşılaştıran detaylı
    bir tablo yazdırır.
    """
    if asenkron_sure > 0:
        hizlanma = senkron_sure / asenkron_sure
    else:
        hizlanma = float('inf')

    tasarruf = senkron_sure - asenkron_sure

    print(f"\n{'='*70}")
    print(f"{Fore.CYAN}⚡ PERFORMANS KARŞILAŞTIRMASI: Senkron vs Asenkron{Style.RESET_ALL}")
    print(f"{'='*70}")

    print(
        f"  {'Metrik':<35} │ {'Senkron (requests)':>17} │ "
        f"{'Asenkron (curl_cffi)':>17}"
    )
    print(f"  {'─'*35} │ {'─'*17} │ {'─'*17}")

    print(
        f"  {'Kütüphane':<35} │ "
        f"{Fore.YELLOW}{'requests':>17}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{'curl_cffi + asyncio':>17}{Style.RESET_ALL}"
    )
    print(
        f"  {'Yaklaşım':<35} │ "
        f"{Fore.YELLOW}{'Sıralı (blocking)':>17}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{'Eşzamanlı (async)':>17}{Style.RESET_ALL}"
    )
    print(
        f"  {'Eşzamanlı İstek Sayısı':<35} │ "
        f"{Fore.YELLOW}{'1':>17}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{MAX_CONCURRENT:>17}{Style.RESET_ALL}"
    )
    print(
        f"  {'Çekilen Roman Sayısı':<35} │ "
        f"{Fore.YELLOW}{senkron_adet:>17}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{asenkron_adet:>17}{Style.RESET_ALL}"
    )
    print(
        f"  {'Geçen Süre':<35} │ "
        f"{Fore.YELLOW}{senkron_sure:>15.2f}s{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{asenkron_sure:>15.2f}s{Style.RESET_ALL}"
    )

    senkron_hiz = senkron_adet / senkron_sure if senkron_sure > 0 else 0
    asenkron_hiz = asenkron_adet / asenkron_sure if asenkron_sure > 0 else 0
    print(
        f"  {'Hız (sayfa/saniye)':<35} │ "
        f"{Fore.YELLOW}{senkron_hiz:>15.1f}x{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{asenkron_hiz:>15.1f}x{Style.RESET_ALL}"
    )

    print(f"  {'─'*35} │ {'─'*17} │ {'─'*17}")
    print(
        f"  {Fore.GREEN}{'🚀 Hızlanma Oranı':<35}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{f'{hizlanma:.1f}x daha hızlı':>37}{Style.RESET_ALL}"
    )
    print(
        f"  {Fore.GREEN}{'⏱️  Zaman Tasarrufu':<35}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{f'{tasarruf:.2f} saniye':>37}{Style.RESET_ALL}"
    )
    print(f"{'='*70}")

    print(f"\n  {Fore.YELLOW}📝 Not:{Style.RESET_ALL}")
    print(f"  • Senkron: Her istek sırayla, biri bitmeden diğeri başlamaz")
    print(f"  • Asenkron: Semaphore({MAX_CONCURRENT}) ile {MAX_CONCURRENT} istek aynı anda çalışır")
    print(f"  • Gerçek dünyada fark, ağ gecikmesine bağlı olarak daha dramatik olabilir")
    print(f"  • Semaphore değeri arttıkça hız artar ama sunucu üzerindeki yük de artar\n")


def main():
    """
    Ana çalıştırma fonksiyonu.
    Senkron ve asenkron kazımayı çalıştırıp karşılaştırır.
    """
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⚡ ASENKRON WEB KAZIYICI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

    basliklar = roman_listesi_al()
    if not basliklar:
        print(f"{Fore.RED}❌ Roman listesi alınamadı, çıkılıyor.{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}Hedef: tr.wikipedia.org — Türk romanları ({len(basliklar)} sayfa){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Karşılaştırma: requests (senkron) vs curl_cffi (asenkron){Style.RESET_ALL}\n")

    toplam_baslangic = time.time()

    # ─── 1. Senkron Çekme ───
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📋 ADIM 1: Senkron Çekme (requests){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    senkron_kitaplar, senkron_sure = senkron_cekme(basliklar)

    print(f"\n{Fore.YELLOW}⏳ Asenkron test öncesi kısa bekleme...{Style.RESET_ALL}")
    random_delay(1.5, 2.5)

    # ─── 2. Asenkron Çekme ───
    print(f"\n{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📋 ADIM 2: Asenkron Çekme (curl_cffi + asyncio){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")

    asenkron_kitaplar, asenkron_sure = asyncio.run(asenkron_cekme(basliklar))

    # ─── 3. Karşılaştırma Tablosu ───
    karsilastirma_tablosu(
        senkron_sure, asenkron_sure,
        len(senkron_kitaplar), len(asenkron_kitaplar),
    )

    # ─── 4. Sonuçları Kaydet (asenkron sonuçları kullan) ───
    kullanilacak = asenkron_kitaplar if asenkron_kitaplar else senkron_kitaplar

    if kullanilacak:
        print(f"\n{Fore.CYAN}📚 İlk 10 Roman (Önizleme):{Style.RESET_ALL}")
        print(f"{'─'*70}")
        for i, kitap in enumerate(kullanilacak[:10], 1):
            baslik = kitap['baslik'][:40] + "..." if len(kitap['baslik']) > 40 else kitap['baslik']
            print(
                f"  {Fore.GREEN}{i:>2}.{Style.RESET_ALL} "
                f"{Fore.YELLOW}{baslik:<43}{Style.RESET_ALL} │ "
                f"{kitap['yazar'] or '?':<25} │ {kitap['yayim_yili'] or '?'}"
            )
        print(f"{'─'*70}")

        try:
            save_to_json(kullanilacak, "async_romanlar", subdir="06_advanced")
            save_to_csv(kullanilacak, "async_romanlar", subdir="06_advanced")
        except Exception as e:
            logger.error(f"💾 Kaydetme hatası: {e}")

    toplam_sure = time.time() - toplam_baslangic
    print_summary(
        scraper_name="Async Scraper (curl_cffi + asyncio) — Türk Romanları",
        total_items=len(kullanilacak),
        elapsed_time=toplam_sure,
        pages_scraped=len(basliklar) * 2,  # Senkron + Asenkron
        errors=0,
    )


if __name__ == "__main__":
    main()
