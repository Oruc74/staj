"""
Vikipedi Pageviews & Özet API Kazıyıcı (Wikimedia REST API)
==============================================================
Hedef API : https://wikimedia.org/api/rest_v1/ ve https://tr.wikipedia.org/api/rest_v1/
Yöntem    : Resmi Wikimedia REST API

Wikimedia, resmi ve açık iki REST API sunar:
  1. Pageviews API  → Belirli bir günde en çok okunan sayfaların listesi
  2. Page Summary API → Bir sayfanın başlık, açıklama ve özet bilgisi

Bu script, önce Türkçe Vikipedi'de en çok okunan sayfaların listesini
çeker, ardından her sayfanın özet bilgisini sıralı (sequential) ve
eşzamanlı (concurrent) yöntemlerle çekerek performans farkını gösterir.

API Endpoints:
  - /metrics/pageviews/top/{proje}/all-access/{yıl}/{ay}/{gün}
        → O güne ait en çok görüntülenen sayfalar (görüntülenme sayısıyla)
  - {dil}.wikipedia.org/api/rest_v1/page/summary/{başlık}
        → Sayfanın başlığı, kısa açıklaması ve özet paragrafı

Not: Bu API'ler herkese açıktır, API anahtarı gerektirmez. Ancak
Wikimedia, isteklerde tanımlayıcı bir User-Agent beklemektedir
(bkz. https://meta.wikimedia.org/wiki/User-Agent_policy) — aksi halde
istekler reddedilebilir.
"""

import sys
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import requests

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, random_delay, polite_delay,
    save_to_json, save_to_csv, print_summary, clean_text
)

from colorama import Fore, Style, init

# Colorama Windows uyumluluğu
init(autoreset=True)

# Logger kurulumu
logger = setup_logger("wikipedia_pageviews_api")

# ============================================================
# SABİTLER
# ============================================================
WIKI_DIL = "tr"
PAGEVIEWS_BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top"
SUMMARY_URL_TEMPLATE = f"https://{WIKI_DIL}.wikipedia.org/api/rest_v1/page/summary/{{}}"

# Wikimedia'nın User-Agent politikası gereği tanımlayıcı bir istemci kimliği
API_HEADERS = {
    "User-Agent": (
        "staj-web-scraping-egitim/1.0 "
        "(https://github.com/ornek-kullanici/staj; egitim amacli)"
    )
}

# Çekilecek makale sayısı (meta sayfalar filtrelendikten sonra)
MAKALE_SAYISI = 30

# Eşzamanlı istek ayarları
MAX_WORKERS = 10

# Pageviews verisi genelde 1-2 gün gecikmeli işlenir; güvenli olması için
# 2 gün öncesinin verisini kullanıyoruz.
HEDEF_TARIH = datetime.now() - timedelta(days=2)

# Görüntülenme listesinde çıkmasını istemediğimiz meta/özel ad alanları
HARIC_TUTULAN_ONEKLER = (
    "Özel:", "Kategori:", "Vikipedi:", "Dosya:", "Konuşma:",
    "Şablon:", "Yardım:", "Wikipedia:", "Main_Page", "Anasayfa",
)


def en_cok_okunan_basliklari_cek() -> list[dict]:
    """
    /metrics/pageviews/top/ endpoint'inden hedef tarihte en çok
    görüntülenen Türkçe Vikipedi sayfalarını çeker.

    API Yanıtı: {"items": [{"articles": [{"article": "...", "views": N}, ...]}]}

    Returns:
        {"title": ..., "views": ...} sözlüklerinden oluşan liste
        (meta/özel sayfalar filtrelenmiş, en fazla MAKALE_SAYISI kadar)
    """
    tarih_str = HEDEF_TARIH.strftime("%Y/%m/%d")
    url = f"{PAGEVIEWS_BASE_URL}/{WIKI_DIL}.wikipedia/all-access/{tarih_str}"

    try:
        logger.info(f"📡 En çok okunanlar çekiliyor: {url}")
        response = requests.get(url, headers=API_HEADERS, timeout=15)
        response.raise_for_status()

        veri = response.json()
        makaleler = veri.get("items", [{}])[0].get("articles", [])

        secilenler = []
        for m in makaleler:
            baslik = m.get("article", "")
            if any(baslik.startswith(onek) for onek in HARIC_TUTULAN_ONEKLER):
                continue
            secilenler.append({"title": baslik, "views": m.get("views", 0)})
            if len(secilenler) >= MAKALE_SAYISI:
                break

        logger.info(
            f"✅ {len(makaleler)} sayfa alındı, filtreleme sonrası "
            f"{len(secilenler)} makale kullanılacak ({tarih_str})"
        )
        return secilenler

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ En çok okunanlar çekilemedi: {e}")
        return []
    except (ValueError, KeyError, IndexError) as e:
        logger.error(f"❌ Yanıt ayrıştırılamadı: {e}")
        return []


def tekil_sayfa_ozeti_cek(baslik_bilgi: dict, istek_no: int = 0) -> dict | None:
    """
    /page/summary/{başlık} endpoint'inden tekil bir sayfanın
    özet bilgisini çeker.

    API Yanıt Yapısı (özetlenmiş):
    {
        "title": "Ömer Halisdemir",
        "description": "Türk asker (1974–2016)",
        "extract": "Ömer Halisdemir, Türk asker. ...",
        "content_urls": {"desktop": {"page": "https://..."}}
    }

    Args:
        baslik_bilgi: {"title": ..., "views": ...} sözlüğü
        istek_no: Sıra numarası (rate limiting için)

    Returns:
        İşlenmiş sayfa özeti sözlüğü veya None (hata durumunda)
    """
    baslik = baslik_bilgi["title"]
    url = SUMMARY_URL_TEMPLATE.format(quote(baslik, safe=""))

    try:
        response = requests.get(url, headers=API_HEADERS, timeout=15)
        response.raise_for_status()

        veri = response.json()

        if veri.get("type") == "disambiguation":
            return None

        sayfa = {
            "title": clean_text(veri.get("title", baslik.replace("_", " "))),
            "description": clean_text(veri.get("description", "")),
            "extract": clean_text(veri.get("extract", ""))[:300],
            "views": baslik_bilgi["views"],
            "wiki_link": veri.get("content_urls", {})
                             .get("desktop", {})
                             .get("page", f"https://{WIKI_DIL}.wikipedia.org/wiki/{baslik}"),
        }
        return sayfa

    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ {baslik} çekilemedi: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ {baslik} işlenemedi: {type(e).__name__}: {e}")
        return None


def sirali_cekme(basliklar: list[dict]) -> tuple[list[dict], float]:
    """
    Sayfa özetlerini sıralı (sequential) olarak tek tek çeker.
    Her istek bir öncekinin bitmesini bekler.

    Args:
        basliklar: {"title": ..., "views": ...} sözlüklerinin listesi

    Returns:
        (sayfa_listesi, gecen_sure) tuple'ı
    """
    logger.info(f"\n{Fore.YELLOW}🐢 SIRALI (Sequential) çekme başlatılıyor...{Style.RESET_ALL}")
    baslangic = time.time()
    sayfalar = []

    for i, b in enumerate(basliklar, 1):
        sayfa = tekil_sayfa_ozeti_cek(b, i)
        if sayfa:
            sayfalar.append(sayfa)

        if i % 10 == 0:
            logger.info(f"  📊 İlerleme: {i}/{len(basliklar)}")

        polite_delay(i, base_delay=0.1)

    gecen_sure = time.time() - baslangic
    logger.info(
        f"  ✅ Sıralı çekme tamamlandı: {len(sayfalar)} sayfa, "
        f"{gecen_sure:.2f} saniye"
    )
    return sayfalar, gecen_sure


def eszamanli_cekme(basliklar: list[dict]) -> tuple[list[dict], float]:
    """
    Sayfa özetlerini eşzamanlı (concurrent) olarak ThreadPoolExecutor
    ile çeker. Birden fazla istek aynı anda gönderilir.

    Args:
        basliklar: {"title": ..., "views": ...} sözlüklerinin listesi

    Returns:
        (sayfa_listesi, gecen_sure) tuple'ı
    """
    logger.info(
        f"\n{Fore.GREEN}🚀 EŞZAMANLI (Concurrent) çekme başlatılıyor "
        f"({MAX_WORKERS} thread)...{Style.RESET_ALL}"
    )
    baslangic = time.time()
    sayfalar = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_baslik = {
            executor.submit(tekil_sayfa_ozeti_cek, b, i): b["title"]
            for i, b in enumerate(basliklar, 1)
        }

        tamamlanan = 0
        for future in as_completed(future_to_baslik):
            baslik = future_to_baslik[future]
            try:
                sayfa = future.result()
                if sayfa:
                    sayfalar.append(sayfa)
                tamamlanan += 1

                if tamamlanan % 10 == 0:
                    logger.info(f"  📊 İlerleme: {tamamlanan}/{len(basliklar)}")

            except Exception as e:
                logger.warning(f"⚠️ {baslik} hatası: {e}")

    gecen_sure = time.time() - baslangic
    logger.info(
        f"  ✅ Eşzamanlı çekme tamamlandı: {len(sayfalar)} sayfa, "
        f"{gecen_sure:.2f} saniye"
    )
    return sayfalar, gecen_sure


def performans_karsilastirmasi(sirali_sure: float, eszamanli_sure: float,
                                sirali_adet: int, eszamanli_adet: int) -> None:
    """Sıralı ve eşzamanlı çekme performansını karşılaştıran tablo yazdırır."""
    if eszamanli_sure > 0:
        hizlanma = sirali_sure / eszamanli_sure
    else:
        hizlanma = float('inf')

    print(f"\n{'='*65}")
    print(f"{Fore.CYAN}⚡ PERFORMANS KARŞILAŞTIRMASI: Sıralı vs Eşzamanlı{Style.RESET_ALL}")
    print(f"{'='*65}")
    print(
        f"  {'Metrik':<30} │ {'Sıralı':>12} │ {'Eşzamanlı':>12}"
    )
    print(f"  {'─'*30} │ {'─'*12} │ {'─'*12}")
    print(
        f"  {'Çekilen Sayfa Sayısı':<30} │ "
        f"{Fore.YELLOW}{sirali_adet:>12}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{eszamanli_adet:>12}{Style.RESET_ALL}"
    )
    print(
        f"  {'Geçen Süre (saniye)':<30} │ "
        f"{Fore.YELLOW}{sirali_sure:>11.2f}s{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{eszamanli_sure:>11.2f}s{Style.RESET_ALL}"
    )
    if sirali_adet > 0 and sirali_sure > 0:
        sirali_hiz = sirali_adet / sirali_sure
        eszamanli_hiz = eszamanli_adet / eszamanli_sure if eszamanli_sure > 0 else 0
        print(
            f"  {'Hız (sayfa/saniye)':<30} │ "
            f"{Fore.YELLOW}{sirali_hiz:>11.1f}x{Style.RESET_ALL} │ "
            f"{Fore.GREEN}{eszamanli_hiz:>11.1f}x{Style.RESET_ALL}"
        )
    print(
        f"  {'Thread Sayısı':<30} │ "
        f"{Fore.YELLOW}{'1':>12}{Style.RESET_ALL} │ "
        f"{Fore.GREEN}{MAX_WORKERS:>12}{Style.RESET_ALL}"
    )
    print(f"  {'─'*30} │ {'─'*12} │ {'─'*12}")
    print(
        f"  {'🚀 Hızlanma Oranı':<30} │ "
        f"{Fore.GREEN}{'':>4}{hizlanma:.1f}x daha hızlı{Style.RESET_ALL}"
    )
    print(f"{'='*65}\n")


def sonuclari_goster(sayfalar: list[dict]) -> None:
    """Sayfaları görüntülenme sayısına göre sıralayıp tablo halinde gösterir."""
    if not sayfalar:
        print(f"{Fore.RED}❌ Gösterilecek sayfa yok!{Style.RESET_ALL}")
        return

    sirali = sorted(sayfalar, key=lambda h: h["views"], reverse=True)

    print(f"\n{Fore.CYAN}🏆 EN ÇOK OKUNAN TÜRKÇE VİKİPEDİ SAYFALARI{Style.RESET_ALL}")
    print(f"{'─'*85}")
    print(
        f"  {'#':<4} {'Görüntülenme':>13} {'Başlık':<25} {'Açıklama':<40}"
    )
    print(f"  {'─'*4} {'─'*13} {'─'*25} {'─'*40}")

    for i, s in enumerate(sirali[:15], 1):
        baslik = s['title'][:23] + "..." if len(s['title']) > 23 else s['title']
        aciklama = s['description'][:38] + "..." if len(s['description']) > 38 else s['description']

        if s['views'] >= 30000:
            renk = Fore.RED
        elif s['views'] >= 10000:
            renk = Fore.YELLOW
        else:
            renk = Fore.WHITE

        print(
            f"  {Fore.GREEN}{i:<4}{Style.RESET_ALL} "
            f"{renk}{s['views']:>13,}{Style.RESET_ALL} "
            f"{Fore.BLUE}{baslik:<25}{Style.RESET_ALL} "
            f"{aciklama:<40}"
        )

    print(f"{'─'*85}\n")


def main():
    """
    Ana çalıştırma fonksiyonu.
    Wikimedia REST API'den en çok okunan sayfaları çeker, performans
    karşılaştırması yapar.
    """
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📰 VİKİPEDİ PAGEVIEWS & ÖZET API KAZIYICI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}API: Wikimedia REST API (herkese açık){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Hedef: {HEDEF_TARIH.strftime('%d.%m.%Y')} tarihli en çok okunan {MAKALE_SAYISI} sayfa{Style.RESET_ALL}\n")

    toplam_baslangic = time.time()

    print(f"{Fore.CYAN}📋 Adım 1: En çok okunan başlıklar çekiliyor...{Style.RESET_ALL}")
    basliklar = en_cok_okunan_basliklari_cek()

    if not basliklar:
        logger.error("❌ Başlık listesi alınamadı, çıkılıyor.")
        return

    print(f"\n{Fore.CYAN}📋 Adım 2: Sayfa özetlerini sıralı (sequential) olarak çek{Style.RESET_ALL}")
    sirali_sayfalar, sirali_sure = sirali_cekme(basliklar)

    print(f"\n{Fore.YELLOW}⏳ Eşzamanlı test öncesi 2 saniye bekleniyor...{Style.RESET_ALL}")
    random_delay(1.5, 2.5)

    print(f"\n{Fore.CYAN}📋 Adım 3: Sayfa özetlerini eşzamanlı (concurrent) olarak çek{Style.RESET_ALL}")
    eszamanli_sayfalar, eszamanli_sure = eszamanli_cekme(basliklar)

    performans_karsilastirmasi(
        sirali_sure, eszamanli_sure,
        len(sirali_sayfalar), len(eszamanli_sayfalar)
    )

    kullanilacak = eszamanli_sayfalar if eszamanli_sayfalar else sirali_sayfalar
    sonuclari_goster(kullanilacak)

    sirali_kayit = sorted(kullanilacak, key=lambda h: h["views"], reverse=True)

    if sirali_kayit:
        try:
            save_to_json(sirali_kayit, "vikipedi_en_cok_okunanlar", subdir="05_api_reverse")
            save_to_csv(sirali_kayit, "vikipedi_en_cok_okunanlar", subdir="05_api_reverse")
        except Exception as e:
            logger.error(f"💾 Kaydetme hatası: {e}")

    toplam_sure = time.time() - toplam_baslangic
    print_summary(
        scraper_name="Vikipedi Pageviews & Özet API",
        total_items=len(kullanilacak),
        elapsed_time=toplam_sure,
        pages_scraped=len(basliklar),
        errors=len(basliklar) - len(kullanilacak),
    )


if __name__ == "__main__":
    main()
