"""Çalışan API'ye birkaç örnek soru sorup cevapları dosyaya yazar.

Rapora koymak için örnek diyalogları üretmeye yarıyor.
    python test_sohbet.py
"""

import sys
from pathlib import Path

import requests

ADRES = "http://127.0.0.1:8000/api/v1/chat"
CIKTI = Path(__file__).parent / "ornek_sohbetler.md"

SORULAR = [
    "Bugün hiç keyfim yok, içim daralıyor.",
    "Memleketi çok özledim, dönmek istiyorum.",
    "Kodum 3 saattir çalışmıyor, delirmek üzereyim.",
    "Sevdiğim insan beni bırakıp gitti.",
    "Yarın sınavım var ve hiç çalışmadım.",
]


def main():
    satirlar = ["# Örnek Sohbetler\n"]
    for soru in SORULAR:
        print(f"\n> {soru}")
        yanit = requests.post(
            ADRES, json={"user_id": "test", "message": soru}, timeout=90
        )
        yanit.raise_for_status()
        veri = yanit.json()
        print(veri["reply"])
        print(f"  (bugünün şarkısı: {veri.get('bugunun_sarkisi')})")

        satirlar.append(f"\n## {soru}\n")
        satirlar.append(f"**Ahmet Kaya:** {veri['reply']}\n")
        satirlar.append(f"*Bugünün şarkısı:* {veri.get('bugunun_sarkisi')}\n")
        satirlar.append("\n<details><summary>Getirilen dizeler</summary>\n")
        for dize in veri["dizeler"]:
            satirlar.append(
                f"\n**{dize['sarki']}** (benzerlik {dize['skor']:.2f})\n\n"
                f"```\n{dize['metin']}\n```\n"
            )
        satirlar.append("\n</details>\n")

    CIKTI.write_text("".join(satirlar), encoding="utf-8")
    print(f"\nkaydedildi: {CIKTI}")


if __name__ == "__main__":
    # Windows konsolu varsayılan olarak cp1254 kullanıyor, Türkçe karakterler
    # bozuk görünmesin diye çıktıyı UTF-8'e çeviriyoruz.
    sys.stdout.reconfigure(encoding="utf-8")
    main()
