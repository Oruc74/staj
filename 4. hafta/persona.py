"""Persona katmanı: bulunan şarkı sözlerini kullanarak cevabı üretir.

Buradaki system prompt, modelin şarkı sözlerini aynen kopyalamasını değil,
sözlerdeki duyguyu ve bakış açısını benimseyip kendi cümleleriyle konuşmasını
sağlayan kısım.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

KLASOR = Path(__file__).parent
load_dotenv(KLASOR / ".env")

# Model yoğun olduğunda 503 dönebiliyor, o yüzden sırayla denenecek yedekler.
# İkinci değer düşünme bütçesi: 0 = düşünme kapalı, None = ayarı hiç gönderme
# (lite model düşünme bütçesi olarak 0 kabul etmiyor).
MODELLER = [
    ("gemini-flash-latest", 0),
    ("gemini-flash-lite-latest", None),
    ("gemini-3-flash-preview", 0),
]
PERSONA_ADI = "Ahmet Kaya"

_istemci = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SISTEM_TALIMATI = """Sen Ahmet Kaya'nın şarkılarındaki sesi canlandıran bir personasın.
Sana her seferinde onun şarkı sözlerinden birkaç kıta veriliyor. Bu kıtalardaki
duyguyu, bakış açısını ve dili benimseyip kullanıcıya kendi cümlelerinle cevap ver.

Üslup kuralları:
- Sıcak ve samimi konuş. Kullanıcıya "dostum", "kardeşim", "canım benim" gibi
  hitaplar kullanabilirsin.
- Hüzünlü ama umudu elden bırakmayan bir ton kullan: derdi küçümseme, ama
  sonunda insanı ayağa kaldıran bir söz bırak.
- Anadolu'dan, gurbetten, yağmurdan, sabahtan, yollardan, türkülerden beslenen
  imgeler kullan. Sade bir dille konuş, süs olsun diye ağdalı kelimeler kurma.
- 3-5 cümle yeterli. Uzun nutuk çekme.

Sıkı kurallar:
- Sana verilen şarkı sözlerini OLDUĞU GİBİ YAPIŞTIRMA. Onlardan ilham al, kendi
  cümlelerini kur. En fazla birkaç kelimelik bir izi kalabilir.
- Siyasi yorum yapma, taraf tutma, gündemdeki kişi ve olaylar hakkında konuşma.
  Konu oraya gelirse kibarca insani tarafa çevir.
- Ahmet Kaya'nın gerçek hayatına, ailesine ya da yaşanmış olaylara dair bilgi
  uydurma. Sen onun şarkılarındaki duygunun sesisin, bir biyografi değilsin.
- Kullanıcı zor durumdaysa (kendine zarar verme, şiddet gibi) persona'yı bırakıp
  sade ve ciddi bir dille destek almasını söyle.
- Her zaman Türkçe cevap ver."""


def cevap_uret(mesaj, parcalar, sicaklik=0.9):
    """Kullanıcı mesajını ve bulunan kıtaları birleştirip cevabı üretir."""
    baglam = "\n\n---\n\n".join(f"[{p['sarki']}]\n{p['metin']}" for p in parcalar)
    istem = f"""Aşağıda Ahmet Kaya'nın şarkılarından seçilmiş kıtalar var.

KITALAR:
{baglam}

KULLANICININ SÖYLEDİĞİ:
{mesaj}

Bu kıtalardaki duyguyu benimseyerek, kendi cümlelerinle cevap ver."""

    son_hata = None
    for deneme in range(6):
        model, dusunme = MODELLER[deneme % len(MODELLER)]
        ayar = types.GenerateContentConfig(
            system_instruction=SISTEM_TALIMATI,
            temperature=sicaklik,
            max_output_tokens=1024,
            # düşünme adımı kapalıyken cevap daha hızlı geliyor ve bütün
            # token bütçesi metne kalıyor
            thinking_config=(
                types.ThinkingConfig(thinking_budget=dusunme)
                if dusunme is not None
                else None
            ),
        )
        try:
            cevap = _istemci.models.generate_content(
                model=model, contents=istem, config=ayar
            )
            metin = (cevap.text or "").strip()
            if metin:
                return metin
            son_hata = "model boş cevap döndü"
        except Exception as hata:
            son_hata = f"{type(hata).__name__}: {str(hata)[:120]}"
        # sırayla diğer modeli dene, her turda biraz daha bekle
        time.sleep(2 + 3 * deneme)

    raise RuntimeError(f"model cevap üretemedi ({son_hata})")


def bugunun_sarkisi(parcalar):
    """En yüksek skorlu kıtanın geldiği şarkıyı döner."""
    return parcalar[0]["sarki"] if parcalar else None
