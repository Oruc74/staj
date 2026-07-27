"""
robots.txt Kontrol Aracı
=========================
Herhangi bir sitenin robots.txt dosyasını okuyup analiz eder.
Scraping yapılabilir/yapılamaz path'leri raporlar.

Kullanım:
    python robots_checker.py https://books.toscrape.com
    python robots_checker.py https://quotes.toscrape.com
"""

import sys
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from colorama import Fore, Style, init
import requests

# Windows konsolu varsayılan olarak cp1254/cp1252 gibi kod sayfaları kullanır,
# bu da emoji içeren print() çağrılarında UnicodeEncodeError'a yol açar.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

init(autoreset=True)

# Bazı siteler (ör. Wikipedia) varsayılan "python-requests/x.x" User-Agent'ını
# robots.txt istekleri için bile 403 ile reddediyor; tarayıcı benzeri bir UA
# gönderiyoruz.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}


def check_robots(url: str, user_agent: str = "*") -> dict:
    """
    Bir sitenin robots.txt dosyasını okur ve analiz eder.
    
    Args:
        url: Kontrol edilecek sitenin URL'si
        user_agent: Kontrol edilecek user agent (varsayılan: *)
    
    Returns:
        Analiz sonuçlarını içeren sözlük
    """
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base_url}/robots.txt"
    
    result = {
        "url": base_url,
        "robots_url": robots_url,
        "exists": False,
        "raw_content": "",
        "allowed_paths": [],
        "disallowed_paths": [],
        "sitemaps": [],
        "crawl_delay": None,
    }
    
    print(f"\n{Fore.CYAN}🤖 robots.txt Kontrol Ediliyor: {robots_url}{Style.RESET_ALL}")
    print(f"{'─'*60}")
    
    try:
        response = requests.get(robots_url, headers=REQUEST_HEADERS, timeout=10)
        
        if response.status_code == 200:
            result["exists"] = True
            result["raw_content"] = response.text
            
            print(f"{Fore.GREEN}✅ robots.txt BULUNDU{Style.RESET_ALL}\n")
            
            # RobotFileParser ile parse et.
            # NOT: rp.read() KULLANMIYORUZ — RobotFileParser dahili olarak
            # urllib.request ile varsayılan Python User-Agent'ı kullanır ve
            # bazı siteler (ör. Wikipedia) bunu 403 ile reddeder. Bu durumda
            # RobotFileParser sessizce "hiçbir şeye izin yok" varsayar ve
            # can_fetch() her path için yanlışlıkla False döner. Bunun yerine,
            # zaten doğru User-Agent ile çektiğimiz içeriği doğrudan besliyoruz.
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.parse(response.text.splitlines())
            
            # Crawl delay kontrolü
            try:
                delay = rp.crawl_delay(user_agent)
                if delay:
                    result["crawl_delay"] = delay
            except Exception:
                pass
            
            # İçeriği satır satır analiz et
            current_agent = None
            for line in response.text.splitlines():
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if line.lower().startswith('user-agent:'):
                    current_agent = line.split(':', 1)[1].strip()
                elif line.lower().startswith('disallow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        result["disallowed_paths"].append({
                            "path": path,
                            "user_agent": current_agent or "*"
                        })
                elif line.lower().startswith('allow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        result["allowed_paths"].append({
                            "path": path,
                            "user_agent": current_agent or "*"
                        })
                elif line.lower().startswith('sitemap:'):
                    sitemap = line.split(':', 1)[1].strip()
                    # 'Sitemap: https://...' formatında "https" kısmını kaybetmemek için
                    if not sitemap.startswith('http'):
                        sitemap = line.split(' ', 1)[1].strip()
                    result["sitemaps"].append(sitemap)
            
            # Sonuçları yazdır
            _print_analysis(result, user_agent, rp, base_url)
            
        elif response.status_code == 404:
            result["exists"] = False
            print(f"{Fore.YELLOW}⚠️  robots.txt BULUNAMADI (404)")
            print(f"   → Site scraping konusunda kısıtlama belirtmemiş{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Beklenmeyen yanıt: HTTP {response.status_code}{Style.RESET_ALL}")
            
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}❌ Bağlantı hatası: {e}{Style.RESET_ALL}")
    
    return result


def _print_analysis(result: dict, user_agent: str, rp: RobotFileParser, base_url: str) -> None:
    """Analiz sonuçlarını renkli olarak yazdırır."""
    
    # Yasaklı path'ler
    if result["disallowed_paths"]:
        print(f"{Fore.RED}🚫 YASAKLI PATH'LER:{Style.RESET_ALL}")
        for item in result["disallowed_paths"]:
            agent_info = f" (User-Agent: {item['user_agent']})" if item['user_agent'] != '*' else ""
            print(f"   ✗ {item['path']}{agent_info}")
    else:
        print(f"{Fore.GREEN}✅ Hiçbir path yasaklanmamış!{Style.RESET_ALL}")
    
    # İzin verilen path'ler
    if result["allowed_paths"]:
        print(f"\n{Fore.GREEN}✅ AÇIKÇA İZİN VERİLEN PATH'LER:{Style.RESET_ALL}")
        for item in result["allowed_paths"]:
            print(f"   ✓ {item['path']}")
    
    # Crawl delay
    if result["crawl_delay"]:
        print(f"\n{Fore.YELLOW}⏱️  Crawl Delay: {result['crawl_delay']} saniye{Style.RESET_ALL}")
    
    # Sitemap'ler
    if result["sitemaps"]:
        print(f"\n{Fore.CYAN}🗺️  SITEMAP'LER:{Style.RESET_ALL}")
        for sm in result["sitemaps"]:
            print(f"   → {sm}")
    
    # Örnek path kontrolü
    print(f"\n{Fore.CYAN}📋 ÖRNEK PATH KONTROLLERİ:{Style.RESET_ALL}")
    test_paths = ["/", "/search", "/api/", "/admin/", "/sitemap.xml"]
    for path in test_paths:
        full_url = f"{base_url}{path}"
        can_fetch = rp.can_fetch(user_agent, full_url)
        status = f"{Fore.GREEN}✅ İZİNLİ" if can_fetch else f"{Fore.RED}🚫 YASAK"
        print(f"   {path:<20} → {status}{Style.RESET_ALL}")


def check_multiple_sites(urls: list[str]) -> None:
    """Birden fazla siteyi toplu olarak kontrol eder."""
    print(f"\n{'='*60}")
    print(f"{Fore.CYAN}🔍 TOPLU ROBOTS.TXT KONTROLÜ ({len(urls)} site){Style.RESET_ALL}")
    print(f"{'='*60}")
    
    for url in urls:
        check_robots(url)
        print()


# ============================================================
# ANA ÇALIŞTIRMA
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Komut satırından URL verilmişse onu kontrol et
        target_url = sys.argv[1]
        check_robots(target_url)
    else:
        # Varsayılan: Projede kullanacağımız tüm siteleri kontrol et
        sites = [
            "https://books.toscrape.com",
            "https://quotes.toscrape.com",
            "https://en.wikipedia.org",
            "https://webscraper.io",
            "https://news.ycombinator.com",
        ]
        check_multiple_sites(sites)
