# PyTorch vs TensorFlow — Framework Karşılaştırması

> **Not:** Bu belge, iki framework'ün belgelenmiş özelliklerine ve genel bilinen
> davranışlarına dayanan **kavramsal bir karşılaştırmadır**. Bu bilgisayarda GPU'lu, her iki
> framework'ün de kurulu olduğu bir ortam bulunmadığından uydurma/rastgele sayılar
> vermek yerine dürüstçe framework'lerin **yapısal** farklarına odaklandım — bir sayı
> görmek yerine "neden farklı davranırlar" sorusuna cevap arıyorum.

## İkisi de Ne İşe Yarar?

Her ikisi de aynı temel işi yapar: tensörler üzerinde matematiksel işlem yapmayı, bu işlemlerin
gradyanını otomatik hesaplamayı (autograd) ve GPU üzerinde hızlandırmayı sağlar. Fark,
**nasıl** yaptıklarında ve etraflarındaki ekosistemde.

| | PyTorch | TensorFlow |
|---|---|---|
| Geliştiren | Meta (Facebook) | Google |
| Çalışma modeli | Dynamic graph (Eager) — kod satır satır çalışır, hata ayıklama kolay | Eskiden static graph, artık (TF2) o da eager moda geçti ama Keras ile daha soyut |
| Sözdizimi hissi | Python'a çok yakın, "sıradan" Python kodu gibi | Keras üzerinden daha "yüksek seviyeli" (`model.fit()`) |
| En güçlü olduğu alan | Araştırma, NLP/Transformer/LLM, hızlı prototipleme | Mobil/gömülü dağıtım (TensorFlow Lite), production pipeline'ları |
| Topluluk/ekosistem | HuggingFace, çoğu güncel LLM (Llama, Qwen, DeepSeek) PyTorch ile eğitiliyor | TensorBoard, TF Serving, uzun süredir kurumsal production'da yaygın |

## Neden Kod Yazma Deneyimi Farklı Hissettiriyor?

PyTorch'ta bir eğitim döngüsü elle yazılır — veri yükleme, forward pass, loss hesaplama,
backward, optimizer adımı hepsi açıkça görünür:

```python
for batch in dataloader:
    optimizer.zero_grad()
    output = model(batch.x)
    loss = criterion(output, batch.y)
    loss.backward()
    optimizer.step()
```

TensorFlow/Keras'ta ise bu döngünün büyük kısmı framework tarafından soyutlanır:

```python
model.compile(optimizer="adam", loss="categorical_crossentropy")
model.fit(x_train, y_train, epochs=10)
```

Bu fark, aslında bir **felsefe farkıdır**: PyTorch "her adımı sen kontrol et, anla" derken,
Keras "en yaygın senaryoyu ben hallederim, sen model mimarisine odaklan" der. Bu yüzden
PyTorch araştırma/deneysel çalışmalarda (yeni bir mimari denemek, eğitim döngüsüne özel
bir müdahale eklemek gerektiğinde), Keras ise standart/klasik problemlerde hızlı sonuç almak
için tercih edilir.

## Neden LLM/Transformer Dünyası PyTorch'a Kaydı?

2020'lerin ortasından itibaren araştırma camiası ağırlıklı olarak PyTorch kullanıyor. Bunun
başlıca sebepleri:

1. **Dynamic graph** yapısı, yeni/deneysel bir attention mekanizması denerken kodu
   doğrudan Python debugger'ıyla adım adım incelemeyi kolaylaştırır.
2. **HuggingFace Transformers** kütüphanesi (günümüzün en yaygın model paylaşım
   platformu) öncelikli olarak PyTorch'u hedefler; çoğu yeni model önce PyTorch ağırlıklarıyla
   yayınlanır.
3. Akademik makalelerin referans implementasyonları çoğunlukla PyTorch'tadır — bu da bir
   kartopu etkisi yaratıp topluluğu daha da PyTorch'a çekmiştir.

TensorFlow ise özellikle **TensorFlow Lite** sayesinde mobil/gömülü cihazlarda modelleri
çalıştırma konusunda hâlâ güçlü bir konumda; bu yüzden "sunucuda büyük bir model eğitip
sonra bir telefon uygulamasına küçültülmüş haliyle gömme" senaryosunda tercih edilebilir.

## Hangi Projede Hangisi?

| Senaryo | Önerilen |
|---|---|
| Bir Transformer/LLM ile deneysel çalışma, NLP araştırması | PyTorch |
| HuggingFace'teki hazır bir modeli fine-tune etmek | PyTorch (çoğu model önce burada) |
| Mobil uygulama içine gömülecek küçük bir görüntü sınıflandırıcı | TensorFlow (TF Lite) |
| Kurumsal, uzun yıllardır TensorFlow altyapısı olan bir production sistemine ekleme yapmak | TensorFlow (mevcut altyapıyla uyum) |
| Staj/okul projesi, hızlı prototip, YZ'yi öğrenmeye çalışmak | PyTorch — hem topluluk kaynağı daha bol hem de "60 Minute Blitz" gibi net bir başlangıç eğitimi var |

## Bu Çalışma Kapsamında Neden PyTorch Seçildi?

Bu görev kapsamındaki pratik uygulama (`09_attention_transformer_uygulamasi.ipynb`) bilinçli
olarak PyTorch ile yazıldı, çünkü:

- Hoca'nın önerdiği "60 Minute Blitz" resmi eğitim serisi PyTorch'a aittir.
- Attention/Transformer mekanizmasını sıfırdan yazarken tensör işlemlerinin (`view`,
  `reshape`, `@`, `transpose`) her adımda ne yaptığını görmek istedim — PyTorch'un dynamic
  graph yapısı bunu adım adım `print(tensor.shape)` ile takip etmeyi çok doğal kılıyor.
- HuggingFace ekosistemiyle ileride çalışmak istersem (hocanın da önerdiği gibi), doğrudan
  aynı framework üzerinde ilerlemiş olacağım.
