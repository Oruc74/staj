"""
Vikisöz - Türk Yazar Alıntıları Kazıyıcı
==========================================
Hedef Site : https://tr.wikiquote.org (Kategori:Türk yazarlar)
Yöntem     : requests + BeautifulSoup (lxml parser)
Açıklama   : "Kategori:Türk yazarlar" sayfasından yazar listesini çeker,
             ardından her yazarın kendi Vikisöz sayfasına girerek
             alıntılarını (varsa hangi esere ait olduğuyla birlikte) ve
             doğum/ölüm bilgilerini toplar. Alıntılar ve yazarlar ayrı
             veri setleri olarak JSON ve CSV formatlarında kaydedilir.
"""

import sys
import os
import re
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

BASE_URL = "https://tr.wikiquote.org"
API_URL = f"{BASE_URL}/w/api.php"
KATEGORI = "Kategori:Türk yazarlar"
MAX_YAZAR = 20  # Kaç yazar sayfası ziyaret edilecek (kibarlık için sınırlı)

# Logger
logger = setup_logger("quotes_scraper")


# ============================================================
# YAZAR LİSTESİ (KATEGORİ API'Sİ)
# ============================================================

def yazar_listesi_al(limit: int = 40) -> list[str]:
    """
    "Kategori:Türk yazarlar" sayfasındaki yazar adlarını MediaWiki API'si
    üzerinden çeker (alt kategorileri değil, sadece gerçek yazar
    sayfalarını almak için namespace=0 filtresi kullanılır).

    Args:
        limit: En fazla kaç yazar adı alınacağı

    Returns:
        Yazar sayfa başlıklarından oluşan liste
    """
    logger.info(f"'{KATEGORI}' kategorisinden yazar listesi çekiliyor...")

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
        yazarlar = [m["title"] for m in members]
        logger.info(f"{len(yazarlar)} yazar bulundu.")
        return yazarlar
    except (requests.RequestException, ValueError) as e:
        logger.error(f"Yazar listesi alınamadı: {e}")
        return []


# ============================================================
# YAZAR SAYFASI AYRIŞTIRICI
# ============================================================

def bio_bilgisi_cikar(soup: BeautifulSoup) -> dict:
    """
    Yazarın biyografi infobox'undan doğum/ölüm bilgilerini çıkarır.

    Args:
        soup: Yazar sayfasının BeautifulSoup nesnesi

    Returns:
        Doğum/ölüm tarihi ve yeri bilgilerini içeren sözlük
    """
    bio = {"dogum_tarihi": "", "dogum_yeri": "", "olum_tarihi": "", "olum_yeri": ""}

    infobox = soup.select_one("table.infobox")
    if not infobox:
        return bio

    alan_haritasi = {
        "doğum tarihi": "dogum_tarihi",
        "doğum": "dogum_tarihi",
        "doğum yeri": "dogum_yeri",
        "ölüm tarihi": "olum_tarihi",
        "ölüm": "olum_tarihi",
        "ölüm yeri": "olum_yeri",
    }

    for row in infobox.select("tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        etiket = clean_text(th.get_text()).lower()
        for anahtar, alan in alan_haritasi.items():
            if etiket == anahtar and not bio[alan]:
                bio[alan] = clean_text(td.get_text())
                break

    return bio


def alintilari_cikar(soup: BeautifulSoup) -> list[dict]:
    """
    Yazar sayfasındaki üst düzey <ul><li> alıntılarını çıkarır.
    Bir <dl>"Ana madde: ..."</dl> etiketinden sonra gelen <ul> listeleri
    o esere ait kabul edilir; öncesinde eser belirtilmemişse "Genel"
    kategorisine alınır.

    Args:
        soup: Yazar sayfasının BeautifulSoup nesnesi

    Returns:
        {"metin": ..., "eser": ...} sözlüklerinden oluşan liste
    """
    content = soup.select_one("#mw-content-text .mw-parser-output")
    if not content:
        return []

    alintilar = []
    guncel_eser = "Genel"

    for child in content.children:
        name = getattr(child, "name", None)
        if name == "dl":
            dl_text = clean_text(child.get_text())
            eslesme = re.search(r"Ana madde:\s*(.+)", dl_text)
            if eslesme:
                guncel_eser = eslesme.group(1).strip()
        elif name == "ul":
            for li in child.find_all("li", recursive=False):
                metin = clean_text(li.get_text())
                # Çok kısa/boş veya gezinme linki gibi görünen öğeleri atla
                if len(metin) < 15:
                    continue
                alintilar.append({"metin": metin, "eser": guncel_eser})
        elif name in ("h2", "h3"):
            # Yeni bir bölüme (ör. "Dış bağlantılar") geçildiğinde
            # eser bağlamını sıfırla
            baslik = clean_text(child.get_text()).lower()
            if "dış bağlantılar" in baslik or "kaynak" in baslik:
                break

    return alintilar


def yazar_sayfasini_isle(yazar_adi: str) -> tuple[dict | None, list[dict]]:
    """
    Bir yazarın Vikisöz sayfasını çeker ve hem biyografi hem de
    alıntı bilgilerini çıkarır.

    Args:
        yazar_adi: Yazarın Vikisöz sayfa başlığı

    Returns:
        (yazar_bilgisi, alıntı_listesi) tuple'ı. Sayfa alıntı
        içermiyorsa (yazar_bilgisi, []) döner.
    """
    url = f"{BASE_URL}/wiki/{yazar_adi.replace(' ', '_')}"

    try:
        response = requests.get(url, headers=get_random_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Sayfa çekilemedi ({yazar_adi}): {e}")
        return None, []

    soup = BeautifulSoup(response.text, "lxml")

    # Yönlendirme sayfalarını atla
    if soup.select_one(".redirectMsg"):
        logger.info(f"  ↪️  {yazar_adi} bir yönlendirme sayfası, atlanıyor.")
        return None, []

    bio = bio_bilgisi_cikar(soup)
    alintilar = alintilari_cikar(soup)

    yazar_bilgisi = {
        "yazar": yazar_adi,
        "url": url,
        "alinti_sayisi": len(alintilar),
        **bio,
    }

    return yazar_bilgisi, alintilar


# ============================================================
# ANA GİRİŞ NOKTASI
# ============================================================

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"📖  Vikisöz — Türk Yazar Alıntıları Kazıyıcı")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    start_time = time.time()
    tum_alintilar: list[dict] = []
    tum_yazarlar: list[dict] = []
    errors = 0

    try:
        yazar_adlari = yazar_listesi_al(limit=40)

        if not yazar_adlari:
            print(f"{Fore.RED}❌ Yazar listesi alınamadı!{Style.RESET_ALL}")

        print(
            f"{Fore.YELLOW}📝 En fazla {MAX_YAZAR} yazar sayfası "
            f"ziyaret edilecek...{Style.RESET_ALL}\n"
        )

        islenen = 0
        for yazar_adi in yazar_adlari:
            if islenen >= MAX_YAZAR:
                break

            logger.info(f"Yazar işleniyor: {yazar_adi}")
            yazar_bilgisi, alintilar = yazar_sayfasini_isle(yazar_adi)

            if yazar_bilgisi is None:
                errors += 1
                continue

            if not alintilar:
                print(
                    f"  {Fore.YELLOW}⏭️  {yazar_adi}: alıntı bulunamadı, "
                    f"atlanıyor{Style.RESET_ALL}"
                )
                random_delay(0.3, 0.8)
                continue

            for alinti in alintilar:
                alinti["yazar"] = yazar_adi

            tum_alintilar.extend(alintilar)
            tum_yazarlar.append(yazar_bilgisi)
            islenen += 1

            print(
                f"  {Fore.GREEN}✔ [{islenen}/{MAX_YAZAR}] {yazar_adi}: "
                f"{len(alintilar)} alıntı "
                f"({yazar_bilgisi['dogum_tarihi'] or 'tarih bilinmiyor'}){Style.RESET_ALL}"
            )

            random_delay(0.5, 1.5)

        if tum_alintilar:
            save_to_json(tum_alintilar, "alintilar", subdir="01_vikisoz")
            save_to_csv(tum_alintilar, "alintilar", subdir="01_vikisoz")

        if tum_yazarlar:
            save_to_json(tum_yazarlar, "yazarlar", subdir="01_vikisoz")
            save_to_csv(tum_yazarlar, "yazarlar", subdir="01_vikisoz")

        if not tum_alintilar:
            print(f"{Fore.RED}❌ Hiç alıntı çekilemedi!{Style.RESET_ALL}")

        # İlk 5 alıntıyı göster
        if tum_alintilar:
            print(f"\n{Fore.CYAN}📋 İlk 5 Alıntı (Önizleme):{Style.RESET_ALL}")
            print(f"{'─'*60}")
            for i, a in enumerate(tum_alintilar[:5], 1):
                metin_kisa = a["metin"][:80] + "..." if len(a["metin"]) > 80 else a["metin"]
                print(f"  {i}. “{metin_kisa}”")
                print(f"     — {a['yazar']} ({a['eser']})")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Kullanıcı tarafından durduruldu.{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}❌ Beklenmeyen hata: {e}{Style.RESET_ALL}")
        logger.exception("Beklenmeyen hata oluştu")
        errors += 1

    elapsed_time = time.time() - start_time

    print_summary(
        scraper_name="Vikisöz — Türk Yazar Alıntıları",
        total_items=len(tum_alintilar),
        elapsed_time=elapsed_time,
        pages_scraped=len(tum_yazarlar),
        errors=errors,
    )

    if tum_yazarlar:
        print(
            f"  {Fore.CYAN}👤 Toplam Yazar: "
            f"{Fore.GREEN}{len(tum_yazarlar)}{Style.RESET_ALL}\n"
        )
