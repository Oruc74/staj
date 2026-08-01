# 3. Hafta (Gün 3-4-5) — AI Engineer Araştırması + Native RAG Uygulaması

Bu klasör iki farklı teslimi içerir: 5 bölümlük teorik araştırma raporu (PDF) ve
framework kullanılmadan sıfırdan yazılmış bir RAG (Retrieval-Augmented
Generation) uygulaması.

## İçindekiler

| Dosya | Konu |
|---|---|
| [bolum_1_ai_muhendisligi_ve_rol_tanimlari.pdf](bolum_1_ai_muhendisligi_ve_rol_tanimlari.pdf) | AI Engineer vs ML Engineer, ürün geliştirmedeki rolü |
| [bolum_2_temel_kavramlar_ve_ai_mimarisi.pdf](bolum_2_temel_kavramlar_ve_ai_mimarisi.pdf) | ANI vs AGI, Embeddings & Vektör Veritabanları, Training vs Inference |
| [bolum_3_ileri_duzey_teknikler.pdf](bolum_3_ileri_duzey_teknikler.pdf) | Fine-tuning vs RAG, AI Agents, Prompt vs Context Engineering |
| [bolum_4_rag_mimarileri.pdf](bolum_4_rag_mimarileri.pdf) | Naive/Advanced RAG, GraphRAG, Multimodal RAG, CRAG/Self-RAG/Agentic RAG, chunking, benzerlik metrikleri, halüsinasyon engelleme |
| [bolum_5_ornekleme_parametreleri.pdf](bolum_5_ornekleme_parametreleri.pdf) | Context window, Temperature, Top-K/Top-P, Repetition Penalty |
| [native_rag.py](native_rag.py) | Native RAG uygulaması — düz Python script hâli |
| [native_rag_uygulamasi.ipynb](native_rag_uygulamasi.ipynb) | Aynı uygulama, açıklamalı/adım adım notebook hâli |

PDF'ler sadece okumak için — hiçbir kurulum gerekmez.

## `native_rag.py` / `native_rag_uygulamasi.ipynb` için Gereksinimler

```powershell
pip install pymupdf
```

Ayrıca kod **Gemini API** kullanıyor (embedding + cevap üretme için), bu yüzden
bir API key ve internet bağlantısı gerekiyor.

### API key nasıl alınır?

1. https://aistudio.google.com/apikey adresine git (Google hesabınla giriş yap)
2. "Create API key" → "Create API key in new project"
3. `AIza...` veya `AQ...` ile başlayan anahtarı kopyala

### `.env` dosyası nasıl kurulur?

Bu klasörün içine (`native_rag.py` ile aynı yere) `.env` adında bir dosya
oluştur, içine tek satır:

```
GEMINI_API_KEY=senin_api_keyin
```

`.env` dosyası `.gitignore`'da hariç tutulmuştur — asla Git'e gönderilmez, key
kod içine de yazılmamıştır, kod her çalıştığında dosyadan okur.

## Nasıl Çalıştırılır

```powershell
python native_rag.py
```

veya notebook hâli için:

```powershell
jupyter notebook native_rag_uygulamasi.ipynb
```

Çalıştığında sırasıyla: `bolum_4_rag_mimarileri.pdf`'i metne çevirir → parçalara
böler → her parçayı embed'ler → iki test sorusu sorar (biri belgede olan, biri
olmayan bir konuda) → sonuçları ekrana yazar.

## Notlar

- `.env` dosyası olmadan kod `.env` dosyasını okumaya çalışırken hata verir —
  önce API key kurulumu yapılmalı.
- Her çalıştırmada gerçek API çağrıları yapılır (embedding + generation), bu
  yüzden internet bağlantısı gereklidir ve sonuçlar modelin o anki cevabına
  göre küçük farklılıklar gösterebilir (metnin anlamı değişmez).
