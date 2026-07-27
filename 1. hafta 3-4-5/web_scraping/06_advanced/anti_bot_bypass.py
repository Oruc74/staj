"""
Anti-Bot Farkındalık ve TLS Parmak İzi Karşılaştırması
======================================================
Hedef Endpoint : https://tls.browserleaks.com/json
Yöntem         : curl_cffi ile tarayıcı benzeri TLS parmak izi

Bu script, modern web sitelerinin bot tespiti için kullandığı
TLS parmak izi (fingerprinting) tekniğini ve bunun nasıl
aşılabileceğini gösterir.

⚠️ ETİK UYARI (ETHICAL DISCLAIMER):
=====================================
Bu script YALNIZCA EĞİTİM AMAÇLIDIR. Aşağıdaki durumlar için uygundur:
  ✅ Kendi web sitenizin bot korumasını test etmek
  ✅ Güvenlik araştırması ve penetrasyon testi
  ✅ Anti-bot mekanizmalarını akademik olarak anlamak
  ✅ Web kazıma teknolojilerini öğrenmek

Aşağıdaki durumlar için UYGUN DEĞİLDİR:
  ❌ Başkalarının web sitelerini izinsiz kazımak
  ❌ Rate limiting'i aşmak
  ❌ Hizmet şartlarını ihlal etmek
  ❌ DDoS veya kötü amaçlı aktiviteler

Her zaman hedef sitenin robots.txt dosyasını kontrol edin
ve hizmet şartlarına uyun.

Bot Tespit Katmanları (5 Layer Defense):
=========================================

Katman 1 — IP İtibarı (IP Reputation):
  - Veri merkezi IP'leri (AWS, GCP, Azure) genelde engellenir
  - Konut IP'leri daha güvenilir görülür
  - IP'nin geçmiş davranışı değerlendirilir
  - Çözüm: Konut proxy'leri kullanmak (ama bu pahalıdır)

Katman 2 — TLS Parmak İzi (JA3/JA4 Fingerprinting):
  - TLS handshake sırasında Client Hello mesajı analiz edilir
  - Cipher suite sırası, uzantılar, elliptic curve'ler incelenir
  - Her tarayıcının benzersiz bir TLS parmak izi vardır
  - Python 'requests' kütüphanesi Python/urllib parmak izi bırakır
  - curl_cffi, gerçek tarayıcı TLS parmak izi taklit eder
  - JA3: TLS Client Hello'nun MD5 hash'i
  - JA4: JA3'ün geliştirilmiş versiyonu (daha detaylı)

Katman 3 — Tarayıcı Parmak İzi (Browser Fingerprinting):
  - JavaScript çalıştırılarak tarayıcı özellikleri toplanır
  - Canvas fingerprint, WebGL, AudioContext
  - Ekran çözünürlüğü, yüklü fontlar, eklentiler
  - Navigator.webdriver özelliği (Selenium tespiti)
  - Çözüm: Playwright/Puppeteer ile gerçek tarayıcı kullanmak

Katman 4 — Davranış Analizi (Behavioral Analysis):
  - Mouse hareketleri, tıklama desenleri
  - Sayfa kaydırma hızı ve yönü
  - Form doldurma süresi (çok hızlı = bot)
  - Sayfa geçiş süresi ve sırası
  - Çözüm: İnsan benzeri gecikmeler ve rastgele davranışlar

Katman 5 — Aktif Sorgulamalar (Active Challenges):
  - CAPTCHA (reCAPTCHA, hCaptcha, Turnstile)
  - Proof of Work (hesaplama gücü ispatı)
  - JavaScript zorlukları (bot JS çalıştıramaz)
  - Çözüm: CAPTCHA servisleri (2Captcha, Anti-Captcha)
    veya gerçek tarayıcı + insan müdahalesi
"""

import sys
import os
import time
import json
import requests

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.helpers import (
    setup_logger, get_random_headers, get_json_headers,
    save_to_json, print_summary
)

from colorama import Fore, Style, init

# Colorama Windows uyumluluğu
init(autoreset=True)

# Logger kurulumu
logger = setup_logger("anti_bot_bypass")

# ============================================================
# SABİTLER
# ============================================================
# TLS parmak izi kontrolü yapan endpoint
# Bu site, isteğin TLS handshake bilgilerini JSON olarak döndürür
TLS_CHECK_URL = "https://tls.browserleaks.com/json"

# Alternatif kontrol URL'leri (yedek)
ALTERNATIF_URLS = [
    "https://tls.browserleaks.com/json",
    "https://ja3er.com/json",
]


def etik_uyari_goster() -> None:
    """
    Script başlangıcında etik uyarı mesajı gösterir.
    Kullanıcıyı yasal ve etik sorumlulukları hakkında bilgilendirir.
    """
    print(f"\n{Fore.RED}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.RED}⚠️  ETİK UYARI / ETHICAL DISCLAIMER{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}")
    print(f"""
  {Fore.YELLOW}Bu script yalnızca EĞİTİM amaçlıdır.{Style.RESET_ALL}
  Bot tespit mekanizmalarını anlamak ve kendi sistemlerinizi
  test etmek için kullanılmalıdır.

  {Fore.GREEN}✅ İzin verilen kullanım:{Style.RESET_ALL}
     • Kendi web sitenizin güvenliğini test etme
     • Akademik araştırma ve öğrenme
     • Yetkili penetrasyon testi

  {Fore.RED}❌ Yasak kullanım:{Style.RESET_ALL}
     • İzinsiz web kazıma
     • Hizmet şartlarını ihlal
     • Kötü amaçlı aktiviteler
    """)
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")


def normal_requests_testi() -> dict | None:
    """
    Standart 'requests' kütüphanesi ile TLS parmak izi kontrolü yapar.

    requests kütüphanesi, Python'un urllib3 kütüphanesini kullanır.
    Bu, Python'a özgü bir TLS parmak izi oluşturur ve bot olarak
    kolayca tespit edilebilir.

    Teknik Detay:
    - requests → urllib3 → OpenSSL kullanır
    - TLS Client Hello mesajı Python'a özgü cipher suite sırası içerir
    - JA3 hash'i, bilinen Python/bot parmak izleriyle eşleşir
    - Birçok anti-bot sistemi bu parmak izini tanır ve engeller

    Returns:
        TLS bilgilerini içeren sözlük veya None (hata durumunda)
    """
    logger.info(f"{Fore.YELLOW}🔍 Normal requests ile TLS testi...{Style.RESET_ALL}")

    try:
        headers = get_json_headers()
        response = requests.get(TLS_CHECK_URL, headers=headers, timeout=15)
        response.raise_for_status()

        veri = response.json()
        return {
            "method": "requests (Python/urllib3)",
            "ja3_hash": veri.get("ja3_hash", "N/A"),
            "ja3_text": veri.get("ja3_text", "N/A"),
            "ja4": veri.get("ja4", "N/A"),
            "akamai_hash": veri.get("akamai_hash", "N/A"),
            "akamai_text": veri.get("akamai_text", "N/A"),
            "tls_version": veri.get("tls_version", "N/A"),
            "cipher_suite": veri.get("cipher_name", "N/A"),
            "user_agent": veri.get("user_agent", headers.get("User-Agent", "N/A")),
            "protocol": veri.get("protocol", "N/A"),
            "raw_response": veri,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ requests testi başarısız: {e}")
        return None

    except Exception as e:
        logger.error(f"❌ Beklenmeyen hata: {type(e).__name__}: {e}")
        return None


def curl_cffi_testi() -> dict | None:
    """
    curl_cffi kütüphanesi ile TLS parmak izi kontrolü yapar.

    curl_cffi, libcurl'ün Python sarmalayıcısıdır ve gerçek
    tarayıcı TLS parmak izlerini taklit edebilir. 'impersonate'
    parametresi ile Chrome, Firefox, Safari gibi tarayıcıların
    TLS davranışını birebir kopyalar.

    Teknik Detay:
    - curl_cffi → libcurl → BoringSSL kullanır (Chrome ile aynı)
    - TLS Client Hello, Chrome'un gerçek cipher suite sırası ile gönderilir
    - JA3 hash'i, gerçek Chrome tarayıcısıyla aynıdır
    - HTTP/2 SETTINGS frame'i de tarayıcı ile uyumludur
    - Akamai fingerprint (HTTP/2) de doğru şekilde taklit edilir

    Returns:
        TLS bilgilerini içeren sözlük veya None (hata durumunda)
    """
    logger.info(f"{Fore.GREEN}🔍 curl_cffi ile TLS testi (Chrome taklidi)...{Style.RESET_ALL}")

    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        logger.error(
            f"{Fore.RED}❌ curl_cffi kurulu değil! "
            f"Kurmak için: pip install curl_cffi{Style.RESET_ALL}"
        )
        # Kurulum bilgisi
        print(f"\n  {Fore.YELLOW}📦 Kurulum:{Style.RESET_ALL}")
        print(f"  pip install curl_cffi")
        print(f"  (Bu kütüphane libcurl'ün C binding'ini içerir)\n")
        return None

    try:
        # impersonate="chrome" parametresi Chrome'un TLS parmak izini taklit eder
        # Desteklenen tarayıcılar: chrome, firefox, safari, edge, vs.
        response = cffi_requests.get(
            TLS_CHECK_URL,
            impersonate="chrome",  # Chrome TLS parmak izi taklit et
            timeout=15,
        )

        veri = response.json()
        return {
            "method": "curl_cffi (Chrome impersonate)",
            "ja3_hash": veri.get("ja3_hash", "N/A"),
            "ja3_text": veri.get("ja3_text", "N/A"),
            "ja4": veri.get("ja4", "N/A"),
            "akamai_hash": veri.get("akamai_hash", "N/A"),
            "akamai_text": veri.get("akamai_text", "N/A"),
            "tls_version": veri.get("tls_version", "N/A"),
            "cipher_suite": veri.get("cipher_name", "N/A"),
            "user_agent": veri.get("user_agent", "N/A"),
            "protocol": veri.get("protocol", "N/A"),
            "raw_response": veri,
        }

    except Exception as e:
        logger.error(f"❌ curl_cffi testi başarısız: {type(e).__name__}: {e}")
        return None


def sonuclari_karsilastir(normal: dict | None, cffi: dict | None) -> None:
    """
    Normal requests ve curl_cffi sonuçlarını yan yana karşılaştırır.
    TLS parmak izi farklarını vurgular.

    Args:
        normal: Normal requests ile alınan TLS bilgileri
        cffi: curl_cffi ile alınan TLS bilgileri
    """
    print(f"\n{'='*75}")
    print(f"{Fore.CYAN}🔍 TLS PARMAK İZİ KARŞILAŞTIRMASI{Style.RESET_ALL}")
    print(f"{'='*75}")

    if not normal and not cffi:
        print(f"{Fore.RED}❌ Her iki test de başarısız oldu!{Style.RESET_ALL}")
        return

    # Karşılaştırılacak alanlar
    karsilastirma_alanlari = [
        ("Yöntem", "method"),
        ("TLS Sürümü", "tls_version"),
        ("Cipher Suite", "cipher_suite"),
        ("Protokol", "protocol"),
        ("JA3 Hash", "ja3_hash"),
        ("JA4", "ja4"),
        ("Akamai Hash", "akamai_hash"),
        ("User-Agent", "user_agent"),
    ]

    # Başlık
    print(
        f"\n  {'Alan':<18} │ {'requests (Python)':^25} │ "
        f"{'curl_cffi (Chrome)':^25}"
    )
    print(f"  {'─'*18} │ {'─'*25} │ {'─'*25}")

    for alan_adi, alan_key in karsilastirma_alanlari:
        normal_deger = normal.get(alan_key, "Test yapılmadı") if normal else "Test yapılmadı"
        cffi_deger = cffi.get(alan_key, "Test yapılmadı") if cffi else "Test yapılmadı"

        # Uzun değerleri kısalt
        if isinstance(normal_deger, str) and len(normal_deger) > 25:
            normal_deger = normal_deger[:22] + "..."
        if isinstance(cffi_deger, str) and len(cffi_deger) > 25:
            cffi_deger = cffi_deger[:22] + "..."

        # Farklı değerleri vurgula
        farkli = normal_deger != cffi_deger
        renk_normal = Fore.RED if farkli else Fore.WHITE
        renk_cffi = Fore.GREEN if farkli else Fore.WHITE

        print(
            f"  {Fore.YELLOW}{alan_adi:<18}{Style.RESET_ALL} │ "
            f"{renk_normal}{str(normal_deger):^25}{Style.RESET_ALL} │ "
            f"{renk_cffi}{str(cffi_deger):^25}{Style.RESET_ALL}"
        )

    print(f"  {'─'*18} │ {'─'*25} │ {'─'*25}")

    # JA3 hash karşılaştırması (detaylı)
    if normal and cffi:
        normal_ja3 = normal.get("ja3_hash", "")
        cffi_ja3 = cffi.get("ja3_hash", "")

        print(f"\n{Fore.CYAN}📋 JA3 Hash Detayları:{Style.RESET_ALL}")
        print(f"  {Fore.RED}requests : {normal_ja3}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}curl_cffi: {cffi_ja3}{Style.RESET_ALL}")

        if normal_ja3 != cffi_ja3:
            print(f"\n  {Fore.GREEN}✅ JA3 parmak izleri FARKLI!{Style.RESET_ALL}")
            print(f"  → curl_cffi, gerçek Chrome TLS parmak izini kullanıyor")
            print(f"  → Anti-bot sistemleri curl_cffi'yi tarayıcı olarak algılar")
        else:
            print(f"\n  {Fore.YELLOW}⚠️ JA3 parmak izleri AYNI (beklenmedik durum){Style.RESET_ALL}")

    print(f"\n{'='*75}\n")


def bot_tespit_katmanlari_goster() -> None:
    """
    Bot tespit mekanizmalarının 5 katmanını detaylı şekilde
    açıklayan bilgilendirici çıktı üretir.
    """
    print(f"\n{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🛡️ BOT TESPİT KATMANLARI (5 Layer Defense){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*65}{Style.RESET_ALL}")

    katmanlar = [
        {
            "no": 1,
            "ad": "IP İtibarı (IP Reputation)",
            "emoji": "🌐",
            "aciklama": "IP adresi veri merkezine mi, konut ağına mı ait?",
            "tespit": "AWS/GCP/Azure IP'leri → %90 ihtimalle bot",
            "asma": "Konut (residential) proxy kullanmak",
            "zorluk": "Düşük",
        },
        {
            "no": 2,
            "ad": "TLS Parmak İzi (JA3/JA4)",
            "emoji": "🔐",
            "aciklama": "TLS handshake sırasındaki cipher suite sırası",
            "tespit": "Python/urllib3 parmak izi → bilinen bot",
            "asma": "curl_cffi ile tarayıcı TLS taklidi",
            "zorluk": "Orta",
        },
        {
            "no": 3,
            "ad": "Tarayıcı Parmak İzi (Browser FP)",
            "emoji": "🖥️",
            "aciklama": "JavaScript ile toplanan tarayıcı özellikleri",
            "tespit": "Canvas, WebGL, fontlar, navigator.webdriver",
            "asma": "Playwright/Puppeteer + stealth eklentileri",
            "zorluk": "Yüksek",
        },
        {
            "no": 4,
            "ad": "Davranış Analizi (Behavioral)",
            "emoji": "🖱️",
            "aciklama": "Mouse, klavye, kaydırma desenleri",
            "tespit": "Çok hızlı tıklama, doğrusal mouse hareketi",
            "asma": "İnsan benzeri gecikme ve rastgele davranışlar",
            "zorluk": "Çok Yüksek",
        },
        {
            "no": 5,
            "ad": "Aktif Sorgulamalar (CAPTCHA)",
            "emoji": "🧩",
            "aciklama": "CAPTCHA, Proof of Work, JS challenge",
            "tespit": "reCAPTCHA, hCaptcha, Cloudflare Turnstile",
            "asma": "CAPTCHA çözüm servisleri veya gerçek insan",
            "zorluk": "Maksimum",
        },
    ]

    for k in katmanlar:
        # Zorluk rengi
        zorluk_renk = {
            "Düşük": Fore.GREEN,
            "Orta": Fore.YELLOW,
            "Yüksek": Fore.RED,
            "Çok Yüksek": Fore.RED,
            "Maksimum": Fore.RED,
        }.get(k["zorluk"], Fore.WHITE)

        print(f"\n  {k['emoji']} {Fore.YELLOW}Katman {k['no']}: {k['ad']}{Style.RESET_ALL}")
        print(f"  {'─'*55}")
        print(f"    Açıklama : {k['aciklama']}")
        print(f"    Tespit   : {Fore.RED}{k['tespit']}{Style.RESET_ALL}")
        print(f"    Aşma     : {Fore.GREEN}{k['asma']}{Style.RESET_ALL}")
        print(f"    Zorluk   : {zorluk_renk}{k['zorluk']}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
    print(f"\n  {Fore.YELLOW}💡 Tavsiye:{Style.RESET_ALL}")
    print(f"  Çoğu web sitesi sadece Katman 1-2 uygular.")
    print(f"  Katman 3-5 genelde büyük şirketler (Google, Amazon, Cloudflare)")
    print(f"  tarafından kullanılır. Basit scraping için curl_cffi + random delay")
    print(f"  genellikle yeterlidir.\n")


def main():
    """
    Ana çalıştırma fonksiyonu.
    Normal requests ve curl_cffi ile TLS parmak izi karşılaştırması yapar.
    """
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🛡️ ANTİ-BOT FARKINDALIK & TLS PARMAK İZİ{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

    # ─── Etik Uyarı ───
    etik_uyari_goster()

    baslangic = time.time()

    # ─── 1. Bot Tespit Katmanlarını Açıkla ───
    bot_tespit_katmanlari_goster()

    # ─── 2. Normal requests Testi ───
    print(f"\n{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🧪 TEST 1: Standart requests kütüphanesi{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    normal_sonuc = normal_requests_testi()

    if normal_sonuc:
        logger.info(f"  ✅ JA3 Hash: {normal_sonuc.get('ja3_hash', 'N/A')[:40]}...")
    else:
        logger.warning("  ⚠️ Normal requests testi başarısız")

    # ─── 3. curl_cffi Testi ───
    print(f"\n{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🧪 TEST 2: curl_cffi (Chrome impersonate){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    cffi_sonuc = curl_cffi_testi()

    if cffi_sonuc:
        logger.info(f"  ✅ JA3 Hash: {cffi_sonuc.get('ja3_hash', 'N/A')[:40]}...")
    else:
        logger.warning("  ⚠️ curl_cffi testi başarısız (kütüphane kurulu olmayabilir)")

    # ─── 4. Karşılaştırma ───
    sonuclari_karsilastir(normal_sonuc, cffi_sonuc)

    # ─── 5. Ham Sonuçları Kaydet ───
    kayit_verileri = []
    if normal_sonuc:
        kayit = {k: v for k, v in normal_sonuc.items() if k != "raw_response"}
        kayit_verileri.append(kayit)
    if cffi_sonuc:
        kayit = {k: v for k, v in cffi_sonuc.items() if k != "raw_response"}
        kayit_verileri.append(kayit)

    if kayit_verileri:
        try:
            save_to_json(kayit_verileri, "tls_fingerprint_comparison", subdir="06_advanced")
        except Exception as e:
            logger.error(f"💾 Kaydetme hatası: {e}")

    # ─── 6. Pratik Öneriler ───
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💡 PRATİK ÖNERİLER{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"""
  {Fore.GREEN}Basit siteler (bot koruması yok):{Style.RESET_ALL}
    → requests + random headers yeterli

  {Fore.YELLOW}Orta seviye koruma (TLS kontrolü):{Style.RESET_ALL}
    → curl_cffi + impersonate="chrome" kullan
    → Random delay ekle (1-3 saniye)

  {Fore.RED}Gelişmiş koruma (Cloudflare, Akamai):{Style.RESET_ALL}
    → Playwright/Puppeteer ile gerçek tarayıcı
    → undetected-chromedriver
    → Konut proxy'leri

  {Fore.RED}Maksimum koruma (CAPTCHA + davranış analizi):{Style.RESET_ALL}
    → İnsan müdahalesi gerekebilir
    → CAPTCHA çözüm servisleri
    → Belki API varsa onu kullanmak en iyisi!
    """)

    # ─── 7. Özet ───
    gecen_sure = time.time() - baslangic
    basarili_test = sum(1 for x in [normal_sonuc, cffi_sonuc] if x is not None)
    print_summary(
        scraper_name="Anti-Bot & TLS Fingerprint",
        total_items=basarili_test,
        elapsed_time=gecen_sure,
        pages_scraped=2,
        errors=2 - basarili_test,
    )


if __name__ == "__main__":
    main()
