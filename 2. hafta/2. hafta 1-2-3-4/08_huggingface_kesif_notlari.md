# HuggingFace Keşif Notları

Hocanın vurguladığı nokta önemli: YZ alanı, diğer yazılım alanlarına göre çok daha hızlı
güncelleniyor, bu yüzden dokümantasyon/topluluk kaynaklarını takip etmek "bir kere öğrenilip
bırakılacak" bir şey değil, sürekli bir alışkanlık olmalı. Bu notları huggingface.co'yu ve resmi
Hub dokümantasyonunu inceleyerek çıkardım.

## HuggingFace Hub Nedir?

HuggingFace Hub, açık kaynaklı makine öğrenmesi modellerinin, veri setlerinin ve demo
uygulamalarının barındırıldığı, Git tabanlı bir paylaşım platformu. Şu an platformda:

- **~2.9 milyon model**
- **~1.5 milyon veri seti**
- **~1.5 milyon "Space" (interaktif demo uygulaması)**

barındırılıyor. Sadece bir "model deposu" değil, aynı zamanda **versiyon kontrolü, commit
geçmişi, diff, branch** gibi Git'in tüm özelliklerini modellere/veri setlerine de taşıyan bir
platform — yani bir model deposuna GitHub'daki gibi pull request açabilir, farklı versiyonlarını
karşılaştırabilirsiniz.

### Üç Ana Bileşen

| Bileşen | Ne İşe Yarar |
|---|---|
| **Models** | Hazır eğitilmiş modelleri indirip kullanma veya kendi modelinizi paylaşma. Her model bir "Model Card" ile gelir — modelin ne işe yaradığı, sınırlamaları, olası önyargıları belgelenir. |
| **Datasets** | 8.000'den fazla dilde, farklı görev türleri için hazır veri setleri. `datasets` kütüphanesiyle tek satır kodla indirilebilir; büyük veri setleri için **streaming** desteği var (tüm veriyi diske indirmeden işleyebilme). |
| **Spaces** | Modelleri tarayıcıda canlı deneyebileceğiniz demo uygulamaları (genelde Gradio veya Streamlit ile yapılır). Kod yazmadan bir modeli "deneyip görme" imkânı sunar. |

## Şu An Trend Olan Modellere Bakış

`huggingface.co/models?sort=trending` sayfasına baktığımda gördüğüm liste, alanın ne kadar
hızlı hareket ettiğinin güzel bir göstergesi:

| Model | Görev | Parametre | İndirme |
|---|---|---|---|
| baidu/Unlimited-OCR | Image-Text-to-Text | 3B | 2.59M |
| poolside/Laguna-S-2.1 | Text Generation | 118B | 56.4K |
| upstage/Solar-Open2-250B | Text Generation | 250B | 3.31K |
| thinkingmachines/Inkling | Image-Text-to-Text | 952B | 34.5K |

Dikkat çeken nokta: listenin neredeyse tamamı **multimodal** (metin + görsel) modeller ya da
çok büyük parametreli metin üretim modelleri — bu da `07_llm_mimari_karsilastirma.md`'de
bahsettiğim "Native Multimodality" ve büyük ölçekli MoE eğilimini gerçek verilerle doğruluyor.
Ayrıca farklı şirketlerden (Baidu, çeşitli araştırma laboratuvarları) modellerin aynı anda trend
olması, alanın artık tek bir oyuncuya (sadece OpenAI/Google) bağlı olmadığını gösteriyor.

## Neden Önemli — Pratik Faydası

Bir modeli sıfırdan eğitmek yerine HuggingFace'ten hazır bir modeli indirip **fine-tune** etmek
(kendi verinizle ince ayar yapmak), günlük iş akışında çok daha yaygın bir senaryodur. Bunun
sağladığı somut avantajlar:

1. **Zaman/maliyet tasarrufu:** Milyarlarca parametreli bir modeli sıfırdan eğitmek haftalar/
   milyonlarca dolar tutabilir; hazır bir "temel model (foundation model)" üzerine küçük bir
   fine-tuning yeterince olabilir.
2. **`transformers` kütüphanesi ile standart arayüz:** Farklı organizasyonların modellerini
   (Llama, Qwen, BERT, GPT tabanlı modeller) neredeyse aynı birkaç satır kodla yükleyip
   kullanabilirsiniz — model mimarisi farklı olsa bile kullanım arayüzü standartlaşmış durumda.
3. **Model Card'lar sayesinde şeffaflık:** Bir modeli kullanmadan önce hangi veriyle
   eğitildiğini, bilinen sınırlamalarını, lisansını görebilirsiniz — bu, "kör kör" bir model
   kullanmaktan çok daha sorumlu bir yaklaşımdır.
4. **Spaces ile hızlı deneme:** Bir modeli entegre etmeden önce, o modelin bir Space'i varsa
   tarayıcıda deneyip "gerçekten işime yarayacak mı?" sorusuna kod yazmadan cevap
   bulabilirsiniz.

## Alışkanlık Olarak Ne Yapmalı?

Hocanın notuyla birebir örtüşen bir sonuç çıktı benim için: HuggingFace'i "bir kere ziyaret edip
geçilen" bir site olarak değil, **düzenli takip edilen bir kaynak** olarak görmek gerekiyor —
tıpkı bir geliştiricinin GitHub trending sayfasını takip etmesi gibi. Trend olan modellere haftada
bir bakmak bile, sektörün hangi yöne gittiğini (bu hafta multimodal mı öne çıkıyor, yoksa
küçük/verimli modeller mi?) anlamak için yeterli bir sinyal veriyor.
