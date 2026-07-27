"""
Türkiye'nin İlleri Kazıyıcı (Vikipedi)
========================================
Hedef Site : https://tr.wikipedia.org/wiki/Türkiye'nin_illeri
Yöntem     : requests + BeautifulSoup (lxml ve html.parser karşılaştırmalı)
Açıklama   : Türkiye'nin 81 iline ait bölge, büyükşehir durumu, kuruluş
             tarihi, yüzölçümü, nüfus, yoğunluk, ilçe/mahalle/köy sayısı,
             rakım, plaka ve telefon kodu bilgilerini Vikipedi'deki
             wikitable'dan kazır. Ek olarak lxml ve html.parser
             ayrıştırıcılarının performansını karşılaştırır.
"""

import sys
import os
import time
import re

# Proje kök dizinini Python yoluna ekle (utils modülüne erişim için)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, get_random_headers,
    save_to_json, save_to_csv, print_summary, clean_text
)

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Colorama başlat
init(autoreset=True)

# ============================================================
# SABİTLER
# ============================================================

TARGET_URL = "https://tr.wikipedia.org/wiki/T%C3%BCrkiye%27nin_illeri"

# Tablodaki kısaltılmış bölge kodlarının açık karşılıkları
BOLGE_HARITASI = {
    "MB": "Marmara Bölgesi",
    "EB": "Ege Bölgesi",
    "AB": "Akdeniz Bölgesi",
    "İAB": "İç Anadolu Bölgesi",
    "KB": "Karadeniz Bölgesi",
    "DAB": "Doğu Anadolu Bölgesi",
    "GAB": "Güneydoğu Anadolu Bölgesi",
}

# Logger
logger = setup_logger("wikipedia_scraper")


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def parse_sayi(text: str) -> int:
    """
    Sayı metnini tamsayıya dönüştürür (binlik nokta ayıracını kaldırır).

    Args:
        text: Ham sayı metni (ör. '2.283.609')

    Returns:
        Sayı (tamsayı), ayrıştırılamazsa 0
    """
    try:
        cleaned = re.sub(r'\[.*?\]', '', text)
        digits = re.sub(r'[^\d]', '', cleaned)
        return int(digits) if digits else 0
    except (ValueError, AttributeError):
        return 0


# ============================================================
# TABLO KAZIYICI
# ============================================================

def scrape_iller_tablosu(html_content: str, parser: str = "lxml") -> list[dict]:
    """
    Vikipedi'deki "Türkiye'nin illeri" wikitable'ını ayrıştırır.

    Sütun sırası: İl | Coğrafi bölge | Büyükşehir | Kuruluş tarihi |
    Yüzölçümü (km²) | Nüfus (2025) | Yoğunluk | İlçe sayısı |
    Mahalle sayısı | Köy sayısı | Rakım (m) | Plaka kodu | Telefon kodu | ...

    Args:
        html_content: Sayfanın ham HTML içeriği
        parser: Kullanılacak BeautifulSoup ayrıştırıcısı

    Returns:
        İl verilerinden oluşan sözlük listesi
    """
    soup = BeautifulSoup(html_content, parser)
    iller = []

    tables = soup.select("table.wikitable")
    if not tables:
        logger.error("İller tablosu bulunamadı!")
        return iller

    table = tables[0]
    rows = table.select("tbody tr")

    logger.info(f"Tablo bulundu. Toplam {len(rows)} satır (başlık dahil).")

    for row in rows:
        cells = row.select("td")
        if len(cells) < 13:
            continue

        try:
            il_adi = clean_text(cells[0].get_text())
            if not il_adi:
                continue

            bolge_kodu = clean_text(cells[1].get_text())
            bolge_adi = BOLGE_HARITASI.get(bolge_kodu, bolge_kodu)

            buyuksehir = clean_text(cells[2].get_text()).lower() == "x"
            kurulus_tarihi = clean_text(cells[3].get_text())
            yuzolcumu = parse_sayi(cells[4].get_text())
            nufus = parse_sayi(cells[5].get_text())
            yogunluk = parse_sayi(cells[6].get_text())
            ilce_sayisi = parse_sayi(cells[7].get_text())
            mahalle_sayisi = parse_sayi(cells[8].get_text())
            koy_sayisi = parse_sayi(cells[9].get_text())
            rakim = parse_sayi(cells[10].get_text())

            # Plaka kodu Vikipedi'de baştaki sıfır olmadan gösteriliyor (01 -> 1)
            plaka_raw = clean_text(cells[11].get_text())
            plaka_kodu = plaka_raw.zfill(2) if plaka_raw.isdigit() else plaka_raw

            telefon_kodu = clean_text(cells[12].get_text())

            il = {
                "il": il_adi,
                "bolge": bolge_adi,
                "buyuksehir": buyuksehir,
                "kurulus_tarihi": kurulus_tarihi,
                "yuzolcumu_km2": yuzolcumu,
                "nufus": nufus,
                "yogunluk": yogunluk,
                "ilce_sayisi": ilce_sayisi,
                "mahalle_sayisi": mahalle_sayisi,
                "koy_sayisi": koy_sayisi,
                "rakim_m": rakim,
                "plaka_kodu": plaka_kodu,
                "telefon_kodu": telefon_kodu,
            }
            iller.append(il)

        except Exception as e:
            logger.error(f"Satır ayrıştırma hatası: {e}")

    return iller


# ============================================================
# PERFORMANS KARŞILAŞTIRMASI
# ============================================================

def compare_parsers(html_content: str) -> None:
    """
    lxml ve html.parser ayrıştırıcılarının performansını
    karşılaştırır. Her birini 5 kez çalıştırıp ortalama süre hesaplar.

    Args:
        html_content: Ayrıştırılacak HTML içeriği
    """
    iterations = 5

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"⚡ PARSER PERFORMANS KARŞILAŞTIRMASI")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"  Her parser {iterations} kez çalıştırılacak.\n")

    lxml_times = []
    for i in range(iterations):
        start = time.perf_counter()
        soup = BeautifulSoup(html_content, "lxml")
        _ = soup.select("table.wikitable tr")
        elapsed = time.perf_counter() - start
        lxml_times.append(elapsed)

    lxml_avg = sum(lxml_times) / len(lxml_times)

    htmlparser_times = []
    for i in range(iterations):
        start = time.perf_counter()
        soup = BeautifulSoup(html_content, "html.parser")
        _ = soup.select("table.wikitable tr")
        elapsed = time.perf_counter() - start
        htmlparser_times.append(elapsed)

    htmlparser_avg = sum(htmlparser_times) / len(htmlparser_times)

    print(f"  {'Parser':<20} {'Ortalama Süre':<20} {'Min':<15} {'Max':<15}")
    print(f"  {'-'*70}")
    print(
        f"  {'lxml':<20} "
        f"{Fore.GREEN}{lxml_avg*1000:>8.2f} ms{Style.RESET_ALL:<11} "
        f"{min(lxml_times)*1000:>8.2f} ms     "
        f"{max(lxml_times)*1000:>8.2f} ms"
    )
    print(
        f"  {'html.parser':<20} "
        f"{Fore.YELLOW}{htmlparser_avg*1000:>8.2f} ms{Style.RESET_ALL:<11} "
        f"{min(htmlparser_times)*1000:>8.2f} ms     "
        f"{max(htmlparser_times)*1000:>8.2f} ms"
    )

    if lxml_avg > 0 and htmlparser_avg > 0:
        if lxml_avg < htmlparser_avg:
            ratio = htmlparser_avg / lxml_avg
            print(
                f"\n  {Fore.GREEN}✅ lxml, html.parser'dan "
                f"{ratio:.2f}x daha hızlı!{Style.RESET_ALL}"
            )
        else:
            ratio = lxml_avg / htmlparser_avg
            print(
                f"\n  {Fore.YELLOW}ℹ️  html.parser, lxml'den "
                f"{ratio:.2f}x daha hızlı!{Style.RESET_ALL}"
            )

    print(f"\n{'='*60}\n")


# ============================================================
# ANA GİRİŞ NOKTASI
# ============================================================

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"🇹🇷  Türkiye'nin İlleri Kazıyıcı (Vikipedi)")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    start_time = time.time()
    iller = []
    error_count = 0

    try:
        logger.info(f"Sayfa çekiliyor: {TARGET_URL}")
        print(f"{Fore.YELLOW}📡 Sayfa çekiliyor...{Style.RESET_ALL}")

        response = requests.get(TARGET_URL, headers=get_random_headers(), timeout=20)
        response.raise_for_status()
        html_content = response.text

        print(
            f"  {Fore.GREEN}✔ Sayfa başarıyla çekildi "
            f"({len(html_content):,} karakter){Style.RESET_ALL}\n"
        )

        print(f"{Fore.YELLOW}📊 İller tablosu ayrıştırılıyor...{Style.RESET_ALL}")
        iller = scrape_iller_tablosu(html_content, parser="lxml")

        if iller:
            print(
                f"  {Fore.GREEN}✔ {len(iller)} il verisi çıkarıldı.{Style.RESET_ALL}"
            )

            # Nüfusa göre en kalabalık 10 il
            en_kalabalik = sorted(iller, key=lambda x: x["nufus"], reverse=True)[:10]
            print(f"\n{Fore.CYAN}📋 Nüfusa Göre En Kalabalık 10 İl:{Style.RESET_ALL}")
            print(f"  {'Sıra':<6} {'İl':<20} {'Nüfus':<15} {'Bölge':<25}")
            print(f"  {'-'*70}")
            for i, il in enumerate(en_kalabalik, 1):
                print(
                    f"  {i:<6} {il['il']:<20} "
                    f"{il['nufus']:>12,}     "
                    f"{il['bolge']:<25}"
                )
        else:
            print(f"{Fore.RED}❌ Tablo verisi çıkarılamadı!{Style.RESET_ALL}")

        compare_parsers(html_content)

        if iller:
            save_to_json(iller, "turkiye_illeri", subdir="01_wikipedia")
            save_to_csv(iller, "turkiye_illeri", subdir="01_wikipedia")

    except requests.RequestException as e:
        print(f"{Fore.RED}❌ Sayfa çekilemedi: {e}{Style.RESET_ALL}")
        logger.error(f"HTTP hatası: {e}")
        error_count = 1

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Kullanıcı tarafından durduruldu.{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}❌ Beklenmeyen hata: {e}{Style.RESET_ALL}")
        logger.exception("Beklenmeyen hata oluştu")
        error_count = 1

    elapsed_time = time.time() - start_time

    print_summary(
        scraper_name="Türkiye'nin İlleri (Vikipedi)",
        total_items=len(iller),
        elapsed_time=elapsed_time,
        pages_scraped=1,
        errors=error_count,
    )
