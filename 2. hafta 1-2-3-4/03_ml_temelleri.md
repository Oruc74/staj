# Makine Öğrenmesi (ML) Temelleri

## Makine Öğrenmesinin Üç Türü

| Tür | Veri | Amaç | Örnek |
|---|---|---|---|
| **Gözetimli (Supervised)** | Girdi + doğru cevap birlikte verilir | Yeni girdiler için doğru cevabı tahmin etmek | E-postanın spam olup olmadığını tahmin etme (etiketli e-posta veri setiyle eğitilir) |
| **Gözetimsiz (Unsupervised)** | Sadece girdi verilir, "doğru cevap" yok | Veri içindeki gizli yapıyı/grupları bulmak | Bir e-ticaret sitesindeki müşterileri alışveriş alışkanlığına göre gruplara ayırma (kimse "bu müşteri grup 3'te" diye etiketlememiş) |
| **Pekiştirmeli (Reinforcement)** | Ortam + ödül/ceza sinyali | Deneme-yanılmayla en iyi stratejiyi bulmak | Bir satranç motorunun kendi kendine oynayarak, kazandığı hamlelerden "ödül" alıp geliştirmesi |

**Ayırt edici soru:** "Elimde doğru cevaplar (etiketler) var mı?" → Evet ise gözetimli, hayır
ama bir grup/yapı arıyorsam gözetimsiz, ortamla etkileşip geri bildirim alıyorsam pekiştirmeli.

Not: Günümüzün büyük dil modelleri (GPT, Claude vb.) aslında bu üç türün **hibrit** bir
kombinasyonuyla eğitilir — önce devasa metin üzerinde gözetimsiz/self-supervised bir
"ön-eğitim" (bir sonraki kelimeyi tahmin etmeyi öğrenme), sonra insan geri bildirimiyle
pekiştirmeli öğrenme (RLHF) uygulanır.

---

## Model Nedir?

Model, girdi verisini alıp bir çıktı (tahmin) üreten **matematiksel bir fonksiyondur**. "Öğrenme"
dediğimiz şey, bu fonksiyonun içindeki sayıları (parametreleri) veriye göre ayarlamaktır.

```
Girdi: bir ev ilanının m², oda sayısı, konum puanı
   ↓
Model (fonksiyon): fiyat = w1*m² + w2*oda_sayisi + w3*konum + b
   ↓
Çıktı: tahmini fiyat
```

Basit bir doğrusal regresyon da bir modeldir, GPT-4 gibi trilyonlarca parametreli bir Transformer
da bir modeldir — ikisi de aynı temel fikri paylaşır: **veriden bir fonksiyon öğrenmek.**

## Parametre Nedir?

Parametreler, yukarıdaki örnekte `w1, w2, w3, b` gibi, **modelin eğitim sırasında kendi kendine
ayarladığı sayılardır**. Eğitim öncesi rastgele (veya belirli bir stratejiyle) başlatılırlar, eğitim
sırasında verideki hatayı azaltacak şekilde güncellenirler.

> Önemli nokta: Parametre sayısı arttıkça model daha karmaşık ilişkiler öğrenebilir, ama bu
> otomatik olarak "daha iyi model" demek değildir — daha fazla veri, daha fazla bellek/işlem
> gücü ve overfitting riski de birlikte gelir (bkz. `04_deep_learning_temelleri.md`).

**Hyperparameter** ile karıştırılmamalı: hyperparameter'lar (öğrenme oranı, batch size, katman
sayısı gibi) modelin **kendisinin öğrenmediği**, geliştiricinin eğitim öncesi belirlediği ayarlardır.

## Training (Eğitim) Nedir?

Eğitim, modelin parametrelerini tekrar tekrar güncelleyerek hata payını azaltma sürecidir:

```
1. Model bir tahmin yapar (Forward Pass)
2. Tahmin ile gerçek değer karşılaştırılır → Loss hesaplanır
3. Loss'un parametrelere göre "türevi" alınır (Backpropagation)
4. Parametreler, Loss'u azaltacak yönde güncellenir (Optimizer)
5. 1'e dön, bunu binlerce/milyonlarca kez tekrarla
```

## Loss (Kayıp) Nedir?

Loss, modelin tahmininin gerçek değerden ne kadar uzak olduğunu **tek bir sayıyla** özetleyen
fonksiyondur. Eğitimin tüm amacı bu sayıyı küçültmektir.

- Gerçek fiyat: 500.000 TL, Model tahmini: 480.000 TL → Loss küçük (iyi)
- Gerçek fiyat: 500.000 TL, Model tahmini: 50.000 TL → Loss büyük (kötü)

Farklı problem türleri farklı Loss fonksiyonu kullanır: sayısal tahminlerde (regresyon) genelde
**MSE (Mean Squared Error)**, sınıflandırmada **Cross Entropy** kullanılır.

## Train / Validation / Test Ayrımı

Bir veri setini üçe bölmenin sebebi, modelin **gerçekten öğrenip öğrenmediğini** dürüstçe
ölçebilmektir:

| Küme | Kullanım Amacı | Analoji |
|---|---|---|
| **Train** | Modelin parametrelerini bu veriyle günceller | Ders çalışma kitabındaki sorular |
| **Validation** | Eğitim sırasında modelin ne kadar iyi gittiğini izlemek, hiperparametre seçmek için | Deneme sınavı |
| **Test** | Eğitim tamamen bitince, modelin daha önce hiç görmediği veriyle **son kez** ölçülür | Gerçek final sınavı |

**Kritik kural:** Test verisi eğitim sırasında **asla** kullanılmamalı, hatta hiperparametre
seçerken bile (o iş Validation'ın görevi) bakılmamalıdır — aksi halde model o veriye "alışır" ve
ölçtüğünüz başarı gerçek dünyada tekrarlanmaz (bu duruma **data leakage** denir).

### Overfitting'i Validation ile yakalamak

```
Epoch 10  → Train Loss: 0.40   Validation Loss: 0.42   (ikisi de düşüyor, iyi)
Epoch 30  → Train Loss: 0.10   Validation Loss: 0.15   (hâlâ iyi)
Epoch 60  → Train Loss: 0.02   Validation Loss: 0.35   (Train düşüyor ama Validation yükseliyor!)
```

Epoch 60'ta model artık genelleme yapmayı bırakıp eğitim verisini **ezberlemeye** (overfitting)
başlamıştır — bunu ancak Validation seti sayesinde fark edebiliriz.

## Accuracy Neden Tek Başına Yeterli Değil?

1000 kişilik bir grupta 990 sağlıklı, 10 hasta olsun. Model **herkese** "sağlıklısın" derse
%99 Accuracy elde eder — ama tek bir hastayı bile bulamamıştır, yani model tamamen işe
yaramazdır. Bu yüzden özellikle dengesiz veri setlerinde ek metrikler kullanılır:

- **Precision:** "Hasta" dediklerimin kaçı gerçekten hasta? *(Yanlış alarm oranını gösterir)*
- **Recall:** Gerçek hastaların kaçını yakalayabildim? *(Kaçırma oranını gösterir)*
- **F1 Score:** Precision ve Recall'un dengeli ortalaması

Sağlık, dolandırıcılık tespiti, güvenlik gibi "kaçırmanın maliyeti çok yüksek" olan alanlarda
sadece Accuracy'e bakmak tehlikelidir.
