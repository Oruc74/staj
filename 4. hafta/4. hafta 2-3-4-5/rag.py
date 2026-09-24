"""RAG hattı: şarkı sözlerini kıtalara bölme, vektörleştirme ve arama.

Bu dosya iki işi yapıyor:
  * `python rag.py` çalıştırıldığında sözleri parçalayıp ChromaDB'ye indeksliyor.
  * api.py bu dosyadaki `ara()` fonksiyonunu kullanarak en yakın kıtaları çekiyor.
"""

import json
import os
import sys
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

KLASOR = Path(__file__).parent
VERI_DOSYASI = KLASOR / "veri" / "ahmet_kaya_sarkilar.json"
CHROMA_YOLU = str(KLASOR / "chroma_db")
KOLEKSIYON = "ahmet_kaya"

EMBED_MODEL = "gemini-embedding-001"
BOYUT = 768  # tam boyut 3072, 768 de yeterli ve daha hızlı
DAKIKA_SINIRI = 85  # ücretsiz katman dakikada 100 metin; altında kalıyoruz
MIN_PARCA = 200  # karakter
MAX_PARCA = 450

load_dotenv(KLASOR / ".env")
_istemci = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# --------------------------------------------------------------------------
# 1) Parçalama (chunking)
# --------------------------------------------------------------------------
def kitalara_bol(sozler):
    """Şarkı sözlerini kıta kıta böler.

    Sözlerde kıtalar boş satırla ayrıldığı için doğal bölme noktası orası.
    Çok kısa kıtaları bir sonrakiyle birleştiriyoruz ki parça anlamlı olsun,
    çok uzun olanları da satır satır bölüp MAX_PARCA'yı aşmalarını önlüyoruz.
    """
    ham_kitalar = [k.strip() for k in sozler.split("\n\n") if k.strip()]

    kitalar = []
    for kita in ham_kitalar:
        if len(kita) <= MAX_PARCA:
            kitalar.append(kita)
            continue
        # uzun kıta: satırları toplayıp MAX_PARCA'ya yaklaşınca kes
        parca = []
        for satir in kita.split("\n"):
            parca.append(satir)
            if len("\n".join(parca)) >= MAX_PARCA:
                kitalar.append("\n".join(parca))
                parca = []
        if parca:
            kitalar.append("\n".join(parca))

    # kısa kıtaları bir sonrakine yapıştır
    birlesik, tampon = [], ""
    for kita in kitalar:
        tampon = f"{tampon}\n\n{kita}".strip() if tampon else kita
        if len(tampon) >= MIN_PARCA:
            birlesik.append(tampon)
            tampon = ""
    if tampon:
        if birlesik:
            birlesik[-1] += "\n\n" + tampon
        else:
            birlesik.append(tampon)
    return birlesik


def parcalari_hazirla(sarkilar):
    """Bütün şarkıları gezip (metin, şarkı adı, url, kıta no) listesi üretir."""
    parcalar = []
    for sarki in sarkilar:
        for sira, kita in enumerate(kitalara_bol(sarki["sozler"])):
            parcalar.append(
                {
                    "metin": kita,
                    "sarki": sarki["sarki"],
                    "url": sarki["url"],
                    "kita": sira,
                }
            )
    return parcalar


# --------------------------------------------------------------------------
# 2) Vektörleştirme (embedding)
# --------------------------------------------------------------------------
def embed_al(metinler, tip="RETRIEVAL_DOCUMENT", yigin=20):
    """Metinleri Gemini ile vektöre çevirir.

    Ücretsiz katmanda dakikada 100 metin sınırlaması var ve yığın hâlinde
    göndersek bile her metin ayrı sayılıyor. Bu yüzden her yığından sonra
    dakikada DAKIKA_SINIRI metni aşmayacak kadar bekliyoruz. Yine de kota
    hatası gelirse (429) bir dakika bekleyip tekrar deniyoruz.
    """
    ayar = types.EmbedContentConfig(task_type=tip, output_dimensionality=BOYUT)
    vektorler = []
    for basla in range(0, len(metinler), yigin):
        dilim = metinler[basla : basla + yigin]
        for deneme in range(6):
            try:
                cevap = _istemci.models.embed_content(
                    model=EMBED_MODEL, contents=dilim, config=ayar
                )
                vektorler.extend([e.values for e in cevap.embeddings])
                break
            except Exception as hata:
                if deneme == 5:
                    raise
                kota = "429" in str(hata) or "RESOURCE_EXHAUSTED" in str(hata)
                bekleme = 60 if kota else 5 * (deneme + 1)
                print(
                    f"    {'kota doldu' if kota else type(hata).__name__}, "
                    f"{bekleme} sn bekleniyor..."
                )
                time.sleep(bekleme)
        if basla + yigin < len(metinler):
            print(f"  {basla + yigin}/{len(metinler)} parça")
            time.sleep(len(dilim) * 60 / DAKIKA_SINIRI)
    return vektorler


# --------------------------------------------------------------------------
# 3) ChromaDB
# --------------------------------------------------------------------------
_koleksiyon_onbellek = None


def koleksiyon_getir(yeniden=False):
    """Koleksiyonu açar. API her istekte yeniden açmasın diye bir kere tutuyoruz."""
    global _koleksiyon_onbellek
    if _koleksiyon_onbellek is not None and not yeniden:
        return _koleksiyon_onbellek

    istemci = chromadb.PersistentClient(path=CHROMA_YOLU)
    if yeniden:
        try:
            istemci.delete_collection(KOLEKSIYON)
        except Exception:
            pass
    _koleksiyon_onbellek = istemci.get_or_create_collection(
        name=KOLEKSIYON,
        embedding_function=None,
        metadata={"hnsw:space": "cosine"},
    )
    return _koleksiyon_onbellek


def indeks_olustur():
    with open(VERI_DOSYASI, encoding="utf-8") as f:
        sarkilar = json.load(f)
    print(f"{len(sarkilar)} şarkı okundu.")

    parcalar = parcalari_hazirla(sarkilar)
    uzunluklar = [len(p["metin"]) for p in parcalar]
    print(
        f"{len(parcalar)} kıta çıktı "
        f"(ortalama {sum(uzunluklar) // len(uzunluklar)} karakter).\n"
    )

    print("vektörleştiriliyor...")
    vektorler = embed_al([p["metin"] for p in parcalar])

    print("\nChromaDB'ye yazılıyor...")
    koleksiyon = koleksiyon_getir(yeniden=True)
    koleksiyon.add(
        ids=[f"{i}" for i in range(len(parcalar))],
        embeddings=vektorler,
        documents=[p["metin"] for p in parcalar],
        metadatas=[
            {"sarki": p["sarki"], "url": p["url"], "kita": p["kita"]} for p in parcalar
        ],
    )
    print(f"bitti: {koleksiyon.count()} kıta indekslendi -> {CHROMA_YOLU}")


# --------------------------------------------------------------------------
# 4) Arama
# --------------------------------------------------------------------------
def ara(soru, k=3):
    """Soruya anlamca en yakın k kıtayı döndürür."""
    koleksiyon = koleksiyon_getir()
    soru_vektor = embed_al([soru], tip="RETRIEVAL_QUERY")[0]
    sonuc = koleksiyon.query(
        query_embeddings=[soru_vektor],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    bulunanlar = []
    for metin, bilgi, uzaklik in zip(
        sonuc["documents"][0], sonuc["metadatas"][0], sonuc["distances"][0]
    ):
        bulunanlar.append(
            {
                "metin": metin,
                "sarki": bilgi["sarki"],
                "url": bilgi["url"],
                "skor": round(1 - uzaklik, 4),  # kosinüs uzaklığını benzerliğe çevir
            }
        )
    return bulunanlar


if __name__ == "__main__":
    # Windows konsolu varsayılan olarak cp1254 kullanıyor, Türkçe karakterler
    # bozuk görünmesin diye çıktıyı UTF-8'e çeviriyoruz.
    sys.stdout.reconfigure(encoding="utf-8")
    indeks_olustur()
