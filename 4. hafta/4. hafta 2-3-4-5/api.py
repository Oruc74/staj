"""FastAPI katmanı: RAG + persona hattını dışarıya RESTful servis olarak açar.

Çalıştırmak için:
    uvicorn api:app --reload
Swagger arayüzü: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import persona
import rag

app = FastAPI(
    title="Ahmet Kaya Persona Chatbot",
    description=(
        "Ahmet Kaya'nın şarkı sözleri üzerine kurulmuş bir RAG servisi. "
        "Gelen mesaja en yakın kıtalar ChromaDB'den bulunur, ardından bir dil "
        "modeli bu kıtalardaki duyguyu benimseyerek cevap üretir."
    ),
    version="1.0.0",
)

# Arayüz (Streamlit) başka bir portta çalıştığı için CORS izni veriyoruz.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SohbetIstegi(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["stajyer-01"])
    message: str = Field(..., min_length=1, examples=["Bugün hiç keyfim yok."])


class Dize(BaseModel):
    sarki: str
    metin: str
    skor: float


class SohbetYaniti(BaseModel):
    status: str
    persona: str
    reply: str
    retrieved_context: list[str]
    dizeler: list[Dize]
    bugunun_sarkisi: str | None = None


@app.get("/api/v1/saglik", summary="Servis ve veri tabanı durumu")
def saglik():
    try:
        adet = rag.koleksiyon_getir().count()
    except Exception as hata:
        raise HTTPException(status_code=503, detail=f"veri tabanı açılamadı: {hata}")
    return {"status": "ok", "persona": persona.PERSONA_ADI, "indeksli_kita": adet}


@app.post("/api/v1/chat", response_model=SohbetYaniti, summary="Persona ile sohbet")
def sohbet(istek: SohbetIstegi):
    """Kullanıcı mesajına en yakın 3 kıtayı bulur ve persona cevabını döndürür."""
    try:
        parcalar = rag.ara(istek.message, k=3)
    except Exception as hata:
        raise HTTPException(status_code=503, detail=f"arama başarısız: {hata}")

    if not parcalar:
        raise HTTPException(status_code=404, detail="uygun şarkı sözü bulunamadı")

    try:
        cevap = persona.cevap_uret(istek.message, parcalar)
    except Exception as hata:
        raise HTTPException(status_code=502, detail=f"model cevap veremedi: {hata}")

    return SohbetYaniti(
        status="ok",
        persona=persona.PERSONA_ADI,
        reply=cevap,
        retrieved_context=[p["metin"] for p in parcalar],
        dizeler=[
            Dize(sarki=p["sarki"], metin=p["metin"], skor=p["skor"]) for p in parcalar
        ],
        bugunun_sarkisi=persona.bugunun_sarkisi(parcalar),
    )
