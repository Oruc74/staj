"""
Web Scraping Yardımcı Fonksiyonlar
===================================
Tüm scraper'ların ortak kullandığı utility fonksiyonları.
"""

import json
import csv
import os
import sys
import time
import random
import logging
from datetime import datetime
from typing import Any
from colorama import Fore, Style, init

# Windows konsolu varsayılan olarak cp1254/cp1252 gibi kod sayfaları kullanır,
# bu da emoji içeren print() çağrılarında UnicodeEncodeError'a yol açar.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

# Colorama başlat (Windows uyumluluğu)
init(autoreset=True)


# ============================================================
# LOGGING KONFIGÜRASYONU
# ============================================================

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Her scraper için ayrı bir logger oluşturur.
    Hem konsola hem dosyaya log yazar.
    
    Args:
        name: Logger ismi (genellikle scraper adı)
        level: Log seviyesi
    
    Returns:
        Yapılandırılmış logger nesnesi
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Eğer handler zaten eklenmişse tekrar ekleme
    if logger.handlers:
        return logger
    
    # Konsol handler - renkli çıktı
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        f'{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} '
        f'{Fore.YELLOW}%(name)s{Style.RESET_ALL} - '
        f'%(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # Dosya handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'{name}.log'),
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_format = logging.Formatter(
        '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger


# ============================================================
# RATE LIMITING & DELAY
# ============================================================

def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """
    Rastgele bir süre bekler. Bot tespitini önlemek için
    istekler arasına insan benzeri gecikmeler ekler.
    
    Args:
        min_sec: Minimum bekleme süresi (saniye)
        max_sec: Maksimum bekleme süresi (saniye)
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def polite_delay(request_count: int, base_delay: float = 1.0) -> None:
    """
    İstek sayısına göre artan gecikme uygular.
    Çok fazla istek atıldığında otomatik olarak yavaşlar.
    
    Args:
        request_count: Şu ana kadar yapılan istek sayısı
        base_delay: Temel bekleme süresi
    """
    if request_count > 50:
        delay = base_delay * 3
    elif request_count > 20:
        delay = base_delay * 2
    else:
        delay = base_delay
    
    # Rastgele jitter ekle (uniform olmayan davranış)
    jitter = random.uniform(0, delay * 0.5)
    time.sleep(delay + jitter)


# ============================================================
# HTTP HEADERS
# ============================================================

# Yaygın User-Agent'lar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]


def get_random_headers() -> dict:
    """
    Rastgele User-Agent ile HTTP headers döndürür.
    Her istekte farklı bir tarayıcı gibi görünmemizi sağlar.
    
    Returns:
        HTTP headers sözlüğü
    """
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        # "br" (Brotli) kasıtlı olarak dışarıda bırakıldı: requests/urllib3,
        # "brotli" paketi kurulu değilse br ile sıkıştırılmış yanıtı açamaz
        # ve BeautifulSoup'a ham (binary) veri gider. gzip/deflate stdlib'de var.
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }


def get_json_headers() -> dict:
    """
    JSON API istekleri için headers döndürür.
    
    Returns:
        JSON-uyumlu HTTP headers sözlüğü
    """
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
    }


# ============================================================
# VERİ KAYDETME (EXPORT)
# ============================================================

def get_data_dir() -> str:
    """Data klasörünün yolunu döndürür ve yoksa oluşturur."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def save_to_json(data: list[dict], filename: str, subdir: str = "") -> str:
    """
    Veriyi JSON formatında kaydeder.
    
    Args:
        data: Kaydedilecek veri listesi
        filename: Dosya adı (.json uzantısı otomatik eklenir)
        subdir: data/ altındaki alt klasör (opsiyonel)
    
    Returns:
        Kaydedilen dosyanın tam yolu
    """
    data_dir = get_data_dir()
    if subdir:
        data_dir = os.path.join(data_dir, subdir)
        os.makedirs(data_dir, exist_ok=True)
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(data_dir, filename)
    
    output = {
        "metadata": {
            "scrape_date": datetime.now().isoformat(),
            "total_items": len(data),
            "source": filename.replace('.json', ''),
        },
        "data": data
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"{Fore.GREEN}✅ JSON kaydedildi: {filepath} ({len(data)} kayıt){Style.RESET_ALL}")
    return filepath


def save_to_csv(data: list[dict], filename: str, subdir: str = "") -> str:
    """
    Veriyi CSV formatında kaydeder.
    
    Args:
        data: Kaydedilecek veri listesi (dict listesi)
        filename: Dosya adı (.csv uzantısı otomatik eklenir)
        subdir: data/ altındaki alt klasör (opsiyonel)
    
    Returns:
        Kaydedilen dosyanın tam yolu
    """
    if not data:
        print(f"{Fore.RED}❌ CSV kaydedilemedi: Boş veri{Style.RESET_ALL}")
        return ""
    
    data_dir = get_data_dir()
    if subdir:
        data_dir = os.path.join(data_dir, subdir)
        os.makedirs(data_dir, exist_ok=True)
    
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"{Fore.GREEN}✅ CSV kaydedildi: {filepath} ({len(data)} kayıt){Style.RESET_ALL}")
    return filepath


# ============================================================
# SCRAPING SONUÇ ÖZETİ
# ============================================================

def print_summary(scraper_name: str, total_items: int, elapsed_time: float, 
                  pages_scraped: int = 0, errors: int = 0) -> None:
    """
    Scraping işlemi sonunda özet bilgi yazdırır.
    
    Args:
        scraper_name: Scraper'ın adı
        total_items: Toplam çekilen öğe sayısı
        elapsed_time: Geçen süre (saniye)
        pages_scraped: Taranan sayfa sayısı
        errors: Hata sayısı
    """
    print(f"\n{'='*60}")
    print(f"{Fore.CYAN}📊 SCRAPING ÖZETİ: {scraper_name}{Style.RESET_ALL}")
    print(f"{'='*60}")
    print(f"  {'📦 Toplam Öğe:':<25} {Fore.GREEN}{total_items}{Style.RESET_ALL}")
    if pages_scraped:
        print(f"  {'📄 Taranan Sayfa:':<25} {Fore.GREEN}{pages_scraped}{Style.RESET_ALL}")
    print(f"  {'⏱️  Geçen Süre:':<25} {Fore.YELLOW}{elapsed_time:.2f} saniye{Style.RESET_ALL}")
    if total_items > 0 and elapsed_time > 0:
        rate = total_items / elapsed_time
        print(f"  {'🚀 Hız:':<25} {Fore.YELLOW}{rate:.1f} öğe/saniye{Style.RESET_ALL}")
    if errors:
        print(f"  {'❌ Hatalar:':<25} {Fore.RED}{errors}{Style.RESET_ALL}")
    print(f"{'='*60}\n")


# ============================================================
# GENEL YARDIMCI
# ============================================================

def ensure_dir(path: str) -> str:
    """Klasörün var olduğundan emin olur, yoksa oluşturur."""
    os.makedirs(path, exist_ok=True)
    return path


def clean_text(text: str) -> str:
    """
    Metni temizler: fazla boşlukları kaldırır, strip eder.
    
    Args:
        text: Temizlenecek metin
    
    Returns:
        Temizlenmiş metin
    """
    if not text:
        return ""
    return " ".join(text.split()).strip()
