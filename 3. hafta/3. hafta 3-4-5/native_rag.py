# Native RAG Projesi (framework'suz, sifirdan)
# Once burada duz .py olarak yazdim, calistigini gordukten sonra
# native_rag_uygulamasi.ipynb icine acikmalariyla birlikte tasidim.

import fitz  # PyMuPDF, PDF'ten metin cikarmak icin
import urllib.request
import json
import math

with open(".env", encoding="utf-8") as f:
    API_KEY = f.read().strip().split("=", 1)[1]

EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={}"
GEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={}"


def yukle_metin(pdf_yolu):
    doc = fitz.open(pdf_yolu)
    metin = ""
    for sayfa in doc:
        metin += sayfa.get_text()
    return metin


def parcala(metin, parca_boyutu=600, ortusme=100):
    parcalar = []
    basla = 0
    while basla < len(metin):
        bitis = basla + parca_boyutu
        parcalar.append(metin[basla:bitis].strip())
        basla = bitis - ortusme
    return [p for p in parcalar if p]


def embed_al(metin):
    body = json.dumps({"content": {"parts": [{"text": metin}]}}).encode("utf-8")
    req = urllib.request.Request(
        EMBED_URL.format(API_KEY), data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["embedding"]["values"]


def kosinus_benzerlik(a, b):
    ic_carpim = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return ic_carpim / (norm_a * norm_b)


def en_yakin_parcalari_bul(soru, parcalar, parca_vektorleri, k=3):
    soru_vektor = embed_al(soru)
    skorlar = [
        (kosinus_benzerlik(soru_vektor, pv), i) for i, pv in enumerate(parca_vektorleri)
    ]
    skorlar.sort(reverse=True)
    return [(parcalar[i], skor) for skor, i in skorlar[:k]]


def cevap_uret(soru, baglam_parcalari):
    baglam = "\n\n---\n\n".join(baglam_parcalari)
    prompt = f"""Aşağıda bir metinden alınmış parçalar var. SADECE bu parçalardaki bilgiyi kullanarak soruyu cevapla. Eğer cevap parçalarda yoksa, başka hiçbir şey söylemeden sadece "Bilgi bulunamadı." yaz.

BAĞLAM:
{baglam}

SORU: {soru}

CEVAP:"""
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(
        GEN_URL.format(API_KEY), data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


if __name__ == "__main__":
    print("=== 1) Metni yukle ve parcala ===")
    metin = yukle_metin("bolum_4_rag_mimarileri.pdf")
    parcalar = parcala(metin, parca_boyutu=600, ortusme=100)
    print(f"toplam karakter: {len(metin)}, parca sayisi: {len(parcalar)}")

    print("\n=== 2) Her parcayi embed'le ===")
    parca_vektorleri = [embed_al(p) for p in parcalar]
    print(f"{len(parca_vektorleri)} parca embed edildi")

    print("\n=== 3) TEST 1: belge ICI soru ===")
    soru1 = "GraphRAG ne zaman avantajli, hangi tip sorularda vektor tabanli aramadan daha iyi calisiyor?"
    bulunanlar1 = en_yakin_parcalari_bul(soru1, parcalar, parca_vektorleri, k=3)
    print("Soru:", soru1)
    for p, skor in bulunanlar1:
        print(f"  [skor={skor:.4f}] {p[:80]}...")
    cevap1 = cevap_uret(soru1, [p for p, s in bulunanlar1])
    print("\nCEVAP 1:\n", cevap1)

    print("\n=== 4) TEST 2: belge DISI soru ===")
    soru2 = "Python programlama dilinde bir for dongusu nasil yazilir?"
    bulunanlar2 = en_yakin_parcalari_bul(soru2, parcalar, parca_vektorleri, k=3)
    print("Soru:", soru2)
    for p, skor in bulunanlar2:
        print(f"  [skor={skor:.4f}] {p[:80]}...")
    cevap2 = cevap_uret(soru2, [p for p, s in bulunanlar2])
    print("\nCEVAP 2:\n", cevap2)
