# 4. Hafta (Gün 2-3-4-5) — Ahmet Kaya RAG Persona Chatbot

Ahmet Kaya'nın şarkı sözleri üzerine kurulmuş, hazır RAG kütüphanesi (LangChain,
LlamaIndex vb.) kullanılmadan yazılmış bir persona chatbot'u. Kullanıcı derdini
yazıyor; sistem en yakın şarkı kıtalarını vektör veritabanından buluyor ve dil
modeli bu kıtalardaki duyguyu benimseyerek kendi cümleleriyle cevap veriyor.

## İçindekiler

| Dosya | Konu |
|---|---|
| [scraper.py](scraper.py) | robots.txt kontrolü + şarkı sözlerinin toplanması (235 şarkı) |
| [rag.py](rag.py) | Kıta bazlı parçalama, Gemini ile vektörleştirme, ChromaDB indeksi ve arama |
| [persona.py](persona.py) | Persona system prompt'u ve cevap üretimi |
| [api.py](api.py) | FastAPI servisi (`POST /api/v1/chat`), Pydantic modelleri, CORS |
| [arayuz.py](arayuz.py) | Streamlit sohbet arayüzü |
| [test_sohbet.py](test_sohbet.py) | Örnek soruları API'ye sorup `ornek_sohbetler.md` dosyasını üretir |
| [veri/ahmet_kaya_sarkilar.json](veri/ahmet_kaya_sarkilar.json) | Toplanan şarkı sözleri |

## Mimari

```
kullanıcı mesajı
      │
      ▼
FastAPI  POST /api/v1/chat
      │
      ├─► rag.ara()      : soru → Gemini embedding → ChromaDB'de en yakın 3 kıta
      │
      └─► persona.cevap_uret() : kıtalar + mesaj → Gemini → persona cevabı
                                   │
                                   ▼
                     {status, persona, reply, retrieved_context, ...}
```

## Gereksinimler

```powershell
pip install -r requirements.txt
```

Ayrıca bu klasörde `.env` dosyası olmalı:

```
GEMINI_API_KEY=senin_api_keyin
```

Key [aistudio.google.com/apikey](https://aistudio.google.com/apikey) üzerinden
alınır. `.env` dosyası `.gitignore`'da, Git'e gönderilmez.

## Nasıl Çalıştırılır

```powershell
python scraper.py              # 1) şarkı sözlerini topla  (~4 dk)
python rag.py                  # 2) vektör indeksini kur   (~6 dk)
uvicorn api:app --reload       # 3) API'yi başlat          -> http://127.0.0.1:8000/docs
streamlit run arayuz.py        # 4) arayüzü aç (ayrı terminalde)
python test_sohbet.py          # 5) örnek sohbetleri üret (API açıkken)
```

Veri ve indeks bir kere kurulduktan sonra 1. ve 2. adımları tekrarlamaya gerek yok.

## API

**İstek** — `POST /api/v1/chat`

```json
{ "user_id": "stajyer-01", "message": "Bugün hiç keyfim yok." }
```

**Yanıt**

```json
{
  "status": "ok",
  "persona": "Ahmet Kaya",
  "reply": "...",
  "retrieved_context": ["...", "...", "..."],
  "dizeler": [{ "sarki": "...", "metin": "...", "skor": 0.72 }],
  "bugunun_sarkisi": "..."
}
```

`GET /api/v1/saglik` servisin ve indeksin durumunu döner. Swagger arayüzü
`/docs` adresinde açılır, istekler oradan da denenebilir.

## Teknik Notlar

- **Parçalama:** Şarkı sözlerinde kıtalar boş satırla ayrıldığı için bölme
  noktası olarak kıta sonları kullanıldı. Çok kısa kıtalar birleştirildi, çok
  uzun olanlar bölündü. Sonuçta 235 şarkıdan 458 parça çıktı (ortalama 346
  karakter).
- **Embedding:** `gemini-embedding-001`, 768 boyut. Ücretsiz katmanda dakikada
  100 metin sınırı olduğu için `rag.py` istekleri kendi içinde yavaşlatıyor.
- **Vektör veritabanı:** ChromaDB, kosinüs benzerliği. `chroma_db/` klasörü
  Git'e gönderilmiyor, `python rag.py` ile yeniden üretilebiliyor.
- **Türkçe karakterler:** Windows konsolu varsayılan olarak cp1254 kullandığı
  için betikler çıktıyı UTF-8'e çeviriyor (`sys.stdout.reconfigure`). Terminalde
  yine bozuk görünürse `chcp 65001` komutu kod sayfasını UTF-8 yapar. Kaydedilen
  dosyalar (JSON, Markdown) her zaman UTF-8.
- **Cevap üretimi:** `gemini-flash-latest` yoğun olduğunda 503 dönebiliyor. Bu
  yüzden `persona.py` sırayla yedek modellere geçiyor ve düşünme adımını
  kapatarak token bütçesinin tamamını cevaba bırakıyor.
- **Persona kuralları:** Model şarkı sözlerini aynen kopyalamıyor, siyasi yorum
  yapmıyor ve sanatçının gerçek hayatına dair bilgi uydurmuyor. Bu kurallar
  `persona.py` içindeki system prompt'ta tanımlı.
- **Scraping:** Sözler [sarkisozum.gen.tr](https://www.sarkisozum.gen.tr/ahmet-kaya)
  üzerinden derlendi. Scraper önce robots.txt'yi kontrol ediyor ve istekler
  arasında bekleme bırakıyor.
- Üretilen cümleler yapay zekâ çıktısıdır, sanatçının kendi sözleri değildir.
