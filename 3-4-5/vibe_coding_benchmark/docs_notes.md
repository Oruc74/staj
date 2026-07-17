# 📖 Cursor Profesyonel Kullanım Notları

> **Tarih:** Temmuz 2026  
> **Cursor Sürümü:** En güncel kararlı sürüm  
> **Amaç:** Cursor'ı temel düzeyden ileri düzeye kadar etkin kullanmak için kapsamlı referans

---

## 📋 İçindekiler

1. [.cursorrules Dosyası](#cursorrules-dosyası)
2. [MCP (Model Context Protocol) Entegrasyonları](#mcp-model-context-protocol-entegrasyonları)
3. [Hooks Sistemi](#hooks-sistemi)
4. [Context Management](#context-management)
5. [Agent Mode vs Chat Mode](#agent-mode-vs-chat-mode)
6. [Klavye Kısayolları](#klavye-kısayolları)
7. [Composer (Çoklu Dosya Düzenleme)](#composer-çoklu-dosya-düzenleme)
8. [Background Agents](#background-agents)
9. [Beginner → Power User Yol Haritası](#beginner--power-user-yol-haritası)
10. [Docs Okuma Alışkanlığı](#docs-okuma-alışkanlığı)

---

## .cursorrules Dosyası

### Nedir?

`.cursorrules` dosyası, Cursor AI'ın proje bazında nasıl davranacağını tanımlayan bir konfigürasyon dosyasıdır. Projenin kök dizinine yerleştirilir ve Cursor her AI etkileşiminde bu kuralları otomatik olarak context'e dahil eder.

Bu, **context engineering**'in en temel ve en güçlü uygulamasıdır: AI'a "ben kimim, bu proje ne, nasıl çalışmalıyız" bilgisini sistematik olarak veriyorsun.

> **Not:** Cursor, `.cursor/rules/` dizininde birden fazla kural dosyası oluşturmayı da destekler. Bu dosyalar belirli glob pattern'lerine göre otomatik eklenir (ör. `*.py` dosyaları için ayrı kurallar). Bu daha gelişmiş bir yaklaşımdır.

### Nasıl Yazılır?

Proje kök dizinine `.cursorrules` dosyası oluştur:

```markdown
# Proje: Web Scraping Staj Projesi

## Genel Kurallar
- Tüm yorum ve docstring'leri Türkçe yaz
- PEP 8 standartlarına uy
- Her fonksiyona type hint ekle
- Comprehensive error handling kullan (try/except)
- Her script if __name__ == "__main__" bloğu içermeli

## Teknoloji Yığını
- Python 3.11+
- requests, BeautifulSoup4, Selenium (web scraping)
- pandas (veri işleme)
- colorama (terminal renklendirme)
- pytest (test)

## Proje Yapısı
- `utils/helpers.py` → ortak yardımcı fonksiyonlar (setup_logger, save_to_json, save_to_csv, vb.)
- `scrapers/` → her site için ayrı scraper dosyası
- `data/` → kazınan veriler (JSON ve CSV)
- `tests/` → test dosyaları

## Kodlama Standartları
- Logger kullan, print yerine logging tercih et
- Her scraper'da timing measurement olsun (time.time())
- colorama ile renkli terminal çıktısı ver
- Veriler hem JSON hem CSV olarak kaydedilmeli
- Random delay kullanarak hedef siteye nazik ol (polite scraping)

## İsimlendirme
- Fonksiyonlar: snake_case (ör. scrape_products, parse_detail_page)
- Sınıflar: PascalCase (ör. BookScraper, ProductParser)
- Sabitler: UPPER_SNAKE_CASE (ör. BASE_URL, MAX_RETRIES)
- Dosyalar: snake_case (ör. book_scraper.py, helpers.py)

## Yapılmaması Gerekenler
- Global değişken kullanma
- Bare except kullanma (her zaman spesifik exception yakala)
- API anahtarlarını koda hardcode etme
- Sonsuz döngü oluşturma (her zaman max iteration sınırı koy)

## Git
- Commit mesajları Türkçe ve açıklayıcı olsun
- Her yeni özellik ayrı commit olsun
```

### Gelişmiş: Dizin Bazlı Kurallar

`.cursor/rules/` dizininde farklı dosya tipleri için özel kurallar:

**`.cursor/rules/python-rules.mdc`**
```markdown
---
description: Python dosyaları için kurallar
globs: ["**/*.py"]
---

# Python Kuralları
- Type hint'leri zorunlu kullan
- Docstring formatı: Google style
- Import sıralaması: stdlib → third-party → local
- f-string tercih et (.format() veya % yerine)
```

**`.cursor/rules/test-rules.mdc`**
```markdown
---
description: Test dosyaları için kurallar
globs: ["tests/**/*.py", "**/test_*.py"]
---

# Test Kuralları
- pytest kullan (unittest değil)
- Her test fonksiyonu test_ ile başlamalı
- fixture'lar conftest.py'da tanımlanmalı
- Mock kullanırken unittest.mock tercih et
- Her test tek bir davranışı test etmeli
```

### İpuçları

1. **Kısa ve öz tut:** Çok uzun kurallar token bütçesini yer. En kritik kuralları yaz.
2. **Örnekle göster:** "Şöyle yaz" demek yerine, kısa bir kod örneği ver.
3. **Güncel tut:** Proje evrildikçe kuralları güncelle.
4. **Takımla paylaş:** `.cursorrules` dosyasını git'e commit'le, takımın aynı standartları kullansın.
5. **Negatif kurallar:** "Yapma" kuralları da çok etkili — AI'ın bilinen hatalarını önler.

---

## MCP (Model Context Protocol) Entegrasyonları

### MCP Nedir?

MCP (Model Context Protocol), AI modellerinin harici araçlar ve veri kaynaklarıyla standart bir şekilde iletişim kurmasını sağlayan açık bir protokoldür. Anthropic tarafından başlatılmış ve 2026'da endüstri standardı haline gelmiştir.

Basit bir analoji: MCP, AI için bir **USB standardı** gibidir. Nasıl USB sayesinde herhangi bir cihazı herhangi bir bilgisayara bağlayabiliyorsan, MCP sayesinde herhangi bir veri kaynağını herhangi bir AI aracına bağlayabilirsin.

### Cursor'da MCP Konfigürasyonu

MCP sunucuları `~/.cursor/mcp.json` (global) veya `.cursor/mcp.json` (proje bazlı) dosyasından konfigüre edilir:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxx"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

### Kullanılabilir MCP Sunucuları

| MCP Sunucusu | Ne İşe Yarar | Kullanım Senaryosu |
|--------------|-------------|-------------------|
| **GitHub** | GitHub API erişimi (repo, issue, PR) | "Bu repo'daki açık issue'ları listele ve bir tanesini çöz" |
| **PostgreSQL** | Veritabanı şema ve sorgu erişimi | "Users tablosunun yapısına bak ve bir sorgu yaz" |
| **Figma** | Figma tasarımlarına erişim | "Bu Figma tasarımını React bileşenine çevir" |
| **Firecrawl** | Web sayfası scraping ve crawling | "Bu URL'deki içeriği oku ve özetle" |
| **Puppeteer** | Tarayıcı otomasyonu | "Bu sayfayı aç, screenshot al, form doldur" |
| **Slack** | Slack mesajları ve kanalları | "Slack'teki #dev kanalındaki son mesajları oku" |
| **Filesystem** | Dosya sistemi erişimi | "Şu dizindeki dosyaları listele ve analiz et" |
| **SQLite** | SQLite veritabanı erişimi | "Bu SQLite DB'deki tabloları incele" |
| **Memory** | Kalıcı bellek / knowledge graph | "Bu bilgiyi hatırla ve sonra kullan" |
| **Brave Search** | Web araması | "Bu konu hakkında güncel bilgi ara" |
| **Sentry** | Hata izleme | "Son hataları göster ve çözüm öner" |
| **Linear/Jira** | Proje yönetimi | "Sprint'teki görevleri listele" |

### MCP Kurulum Adımları

1. **Node.js gerekli:** MCP sunucuları genellikle Node.js üzerinde çalışır. `node` ve `npx` yüklü olmalı.
2. **Konfigürasyon dosyası oluştur:** `.cursor/mcp.json`
3. **Cursor'ı yeniden başlat:** MCP sunucuları başlangıçta yüklenir.
4. **Test et:** Agent mode'da MCP araçlarını kullanmayı dene.

### Güvenlik Notları

- API anahtarlarını `.env` dosyasında tut, `.cursor/mcp.json`'a direkt yazma
- `.cursor/mcp.json`'u `.gitignore`'a ekle (hassas bilgi içeriyorsa)
- MCP sunucularının erişim kapsamını sınırla (ör. filesystem sunucusuna sadece proje dizinini ver)
- Üçüncü parti MCP sunucularını kullanmadan önce kaynak kodunu incele

---

## Hooks Sistemi

### Hooks Nedir?

Hooks, Cursor'ın AI işlemleri öncesinde ve sonrasında otomatik olarak çalıştırılan komutlardır. Bu sistem, **"Vibe & Verify"** yaklaşımının teknik uygulamasıdır: AI kod yazarken, arka planda otomatik olarak kalite kontrolleri çalışır.

### Hook Türleri

| Hook | Ne Zaman Çalışır | Kullanım Amacı |
|------|-------------------|----------------|
| **SessionStart** | Yeni bir AI oturumu başladığında | Ortam hazırlığı, bağımlılık kontrolü |
| **PreToolUse** | AI bir araç kullanmadan önce (dosya yazma, komut çalıştırma) | Güvenlik kontrolü, izin doğrulama |
| **PostToolUse** | AI bir araç kullandıktan sonra | Otomatik lint, test, format |
| **Stop** | AI oturumu tamamlandığında | Temizlik, özet rapor, commit |

### Konfigürasyon

Hooks, `.cursor/hooks/` dizininde veya Cursor ayarlarından konfigüre edilir:

**Örnek: Otomatik Lint (PostToolUse)**

`.cursor/hooks/post-edit-lint.sh`
```bash
#!/bin/bash
# Dosya düzenlendikten sonra otomatik lint çalıştır

# Sadece Python dosyaları için çalış
if [[ "$CURSOR_FILEPATH" == *.py ]]; then
    echo "🔍 Lint kontrolü yapılıyor: $CURSOR_FILEPATH"
    
    # flake8 ile lint
    flake8 "$CURSOR_FILEPATH" --max-line-length=120 --ignore=E501,W503
    
    # Hata varsa bildir
    if [ $? -ne 0 ]; then
        echo "⚠️ Lint hataları bulundu!"
    else
        echo "✅ Lint temiz!"
    fi
fi
```

**Örnek: Otomatik Test (PostToolUse)**

`.cursor/hooks/post-edit-test.sh`
```bash
#!/bin/bash
# Dosya düzenlendikten sonra ilgili testleri çalıştır

if [[ "$CURSOR_FILEPATH" == *.py ]]; then
    # Test dosyası varsa çalıştır
    TEST_FILE="tests/test_$(basename $CURSOR_FILEPATH)"
    
    if [ -f "$TEST_FILE" ]; then
        echo "🧪 Testler çalıştırılıyor: $TEST_FILE"
        python -m pytest "$TEST_FILE" -v --tb=short
    fi
fi
```

**Örnek: SessionStart Hook**

`.cursor/hooks/session-start.sh`
```bash
#!/bin/bash
# Oturum başlangıcında ortamı kontrol et

echo "🚀 Cursor AI oturumu başlıyor..."
echo "📁 Proje: $(basename $(pwd))"
echo "🐍 Python: $(python --version 2>&1)"
echo "📦 Sanal ortam: ${VIRTUAL_ENV:-'Aktif değil'}"

# Gerekli bağımlılıkları kontrol et
if [ -f "requirements.txt" ]; then
    pip check 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️ Bağımlılık sorunları var! 'pip install -r requirements.txt' çalıştırın."
    fi
fi
```

### Windows PowerShell Hooks

Windows kullanıcıları için PowerShell versiyonları:

**Post-edit lint (PowerShell):**
```powershell
# post-edit-lint.ps1
param($FilePath)

if ($FilePath -match '\.py$') {
    Write-Host "🔍 Lint kontrolü: $FilePath" -ForegroundColor Cyan
    python -m flake8 $FilePath --max-line-length=120
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Lint temiz!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Lint hataları bulundu!" -ForegroundColor Yellow
    }
}
```

### Hook'ların Faydaları

1. **Otomatik kalite kontrolü:** Her AI düzenlemesinden sonra lint/test çalışır
2. **Güvenlik:** AI'ın tehlikeli komut çalıştırmasını engelleyebilirsin
3. **Tutarlılık:** Code format her zaman standart kalır
4. **Erken hata tespiti:** Sorunlar büyümeden yakalanır
5. **"Verify" otomasyonu:** Vibe & Verify'ın "verify" kısmını otomatikleştirir

---

## Context Management

### @-Mentions ile Referans Sistemi

Cursor'da `@` sembolü ile çeşitli kaynaklara doğrudan referans verebilirsin. Bu, AI'a doğru bağlamı sağlamanın en hızlı yoludur.

| Mention Türü | Sözdizimi | Ne Yapar |
|--------------|-----------|----------|
| **Dosya** | `@filename.py` | Belirtilen dosyanın içeriğini context'e ekler |
| **Klasör** | `@src/utils/` | Klasör yapısını ve içeriklerini gösterir |
| **Sembol** | `@functionName` | Fonksiyon/sınıf tanımını bulur ve ekler |
| **Web** | `@url` | URL içeriğini okur ve context'e ekler |
| **Docs** | `@docs` | Cursor'ın indekslediği dokümantasyon |
| **Codebase** | `@codebase` | Tüm proje üzerinde arama yapar |
| **Git** | `@git` | Git geçmişi ve değişiklikleri |
| **Definitions** | `@definitions` | Seçili kodun tüm tanımlarını bulur |
| **Recent files** | `@recent` | Son düzenlenen dosyalar |

### Kullanım Örnekleri

```
# Belirli bir dosyayı referans vererek soru sormak
@helpers.py bu dosyadaki save_to_json fonksiyonunu CSV desteği ekleyecek şekilde güncelle

# Birden fazla dosya ile çalışmak
@book_scraper.py ve @helpers.py dosyalarına bakarak, scraper'ın çıktı formatını düzelt

# Codebase genelinde arama
@codebase projede retry mekanizması kullanan tüm yerleri bul

# Web dokümantasyonuna referans
@https://docs.python.org/3/library/asyncio.html bu dokümana bakarak async scraper yaz

# Git değişikliklerine referans
@git son 3 commit'te ne değişti?
```

### Codebase Indexing

Cursor, projenin tamamını indeksleyerek AI'ın tüm kodu anlamasını sağlar.

**Nasıl çalışır:**
1. Cursor projeyi açtığında otomatik indeksleme başlar
2. Dosya değişikliklerinde indeks güncellenir
3. `@codebase` ile tüm proje üzerinde anlamlı arama yapılabilir
4. AI, sadece açık dosyaları değil, projenin genel yapısını anlayabilir

**İndeksleme durumunu kontrol etmek:**
- Cursor'ın sağ alt köşesindeki indeksleme göstergesine bak
- `Cursor Settings > Features > Codebase Indexing` ayarlarını kontrol et

### .cursorignore

İndekslemeye dahil edilmemesi gereken dosya/dizinleri belirlemek için `.cursorignore` dosyası kullanılır (`.gitignore` sözdizimiyle aynı):

```gitignore
# .cursorignore

# Büyük veri dosyaları (indexing'i yavaşlatır)
data/
*.csv
*.json

# Bağımlılıklar
node_modules/
venv/
.venv/
__pycache__/

# Build çıktıları
dist/
build/
*.egg-info/

# Hassas dosyalar
.env
*.key
*.pem
secrets/

# IDE dosyaları
.idea/
.vscode/

# Log dosyaları
*.log
logs/
```

### Context Yönetimi İpuçları

1. **Az ama öz context:** Çok fazla dosya eklemek yerine, ilgili dosyaları hedefli olarak ekle
2. **Önemli dosyaları pin'le:** Sık kullanılan dosyaları context'te sabit tut
3. **@codebase'i stratejik kullan:** Genel sorularda kullan, spesifik sorularda direkt dosya referansı ver
4. **Dokümantasyon referansı:** Harici kütüphane kullanırken @url ile dokümanı context'e ekle
5. **.cursorignore'u güncel tut:** Gereksiz dosyaları indeksten çıkar, hem hız kazandırır hem doğruluğu artırır

---

## Agent Mode vs Chat Mode

### Ne Zaman Hangisi?

| Özellik | Chat Mode (⌘L / Ctrl+L) | Agent Mode (⌘I / Ctrl+I) |
|---------|--------------------------|---------------------------|
| **Amaç** | Soru-cevap, açıklama, küçük düzenleme | Otonom görev tamamlama |
| **Dosya düzenleme** | Öneri verir, onayını bekler | Doğrudan düzenler (izinle) |
| **Çoklu dosya** | Manuel olarak dosya eklemen gerekir | Otomatik olarak ilgili dosyaları bulur |
| **Komut çalıştırma** | Önerir ama çalıştırmaz | Terminal komutları çalıştırabilir |
| **Maliyet** | Düşük (kısa yanıtlar) | Yüksek (çok adımlı, çok dosyalı) |
| **Kontrol** | Tam kontrol sende | Daha fazla otonomi AI'da |

### Chat Mode İçin İdeal Senaryolar

```
✅ "Bu fonksiyon ne yapıyor?" → Açıklama iste
✅ "Bu hata ne anlama geliyor?" → Debug yardımı
✅ "Bu kodu optimize et" → Tek dosya düzenleme
✅ "Regular expression yaz: email validation" → Küçük kod parçası
✅ "Python'da async/await nasıl çalışır?" → Öğrenme/soru
✅ "Bu SQL sorgusunu açıkla" → Analiz
```

### Agent Mode İçin İdeal Senaryolar

```
✅ "Yeni bir web scraper yaz: X sitesini tara, JSON'a kaydet" → Çoklu dosya oluşturma
✅ "Bu projeye test ekle" → Birden fazla test dosyası oluşturma
✅ "Hata mesajını düzelt ve tüm etkilenen dosyaları güncelle" → Çoklu dosya düzenleme
✅ "requirements.txt'i güncelle ve bağımlılıkları yükle" → Komut çalıştırma + dosya düzenleme
✅ "Bu API'ye endpoint ekle ve dokümantasyonunu yaz" → Kapsamlı görev
✅ "Projeyi refactor et: helper fonksiyonları ayrı modüle taşı" → Yapısal değişiklik
```

### İpuçları

1. **Küçük başla, büyüt:** Emin değilsen Chat ile başla, gerekirse Agent'a geç
2. **Agent'a net talimat ver:** "Bir şeyler yap" yerine "X dosyasında Y fonksiyonunu Z şekilde değiştir" de
3. **Agent diff'lerini incele:** Agent'ın yaptığı değişiklikleri kabul etmeden önce diff'leri gözden geçir
4. **Maliyet bilinci:** Agent mode çok daha fazla token tüketir; basit sorular için Chat yeterli
5. **Iteratif çalış:** Büyük bir görevi tek seferde Agent'a vermek yerine, küçük adımlara böl

---

## Klavye Kısayolları

### En Sık Kullanılanlar

| Kısayol (Windows/Linux) | Kısayol (macOS) | İşlev |
|--------------------------|-----------------|-------|
| `Ctrl + L` | `⌘ + L` | Chat panelini aç |
| `Ctrl + I` | `⌘ + I` | Composer/Agent panelini aç |
| `Ctrl + K` | `⌘ + K` | Inline edit (seçili kodu düzenle) |
| `Tab` | `Tab` | AI completion'ı kabul et |
| `Esc` | `Esc` | AI completion'ı reddet |
| `Ctrl + Shift + L` | `⌘ + Shift + L` | Seçili kodu Chat'e ekle |
| `Ctrl + Shift + K` | `⌘ + Shift + K` | Satırı sil |
| `Ctrl + Enter` | `⌘ + Enter` | Chat'te mesaj gönder |
| `Ctrl + /` | `⌘ + /` | Yorum satırı toggle |
| `Ctrl + Shift + I` | `⌘ + Shift + I` | Background Agent başlat |

### Verimlilik İpuçları

1. **Tab akışı:** Kod yazarken Tab tuşuna hafifçe basarak AI önerilerini hızlıca kabul et. Ret için Esc.
2. **Inline edit:** Bir kod bloğunu seç → `Ctrl+K` → ne istediğini yaz → Enter. Hızlı düzenleme için ideal.
3. **Chat'e kod gönder:** Bir kodu anlamak istiyorsan seç → `Ctrl+Shift+L` → soru sor.
4. **Multi-cursor:** `Alt+Click` ile birden fazla cursor oluşturup toplu düzenleme yap (bu VS Code özelliği ama Cursor'da da çalışıyor).

---

## Composer (Çoklu Dosya Düzenleme)

### Nedir?

Composer, Cursor'ın çoklu dosya üzerinde aynı anda çalışma yeteneğidir. Agent mode ile birlikte kullanıldığında, bir talimatla birden fazla dosyayı oluşturabilir, düzenleyebilir veya refactor edebilirsin.

### Kullanım Senaryoları

**1. Yeni Proje İskeleti Oluşturma:**
```
Composer'a söyle:
"Python web scraping projesi oluştur:
- main.py (ana script)
- scrapers/base_scraper.py (temel sınıf)
- scrapers/book_scraper.py (kitap scraper)
- utils/helpers.py (yardımcı fonksiyonlar)
- tests/test_book_scraper.py (testler)
- requirements.txt
- README.md

Her dosyayı uygun içerikle doldur."
```

**2. Refactoring:**
```
"helpers.py'daki save fonksiyonlarını ayrı bir io_utils.py modülüne taşı
ve tüm import'ları güncelle"
```

**3. Özellik Ekleme:**
```
"Tüm scraper'lara retry mekanizması ekle:
- utils/retry.py oluştur (decorator pattern)
- Mevcut scraper'ları güncelle
- Test ekle"
```

### Composer İpuçları

1. **Açık dosya listesi ver:** Hangi dosyaların etkileneceğini belirt
2. **Sıralama belirt:** "Önce X'i oluştur, sonra Y'yi güncelle" gibi
3. **Diff review:** Composer'ın önerdiği değişiklikleri dosya dosya incele
4. **Kısmi kabul:** Bazı dosyalardaki değişiklikleri kabul edip diğerlerini reddedebilirsin
5. **Iteratif refinement:** İlk sonuç mükemmel olmayabilir — "ayrıca şunu da ekle" diyerek refine et

---

## Background Agents

### Nedir?

Background Agents, Cursor'ın arka planda otonom olarak çalışan AI agent'larıdır. Bir görevi arka plana atarsın, sen başka bir şeyle ilgilenirken agent görevi tamamlar ve sonucu bildirir.

### Nasıl Kullanılır?

1. `Ctrl + Shift + I` ile Background Agent panelini aç
2. Görevi tanımla (ör. "Bu PR'daki tüm linting hatalarını düzelt")
3. Agent arka planda çalışmaya başlar
4. Tamamlandığında bildirim alırsın
5. Sonuçları incele ve onayla

### İdeal Kullanım Senaryoları

| Senaryo | Açıklama |
|---------|----------|
| **PR Hazırlama** | "Bu branch'teki değişiklikleri temizle, testleri çalıştır, PR açıklaması yaz" |
| **Bug Fix** | "Bu hata raporunu al ve çöz" — sen başka bir şeyle ilgilen |
| **Test Yazma** | "Bu modüldeki tüm fonksiyonlar için unit test yaz" |
| **Dokümantasyon** | "Projenin README'sini ve API dokümantasyonunu güncelle" |
| **Dependency Update** | "Bağımlılıkları güncelle ve uyumluluk sorunlarını çöz" |

### Dikkat Edilmesi Gerekenler

- Background agent'lar premium istek kotasından düşer
- Karmaşık görevlerde agent yanlış yöne gidebilir — sonuçları mutlaka incele
- Git branch kullanarak agent'ın değişikliklerini izole et
- Hassas dosyalarda (konfigürasyon, güvenlik) dikkatli ol

---

## Beginner → Power User Yol Haritası

### 🌱 Seviye 1: Başlangıç (1-2 Hafta)

**Hedef:** Cursor'ın temel özelliklerine alışmak

- [ ] Cursor'ı indir ve kur
- [ ] VS Code eklentilerini Cursor'a taşı
- [ ] Tab completion ile kod yazma pratiği yap
- [ ] `Ctrl+L` (Chat) ile basit sorular sor
- [ ] `Ctrl+K` (Inline Edit) ile küçük düzenlemeler yap
- [ ] Kısayol listesini öğren ve pratik yap

**Bu seviyede yapılmaması gereken:**
- Agent mode'a atlamak (önce Chat'i öğren)
- Her şeyi AI'a yazdırmak (önce kendin dene, sonra AI'dan yardım iste)

---

### 🌿 Seviye 2: Orta (2-4 Hafta)

**Hedef:** Context engineering ve Agent mode'u etkin kullanmak

- [ ] `.cursorrules` dosyası oluştur ve projene özelleştir
- [ ] `@` mentions kullanarak dosya/sembol referansı vermeyi öğren
- [ ] Agent mode (`Ctrl+I`) ile çoklu dosya görevleri çöz
- [ ] Composer ile proje iskeleti oluştur
- [ ] `.cursorignore` dosyası oluştur
- [ ] AI'ın önerdiği kodu inceleme ve eleştirme alışkanlığı geliştir
- [ ] Diff review pratiği yap (değişiklikleri kabul etmeden incele)

**Bu seviyede öğrenilmesi gereken kavramlar:**
- Context window nedir, neden önemli
- Token maliyeti ve verimli prompt yazma
- "Küçük adımlarla iteratif geliştirme" yaklaşımı

---

### 🌳 Seviye 3: İleri (1-2 Ay)

**Hedef:** MCP, Hooks ve gelişmiş özelleştirmeler

- [ ] En az 2-3 MCP sunucusu kur ve kullan (GitHub, Filesystem, vb.)
- [ ] Hooks sistemi ile otomatik lint/test kur
- [ ] `.cursor/rules/` dizininde dosya tipine özel kurallar yaz
- [ ] Background Agents kullanmayı dene
- [ ] Git workflow'unu AI ile entegre et (branch, commit, PR)
- [ ] Farklı modelleri dene ve karşılaştır (Claude vs GPT vs Gemini)
- [ ] Codebase indexing'in nasıl çalıştığını anla ve optimize et

**Bu seviyede geliştirilmesi gereken alışkanlıklar:**
- AI'ın çıktısını her zaman test et (Vibe & Verify)
- Karmaşık görevleri küçük, doğrulanabilir adımlara böl
- AI ile "pair programming" yaklaşımını benimse

---

### 🏔️ Seviye 4: Power User (Sürekli)

**Hedef:** Cursor'ı iş akışının doğal bir parçası haline getirmek

- [ ] Özel MCP sunucusu yaz (kendi API'n veya veritabanın için)
- [ ] CI/CD pipeline'ında Cursor/AI entegrasyonu
- [ ] Takım için `.cursorrules` standardı oluştur
- [ ] Karmaşık multi-step agent görevleri tasarla
- [ ] Yeni Cursor özelliklerini çıktığı gün dene
- [ ] Toplulukta paylaşım yap (blog, video, Discord)
- [ ] Alternatif araçları da düzenli olarak dene (Claude Code, Cline)

**Power User alışkanlıkları:**
- Her hafta Cursor changelog'unu oku
- Yeni MCP sunucularını takip et
- Prompt/talimat kütüphanesi oluştur (sık kullanılan talimatları kaydet)
- Maliyet optimizasyonu yap (basit görevler için hızlı model, karmaşık görevler için güçlü model)

---

## Docs Okuma Alışkanlığı

### Neden Kritik?

Hocanın sürekli vurguladığı ve bu benchmark çalışmasında da doğrulanan bir gerçek:

> **"En güçlü AI aracını bile etkin kullanamazsın, eğer dokümantasyonunu okumadıysan."**

Bu basit ama çoğu geliştiricinin ihmal ettiği bir alışkanlık. İşte neden kritik olduğu:

### 1. Araçlar Sürekli Değişiyor

AI kodlama araçları haftalık güncelleme alıyor. 3 ay önceki bilgin güncel olmayabilir:
- Cursor her hafta yeni özellik ekliyor
- Model versiyonları değişiyor (Claude Sonnet 3.5 → 4, GPT-4 → 4.1)
- MCP ekosistemi hızla büyüyor
- Pricing ve kotalar değişebiliyor

**Çözüm:** Haftalık changelog takibi. Cursor'ın blog'unu ve Discord'unu takip et.

### 2. "Bilmediğin Şeyi Kullanamazsın"

Cursor'ın Hooks özelliğini bilmeyen bir kullanıcı, her AI düzenlemesinden sonra manuel lint çalıştırıyor olabilir. Background Agents'ı bilmeyen biri, CI görevlerini elle yapıyor olabilir. MCP'yi bilmeyen biri, veritabanı şemasını her seferinde kopyala-yapıştır yapıyor olabilir.

**Çözüm:** Docs'u baştan sona en az bir kez oku. Her bölümü kullanmasan bile, "böyle bir özellik varmış" bilgisi bile yeterli.

### 3. Öğrenme Kaynakları Hiyerarşisi

| Kaynak | Güvenilirlik | Güncellik | Derinlik |
|--------|-------------|-----------|----------|
| **Resmi Docs** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Resmi Blog/Changelog** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **GitHub Discussions** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Discord/Topluluk** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **YouTube Tutorials** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Twitter/X** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **ChatGPT'ye sormak** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

> **Kural:** Resmi docs her zaman birincil kaynak olmalı. YouTube ve blog yazıları tamamlayıcı. ChatGPT'ye "Cursor'ın X özelliği nasıl çalışır?" diye sormak yerine, önce docs'u oku.

### 4. Pratik Docs Okuma Stratejisi

1. **İlk kurulumda:** Docs'un "Getting Started" bölümünü baştan sona oku (~30 dakika)
2. **Haftalık:** Changelog'u tara (~5 dakika)
3. **Yeni özellik çıktığında:** İlgili docs bölümünü oku (~10 dakika)
4. **Sorun yaşadığında:** Önce docs'ta ara, bulamazsan toplulukta sor
5. **Aylık:** Docs'un tamamını bir kez daha gözden geçir — daha önce atladığın şeyleri farklı gözle göreceksin

### 5. Cursor Resmi Kaynaklar

| Kaynak | URL | Ne İçerir |
|--------|-----|-----------|
| **Docs** | docs.cursor.com | Kapsamlı dokümantasyon |
| **Blog** | cursor.com/blog | Yeni özellikler, vizyonlar |
| **Changelog** | cursor.com/changelog | Haftalık güncellemeler |
| **Forum** | forum.cursor.com | Topluluk tartışmaları |
| **Discord** | discord.gg/cursor | Gerçek zamanlı yardım |
| **GitHub** | github.com/getcursor | Issue tracker |
| **Twitter/X** | @cursor_ai | Duyurular, ipuçları |

### Son Söz

> *"Araçları kullanmayı öğrenmek, araçlarla üretmekten daha önemlidir. Docs okumak, prompt yazmaktan daha temeldir. Çünkü doğru aracı, doğru şekilde kullanmayı bilmeden, ne kadar iyi prompt yazarsan yaz, potansiyelin sınırlı kalır."*
> 
> — Staj notlarından

---

### Hızlı Referans Kartı

```
╔══════════════════════════════════════════════════════════╗
║                 CURSOR HIZLI REFERANS                    ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Chat:        Ctrl+L    │  Agent:       Ctrl+I           ║
║  Inline Edit: Ctrl+K    │  Background:  Ctrl+Shift+I     ║
║  Tab Accept:  Tab       │  Tab Reject:  Esc              ║
║  Code to Chat: Ctrl+Shift+L                              ║
║                                                          ║
║  Kurallar:    .cursorrules (proje kökü)                  ║
║  İgnore:      .cursorignore                              ║
║  MCP:         .cursor/mcp.json                           ║
║  Hooks:       .cursor/hooks/                             ║
║  Rules:       .cursor/rules/*.mdc                        ║
║                                                          ║
║  Context:     @ + dosya/sembol/url/codebase              ║
║                                                          ║
║  Docs:        docs.cursor.com                            ║
║  Changelog:   cursor.com/changelog                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

**Notlar Sonu**  
*Bu doküman, Cursor'ın resmi dokümantasyonu, topluluk kaynakları ve kişisel deneyimler temel alınarak hazırlanmıştır. Düzenli güncelleme gerektirir.*
