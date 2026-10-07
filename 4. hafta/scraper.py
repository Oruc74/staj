"""Ahmet Kaya şarkı sözlerini toplayan scraper.

1. hafta 3-4-5'teki web scraping çalışmasının aynısı: önce robots.txt kontrol
ediliyor, sonra sanatçı sayfasındaki şarkı linkleri çıkarılıyor ve her şarkı
sayfasından sözler çekiliyor. İstekler arasında bekleme bırakıldı.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.robotparser
from pathlib import Path

from bs4 import BeautifulSoup

SANATCI_URL = "https://www.sarkisozum.gen.tr/ahmet-kaya"
BASLIK = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
BEKLEME = 0.4  # saniye, siteyi yormamak için
CIKTI = Path(__file__).parent / "veri" / "ahmet_kaya_sarkilar.json"


def robots_izin_var_mi(url):
    """Sitenin robots.txt dosyasına bakıp bu adresi çekebilir miyiz diye sorar.

    robots.txt'yi kendi User-Agent'ımızla indirip parser'a satır satır veriyoruz;
    çünkü site, kütüphanenin varsayılan kimliğine 403 dönüyor ve dosya
    okunamayınca her şey yasakmış gibi görünüyor.
    """
    rp = urllib.robotparser.RobotFileParser()
    istek = urllib.request.Request(
        "https://www.sarkisozum.gen.tr/robots.txt", headers=BASLIK
    )
    with urllib.request.urlopen(istek, timeout=20) as cevap:
        rp.parse(cevap.read().decode("utf-8", "replace").splitlines())
    return rp.can_fetch(BASLIK["User-Agent"], url)


def sayfa_getir(url, deneme=3):
    """Sayfayı indirir, hata olursa biraz bekleyip tekrar dener."""
    for i in range(deneme):
        try:
            istek = urllib.request.Request(url, headers=BASLIK)
            with urllib.request.urlopen(istek, timeout=20) as cevap:
                return cevap.read().decode("utf-8", "replace")
        except Exception as hata:
            if i == deneme - 1:
                print(f"    ! alınamadı: {url} ({hata})")
                return None
            time.sleep(2 * (i + 1))


def sarki_linklerini_bul(html):
    """Sanatçı sayfasındaki tüm şarkı linklerini (ad, url) olarak döndürür."""
    soup = BeautifulSoup(html, "lxml")
    linkler = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/ahmet-kaya/" in href and href.endswith("-sarkisozu"):
            ad = a.get_text(strip=True)
            if ad:
                linkler[href] = ad
    return [(ad, url) for url, ad in linkler.items()]


def sozleri_ayikla(html):
    """Şarkı sayfasındaki sözleri, kıta aralarındaki boşlukları koruyarak alır.

    Sözler class'ı olmayan düz bir <div> içinde, satırlar <br /> ile ayrılmış
    durumda. İçinde en çok <br /> geçen div'i sözler kabul ediyoruz.
    """
    soup = BeautifulSoup(html, "lxml")
    en_iyi, en_cok_br = None, 0
    for div in soup.find_all("div"):
        br_sayisi = len(div.find_all("br", recursive=False))
        if br_sayisi > en_cok_br:
            en_iyi, en_cok_br = div, br_sayisi
    if en_iyi is None:
        return ""

    # Kaynak kodundaki satır sonları anlamsız, asıl satır sonu <br /> etiketi.
    # Önce kod satırlarını temizleyip <br />'leri gerçek satır sonuna çeviriyoruz,
    # böylece kıta aralarındaki çift <br /> boş satır olarak korunuyor.
    ic_html = re.sub(r"[\r\n]+", " ", en_iyi.decode_contents())
    ic_html = re.sub(r"<br\s*/?>", "\n", ic_html, flags=re.I)
    metin = BeautifulSoup(ic_html, "lxml").get_text()

    satirlar = [s.strip() for s in metin.split("\n")]
    metin = re.sub(r"\n{3,}", "\n\n", "\n".join(satirlar))
    return metin.strip()


def main():
    print(f"robots.txt kontrol ediliyor: {SANATCI_URL}")
    if not robots_izin_var_mi(SANATCI_URL):
        print("robots.txt bu sayfayı çekmeye izin vermiyor, duruldu.")
        return
    print("izin var, devam ediliyor.\n")

    liste_html = sayfa_getir(SANATCI_URL)
    if not liste_html:
        print("sanatçı sayfası alınamadı.")
        return

    sarkilar = sarki_linklerini_bul(liste_html)
    print(f"{len(sarkilar)} şarkı linki bulundu.\n")

    sonuclar = []
    for i, (ad, url) in enumerate(sarkilar, 1):
        html = sayfa_getir(url)
        if not html:
            continue
        sozler = sozleri_ayikla(html)
        if len(sozler) < 80:  # boş ya da çok kısa sayfaları alma
            print(f"  {i:>3}/{len(sarkilar)} atlandı (sözler boş): {ad}")
            continue
        sonuclar.append({"sarki": ad, "url": url, "sozler": sozler})
        print(f"  {i:>3}/{len(sarkilar)} {ad} ({len(sozler)} karakter)")
        time.sleep(BEKLEME)

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    with open(CIKTI, "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, ensure_ascii=False, indent=2)

    toplam = sum(len(s["sozler"]) for s in sonuclar)
    print(f"\nbitti: {len(sonuclar)} şarkı, toplam {toplam} karakter")
    print(f"kaydedildi: {CIKTI}")


if __name__ == "__main__":
    # Windows konsolu varsayılan olarak cp1254 kullanıyor, Türkçe karakterler
    # bozuk görünmesin diye çıktıyı UTF-8'e çeviriyoruz.
    sys.stdout.reconfigure(encoding="utf-8")
    main()
