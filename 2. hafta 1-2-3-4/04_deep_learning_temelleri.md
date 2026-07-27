# Deep Learning (Derin Öğrenme) Temelleri

Deep Learning, Neural Network (Yapay Sinir Ağı) tabanlı modellerle çalışan bir ML alt dalıdır.
"Derin" kelimesi, ağın birden fazla (çoğu zaman onlarca/yüzlerce) katmandan oluşmasından gelir.

## Neural Network — Genel Yapı

```
Girdi Katmanı (Input Layer)
        ↓
Gizli Katman (Hidden Layer) 1
        ↓
Gizli Katman (Hidden Layer) 2
        ↓
...
        ↓
Çıktı Katmanı (Output Layer)
```

Her katman, bir önceki katmandan gelen sayıları alır, kendi **Weight**'leriyle çarpıp toplar, bir
**Activation Function**'dan geçirir ve sonraki katmana yollar.

### Layer (Katman) Nedir?

Bir katman, girdiyi belirli bir dönüşümden geçiren bir işlem birimidir. Görüntü tanımada
sezgisel bir örnek: ilk katmanlar basit kenar/çizgi desenlerini fark eder, ortadaki katmanlar bu
kenarlardan şekiller (göz, kulak hatları) kurar, son katmanlar bu şekillerden nesneleri
(kedi, köpek) tanır. Modelin "derinliği" arttıkça öğrenebildiği soyutlama seviyesi de artar.

### Weight (Ağırlık) Nedir?

Weight'ler, bir katmandaki her bağlantının "önem derecesini" tutan sayılardır — modelin
eğitim boyunca öğrendiği asıl şey bunlardır. Örneğin bir e-posta spam sınıflandırıcısında
"ücretsiz", "kazandınız" gibi kelimelere karşılık gelen weight'ler yüksek pozitif değerler
alabilir (spam olma ihtimalini artırır), günlük konuşma kelimelerinin weight'i düşük/negatif
kalabilir.

## Forward Pass (İleri Geçiş)

Girdinin, katman katman ilerleyip bir çıktı/tahmin üretmesi sürecidir — modelin "tahmin yapma"
anıdır:

```
Girdi → Katman 1 (Weight'lerle çarp, topla, activation uygula) → Katman 2 → ... → Tahmin
```

## Backpropagation (Geri Yayılım)

Forward Pass sonunda bir Loss (hata) elde ettikten sonra, "bu hataya hangi katmandaki hangi
weight ne kadar sebep oldu?" sorusunun cevabını **sondan başa doğru** hesaplama sürecidir.
Matematiksel olarak zincir kuralı (chain rule) ile Loss'un her bir weight'e göre türevi
(**Gradient**) hesaplanır.

```
Loss
  ↓ (geriye doğru)
Son katmanın weight'lerine olan katkısı hesaplanır
  ↓
Bir önceki katmanın weight'lerine olan katkısı hesaplanır
  ↓
... en baştaki katmana kadar devam eder
```

## Gradient Descent

Gradient (türev), bir weight'i **hangi yönde** değiştirirsek Loss'un azalacağını gösterir.
Gradient Descent ise bu bilgiyi kullanarak weight'leri küçük adımlarla güncelleyen algoritmadır.

**Analoji:** Sisli bir dağda, aşağıyı göremeden en düşük noktaya inmeye çalışıyorsunuz. Tek
yapabileceğiniz, ayağınızın altındaki eğimi hissedip en dik iniş yönüne bir adım atmak — bunu
tekrar tekrar yaparsınız. Gradient, o an ayağınızın altındaki eğimdir; **learning rate** ise
attığınız adımın büyüklüğüdür.

- Learning rate çok büyükse: dağın tepesinden karşı tepeye zıplarsınız, hiç inemezsiniz (kararsız eğitim).
- Learning rate çok küçükse: doğru yöne gidersiniz ama vadiye inmek çok uzun sürer.

## Optimizer

Gradient Descent bize "hangi yöne gidilmeli" bilgisini verir; **Optimizer** ise bu bilgiyi
kullanarak weight'lerin *tam olarak nasıl* güncelleneceğini belirleyen algoritmadır:

| Optimizer | Öne Çıkan Özellik |
|---|---|
| **SGD** | En basit hali; her adımda sabit büyüklükte güncelleme yapar |
| **Adam** | Öğrenme hızını her parametre için ayrı ayrı, verinin geçmişine bakarak otomatik ayarlar — günümüzde en yaygın tercih |
| **AdamW** | Adam + "Weight Decay" (weight'lerin aşırı büyümesini engelleyen bir düzenleme) — özellikle Transformer/LLM eğitiminde standart |

## Activation Functions (Aktivasyon Fonksiyonları)

Eğer katmanlar arasında activation function olmasaydı, art arda gelen doğrusal (linear)
işlemler yine doğrusal bir işleme eşdeğer olurdu — yani ağ ne kadar derin olursa olsun
karmaşık (doğrusal olmayan) örüntüleri asla öğrenemezdi. Activation function, ağa
**doğrusal olmayanlık (non-linearity)** kazandırır.

### ReLU (Rectified Linear Unit)

```
x < 0 için  → 0
x >= 0 için → x
```

Basit, hesaplaması ucuz, çok katmanlı ağlarda uzun süredir standart tercih. Dezavantajı: bir
nöron sürekli negatif girdi alırsa "ölebilir" (gradyanı hep 0 olur, hiç öğrenmez — buna
"dying ReLU" problemi denir).

### GELU (Gaussian Error Linear Unit)

ReLU'nun aksine keskin bir "kes/geçir" kararı vermez; girdinin değerine göre **yumuşak bir
geçiş** uygular — küçük negatif değerlerin bir kısmını da geçirebilir. Bu yumuşaklık, gradyanın
daha istikrarlı akmasını sağladığı için modern Transformer tabanlı modellerde (GPT, BERT gibi)
ReLU yerine tercih edilir.

## Batch ve Epoch

- **Batch:** Modelin tek bir güncelleme adımında gördüğü veri grubudur. 10.000 satırlık bir
  veri setini `batch_size=100` ile eğitirseniz, her epoch 100 güncelleme adımından oluşur.
- **Epoch:** Modelin tüm eğitim verisini **bir kez baştan sona** görmesidir.

```
10.000 örnek, batch_size = 100
   → 1 epoch = 100 batch (100 güncelleme adımı)
   → epochs = 20 dendiğinde, bu 100 adımlık tur 20 kez tekrarlanır
```

Küçük batch: daha az bellek, daha "gürültülü" ama bazen daha iyi genelleyen bir öğrenme.
Büyük batch: daha stabil gradyan tahmini, daha çok bellek, GPU'yu daha verimli kullanır.

## Overfitting ve Train/Validation Loss

Overfitting, modelin eğitim verisindeki **gürültüyü ve özel detayları** dahi ezberlemesi,
bunun sonucunda görmediği veride kötü performans göstermesidir. Bunu erken fark etmenin
en pratik yolu Train Loss ile Validation Loss'u birlikte izlemektir:

```
Epoch  Train Loss   Validation Loss
  5      0.55            0.57        ← ikisi birlikte düşüyor, sağlıklı
 20      0.20            0.22        ← hâlâ sağlıklı
 40      0.05            0.30        ← Train düşmeye devam ediyor ama Validation YÜKSELİYOR
```

40. epoch'ta aradaki makas açılmaya başlamıştır — bu, "artık ezberlemeye geçti, eğitimi
durdurmalıyım (early stopping)" sinyalidir. Overfitting'i azaltmanın yaygın yolları: daha fazla
veri, `dropout` katmanları, weight decay (AdamW), veya basitçe modeli daha erken durdurmak.
