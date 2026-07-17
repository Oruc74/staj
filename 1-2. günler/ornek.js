/*
=======================================================================
JSON (JavaScript Object Notation) NEDİR VE YAPAY ZEKADA NEDEN ÖNEMLİDİR?
=======================================================================

1. JSON Nedir?
   Tamamen metin tabanlı, evrensel bir veri formatıdır. Farklı 
   programlama dillerinin (Python, JavaScript vb.) birbiriyle 
   anlaşabilmesi için kullandıkları ortak dildir.

2. Ne İşe Yarar? Neden Kullanırız?
   En büyük amacı veri taşımaktır. Python (FastAPI) ile yazdığın 
   bir yapay zeka uygulamasının sonuçlarını React arayüzüne gönderirken 
   veriler JSON formatına paketlenip yollanır.

3. Yapay Zeka Dünyasında Neden Önemli?
   - Veri Setleri: NLP modelleri eğitirken kullanılan ham veriler.
   - Model Ayarları: Modellerin parametreleri config.json'da tutulur.
   - Haberleşme: Modelin ürettiği sonuçları başka yazılıma aktarırken kullanılır.
=======================================================================
*/

// Örnek bir JSON yapısının JS dosyasında bir objeye atanmış hali
const ornekJsonVerisi = {
  "proje_adi": "Mail_AI_Asistan",
  "versiyon": 2.1,
  "kullanimda_mi": true,
  "desteklenen_diller": [
    "Turkce",
    "Ingilizce",
    "Almanca"
  ],
  "model_ayarlari": {
    "model_tipi": "Mistral",
    "katman_sayisi": 32,
    "ogrenme_orani": 0.001
  },
  "hata_loglari": null
};

// test dosyası
console.log("Proje Adı:", ornekJsonVerisi.proje_adi);
console.log("Model Tipi:", ornekJsonVerisi.model_ayarlari.model_tipi);