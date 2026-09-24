"""Streamlit arayüzü: FastAPI servisine bağlanan basit sohbet ekranı.

Çalıştırmak için (api.py ayrı bir terminalde açıkken):
    streamlit run arayuz.py
"""

import html

import requests
import streamlit as st

API_ADRESI = "http://127.0.0.1:8000/api/v1/chat"
ORNEK_SORULAR = [
    "Bugün hiç keyfim yok, içim daralıyor.",
    "Memleketi çok özledim.",
    "Kodum 3 saattir çalışmıyor, delirmek üzereyim.",
    "Bir insanı beklemek nedir?",
]

st.set_page_config(
    page_title="Ahmet Kaya Persona Chatbot", page_icon="🎶", layout="centered"
)

STIL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

.stApp {
    background:
        radial-gradient(1200px 600px at 50% -10%, #2b1f16 0%, rgba(43,31,22,0) 60%),
        linear-gradient(180deg, #17110d 0%, #120d0a 100%);
    color: #efe3d3;
}
html, body, [class*="css"] { font-family: 'Lora', Georgia, serif; }

.baslik { text-align: center; padding: 6px 0 2px 0; }
.baslik h1 {
    font-size: 2.5rem; letter-spacing: .22em; margin: 0;
    color: #e9c078; font-weight: 600; text-transform: uppercase;
}
.baslik p { color: #a08a6f; margin: .35rem 0 0 0; font-style: italic; font-size: .95rem; }
.ayrac { display: flex; align-items: center; gap: 14px; margin: 14px 0 26px 0; }
.ayrac hr { flex: 1; border: 0; border-top: 1px solid #4a3627; margin: 0; }

/* kullanıcı mesajı */
.kullanici {
    background: #241a13; border: 1px solid #3a2a1d; border-radius: 14px 14px 4px 14px;
    padding: 12px 16px; margin: 14px 0 6px auto; max-width: 78%; width: fit-content;
    color: #e6d8c6; font-size: .97rem;
}
/* persona cevabı: mektup kâğıdı */
.mektup {
    background: linear-gradient(180deg, #f6ecd9 0%, #efe2ca 100%);
    color: #2e2318; border-radius: 4px 14px 14px 14px; padding: 20px 22px 14px 22px;
    margin: 6px auto 4px 0; max-width: 88%;
    box-shadow: 0 10px 26px rgba(0,0,0,.45); border-left: 4px solid #b5803c;
    font-size: 1.02rem; line-height: 1.75;
}
.mektup .imza {
    text-align: right; font-style: italic; color: #7a5a33;
    margin-top: 12px; font-size: .92rem;
}
.sarki-rozeti {
    display: inline-block; margin: 8px 0 2px 2px; padding: 5px 12px;
    background: #2a1d12; border: 1px solid #6b4d2b; border-radius: 999px;
    color: #e9c078; font-size: .82rem; letter-spacing: .04em;
}
.dize {
    background: #1d1610; border-left: 3px solid #6b4d2b; border-radius: 6px;
    padding: 10px 14px; margin: 8px 0; color: #cdbba4;
    font-size: .9rem; white-space: pre-wrap; font-style: italic;
}
.dize b { color: #e9c078; font-style: normal; }
.not { color: #7d6a55; font-size: .78rem; text-align: center; margin-top: 26px; }
</style>
"""
st.markdown(STIL, unsafe_allow_html=True)

# Başlık altındaki bağlama çizimi (inline SVG, dışarıdan görsel indirmiyoruz)
SAZ = """
<div class="ayrac">
  <hr>
  <svg viewBox="0 0 250 60" width="220" height="53" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="196" cy="30" rx="44" ry="26" fill="#2b1d12" stroke="#b5803c" stroke-width="1.6"/>
    <ellipse cx="196" cy="30" rx="34" ry="18" fill="none" stroke="#6b4d2b" stroke-width="1"/>
    <circle cx="180" cy="30" r="6.5" fill="#12100d" stroke="#b5803c" stroke-width="1"/>
    <rect x="44" y="26" width="120" height="8" rx="3" fill="#25190f" stroke="#b5803c" stroke-width="1.2"/>
    <rect x="16" y="21" width="30" height="18" rx="4" fill="#25190f" stroke="#b5803c" stroke-width="1.2"/>
    <line x1="22" y1="21" x2="22" y2="13" stroke="#b5803c" stroke-width="1.6"/>
    <line x1="31" y1="21" x2="31" y2="13" stroke="#b5803c" stroke-width="1.6"/>
    <line x1="40" y1="21" x2="40" y2="13" stroke="#b5803c" stroke-width="1.6"/>
    <line x1="46" y1="28.5" x2="214" y2="28.5" stroke="#e9c078" stroke-width="0.7" opacity=".75"/>
    <line x1="46" y1="30" x2="214" y2="30" stroke="#e9c078" stroke-width="0.7" opacity=".55"/>
    <line x1="46" y1="31.5" x2="214" y2="31.5" stroke="#e9c078" stroke-width="0.7" opacity=".75"/>
    <rect x="210" y="24" width="4" height="12" rx="1" fill="#b5803c"/>
  </svg>
  <hr>
</div>
"""

st.markdown(
    """
    <div class="baslik">
        <h1>Ahmet Kaya</h1>
        <p>Gurbetten Mektup &mdash; derdini yaz, şarkılarından cevap gelsin</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(SAZ, unsafe_allow_html=True)

if "gecmis" not in st.session_state:
    st.session_state.gecmis = []

with st.sidebar:
    st.markdown("### Ayarlar")
    adres = st.text_input("API adresi", API_ADRESI)
    dizeleri_goster = st.checkbox("İlham alınan dizeleri göster", value=True)

    st.markdown("### Örnek sorular")
    for soru in ORNEK_SORULAR:
        if st.button(soru, use_container_width=True):
            st.session_state.bekleyen = soru

    if st.button("Sohbeti temizle", use_container_width=True):
        st.session_state.gecmis = []
        st.rerun()

    st.markdown(
        "---\nBu uygulama, Ahmet Kaya'nın şarkı sözleri üzerine kurulmuş bir "
        "RAG denemesidir. Üretilen cümleler yapay zekâ tarafından yazılır, "
        "sanatçının kendi sözleri değildir."
    )


def cevap_al(adres, mesaj):
    yanit = requests.post(
        adres, json={"user_id": "arayuz", "message": mesaj}, timeout=90
    )
    yanit.raise_for_status()
    return yanit.json()


def mesaji_ciz(kayit):
    st.markdown(
        f'<div class="kullanici">{html.escape(kayit["soru"])}</div>',
        unsafe_allow_html=True,
    )
    cevap = html.escape(kayit["cevap"]).replace("\n", "<br>")
    st.markdown(
        f'<div class="mektup">{cevap}<div class="imza">&mdash; Ahmet Kaya</div></div>',
        unsafe_allow_html=True,
    )
    if kayit.get("sarki"):
        st.markdown(
            f'<div class="sarki-rozeti">Bugünün şarkısı: '
            f'{html.escape(kayit["sarki"])}</div>',
            unsafe_allow_html=True,
        )
    if dizeleri_goster and kayit.get("dizeler"):
        with st.expander("İlham alınan dizeler"):
            for dize in kayit["dizeler"]:
                metin = html.escape(dize["metin"]).replace("\n", "<br>")
                st.markdown(
                    f'<div class="dize"><b>{html.escape(dize["sarki"])}</b> '
                    f'&middot; benzerlik {dize["skor"]:.2f}<br>{metin}</div>',
                    unsafe_allow_html=True,
                )


for kayit in st.session_state.gecmis:
    mesaji_ciz(kayit)

mesaj = st.chat_input("Derdini yaz...")
if not mesaj and "bekleyen" in st.session_state:
    mesaj = st.session_state.pop("bekleyen")

if mesaj:
    st.markdown(
        f'<div class="kullanici">{html.escape(mesaj)}</div>', unsafe_allow_html=True
    )
    with st.spinner("Bir türkü dinleniyor..."):
        try:
            sonuc = cevap_al(adres, mesaj)
        except Exception as hata:
            st.error(
                f"Servise ulaşılamadı: {hata}\n\n"
                "API açık mı? `uvicorn api:app --reload`"
            )
            st.stop()

    kayit = {
        "soru": mesaj,
        "cevap": sonuc["reply"],
        "sarki": sonuc.get("bugunun_sarkisi"),
        "dizeler": sonuc.get("dizeler", []),
    }
    st.session_state.gecmis.append(kayit)
    st.rerun()

st.markdown(
    '<div class="not">Yapay zekâ üretimi &middot; şarkı sözleri sarkisozum.gen.tr '
    "üzerinden derlenmiştir</div>",
    unsafe_allow_html=True,
)
