"""
Türk Romanları Kazıyıcı (Vikipedi)
=====================================
Hedef Site : https://tr.wikipedia.org (Kategori:Türk romanları)
Yöntem     : requests + BeautifulSoup (lxml parser)
Açıklama   : "Kategori:Türk romanları" kategorisindeki roman listesini
             MediaWiki API'siyle çeker, ardından her romanın Vikipedi
             sayfasındaki infobox'tan yazar, yayım yılı, yayımcı, sayfa
             sayısı, ISBN gibi bilgileri ve özet paragrafını toplar.
             Sonuçlar JSON ve CSV formatlarında kaydedilir.
"""

import sys
import os
import time

# Proje kök dizinini Python yoluna ekle (utils modülüne erişim için)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, random_delay, get_random_headers,
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

BASE_URL = "https://tr.wikipedia.org"
API_URL = f"{BASE_URL}/w/api.php"
KATEGORI = "Kategori:Türk romanları"

# Vikipedi infobox etiketlerinin normalize edilmiş alan adlarına eşlemesi
INFOBOX_ALAN_HARITASI = {
    "yazar": "yazar",
    "ülke": "ulke",
    "konu": "konu",
    "tür": "tur",
    "yayım": "yayim_yili",
    "yayımlanma tarihi": "yayim_yili",
    "yayımcı": "yayimci",
    "medya türü": "medya_turu",
    "sayfa": "sayfa_sayisi",
    "isbn": "isbn",
}

# Logger
logger = setup_logger("books_scraper")


# ============================================================
# KATEGORİ ÜYELERİ (MEDIAWIKI API)
# ============================================================

def roman_listesi_al(limit: int = 100) -> list[str]:
    """
    "Kategori:Türk romanları" kategorisindeki roman başlıklarını
    MediaWiki API'si üzerinden çeker (alt kategoriler hariç, sadece
    gerçek makale sayfaları).

    Args:
        limit: En fazla kaç roman başlığı alınacağı

    Returns:
        Roman sayfa başlıklarından oluşan liste
    """
    logger.info(f"'{KATEGORI}' kategorisinden roman listesi çekiliyor...")

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
        data = response.json()
        members = data.get("query", {}).get("categorymembers", [])
        romanlar = [m["title"] for m in members]
        logger.info(f"{len(romanlar)} roman bulundu.")
        return romanlar
    except (requests.RequestException, ValueError) as e:
        logger.error(f"Roman listesi alınamadı: {e}")
        return []


# ============================================================
# ROMAN DETAY SAYFASI AYRIŞTIRICI
# ============================================================

def infobox_bilgilerini_cikar(soup: BeautifulSoup) -> dict:
    """
    Roman sayfasındaki infobox tablosundan yapılandırılmış bilgileri
    çıkarır (yazar, yayım yılı, yayımcı, sayfa sayısı, ISBN vb.).

    Args:
        soup: Roman sayfasının BeautifulSoup nesnesi

    Returns:
        Normalize edilmiş alan adlarıyla bilgi sözlüğü
    """
    bilgi = {alan: "" for alan in set(INFOBOX_ALAN_HARITASI.values())}

    infobox = soup.select_one("table.infobox")
    if not infobox:
        return bilgi

    for row in infobox.select("tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        etiket = clean_text(th.get_text()).lower()
        alan = INFOBOX_ALAN_HARITASI.get(etiket)
        if alan and not bilgi[alan]:
            bilgi[alan] = clean_text(td.get_text())

    return bilgi


def roman_sayfasini_isle(baslik: str) -> dict | None:
    """
    Bir romanın Vikipedi sayfasını çeker, infobox ve özet bilgilerini
    çıkarır.

    Args:
        baslik: Romanın Vikipedi sayfa başlığı

    Returns:
        Roman bilgi sözlüğü, sayfa çekilemezse None
    """
    url = f"{BASE_URL}/wiki/{baslik.replace(' ', '_')}"

    try:
        response = requests.get(url, headers=get_random_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Sayfa çekilemedi ({baslik}): {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    if soup.select_one(".redirectMsg"):
        logger.info(f"  ↪️  {baslik} bir yönlendirme sayfası, atlanıyor.")
        return None

    infobox = infobox_bilgilerini_cikar(soup)

    # İlk paragrafı özet olarak al
    content = soup.select_one("#mw-content-text .mw-parser-output")
    ozet = ""
    if content:
        for p in content.select("p"):
            metin = clean_text(p.get_text())
            if len(metin) > 30:
                ozet = metin
                break

    kitap = {
        "baslik": baslik.split(" (roman)")[0],
        "url": url,
        "ozet": ozet[:400],
        **infobox,
    }
    return kitap


# ============================================================
# ANA GİRİŞ NOKTASI
# ============================================================

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"📚  Türk Romanları Kazıyıcı (Vikipedi)")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    start_time = time.time()
    romanlar_data: list[dict] = []
    errors = 0

    try:
        baslik_listesi = roman_listesi_al()

        if not baslik_listesi:
            print(f"{Fore.RED}❌ Roman listesi alınamadı!{Style.RESET_ALL}")

        print(
            f"{Fore.YELLOW}📝 {len(baslik_listesi)} roman sayfası "
            f"ziyaret edilecek...{Style.RESET_ALL}\n"
        )

        for idx, baslik in enumerate(baslik_listesi, 1):
            logger.info(f"Roman işleniyor ({idx}/{len(baslik_listesi)}): {baslik}")
            kitap = roman_sayfasini_isle(baslik)

            if kitap is None:
                errors += 1
                random_delay(0.3, 0.8)
                continue

            romanlar_data.append(kitap)
            print(
                f"  {Fore.GREEN}✔ [{idx}/{len(baslik_listesi)}] {kitap['baslik']} "
                f"— {kitap['yazar'] or 'yazar bilinmiyor'} "
                f"({kitap['yayim_yili'] or '?'}){Style.RESET_ALL}"
            )

            random_delay(0.5, 1.2)

        if romanlar_data:
            save_to_json(romanlar_data, "turk_romanlari", subdir="01_romanlar")
            save_to_csv(romanlar_data, "turk_romanlari", subdir="01_romanlar")
        else:
            print(f"{Fore.RED}❌ Hiç roman verisi çekilemedi!{Style.RESET_ALL}")

        if romanlar_data:
            print(f"\n{Fore.CYAN}📋 İlk 5 Roman (Önizleme):{Style.RESET_ALL}")
            print(f"{'─'*70}")
            for i, k in enumerate(romanlar_data[:5], 1):
                print(
                    f"  {i}. {Fore.GREEN}{k['baslik']}{Style.RESET_ALL} "
                    f"— {k['yazar'] or '?'} ({k['yayim_yili'] or '?'}) "
                    f"| {k['sayfa_sayisi'] or 'sayfa sayısı bilinmiyor'}"
                )

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Kullanıcı tarafından durduruldu.{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}❌ Beklenmeyen hata: {e}{Style.RESET_ALL}")
        logger.exception("Beklenmeyen hata oluştu")
        errors += 1

    elapsed_time = time.time() - start_time

    print_summary(
        scraper_name="Türk Romanları (Vikipedi)",
        total_items=len(romanlar_data),
        elapsed_time=elapsed_time,
        pages_scraped=len(romanlar_data),
        errors=errors,
    )
