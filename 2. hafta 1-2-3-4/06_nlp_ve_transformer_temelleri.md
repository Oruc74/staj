# NLP ve Transformer Mimarisinin Temelleri

## NLP (Doğal Dil İşleme) Nedir?

NLP (Natural Language Processing), bilgisayarların insan dilini (metni, konuşmayı) anlaması,
işlemesi ve üretmesini sağlayan yapay zekâ alt dalıdır. Çeviri, özetleme, duygu analizi, arama
motorları, sesli asistanlar, chatbot'lar — hepsi NLP'nin uygulama alanlarıdır.

### Günümüz Yapay Zekâlarıyla Farkı ve Ortak Yanı

"NLP" ile "günümüzün yapay zekâları" (ChatGPT, Claude gibi büyük dil modelleri) aynı şey
değildir ama iç içe geçmiş durumdadır:

- **Ortak yan:** Büyük dil modelleri (LLM), aslında NLP alanının **en gelişmiş uygulamasıdır**.
  Temelde hâlâ "metni anlama ve üretme" işini yaparlar — sadece bunu eskiye göre çok daha
  büyük ölçekte ve çok daha genel amaçlı yaparlar.
- **Fark:** Klasik NLP sistemleri genelde **tek bir göreve özelleşmiş** modellerdi (sadece
  duygu analizi yapan bir model, sadece çeviri yapan ayrı bir model gibi). Günümüz LLM'leri
  ise tek bir model ile onlarca farklı dil görevini (çeviri, özetleme, kod yazma, muhakeme)
  aynı anda yapabiliyor — çünkü hepsi aynı temel yeteneğe (bir sonraki token'ı doğru tahmin
  etmeye) dayanıyor ve bu yetenek, yeterince büyük ölçekte, şaşırtıcı bir genel yeteneğe
  dönüşüyor.

Kısacası: LLM'ler "NLP'nin yerini alan farklı bir şey" değil, **NLP problemine devasa ölçekte,
tek bir mimariyle (Transformer) çözüm bulan yaklaşımdır.**

## Token Nedir?

Bir dil modeli, metni doğrudan harf harf ya da kelime kelime değil, **token** adı verilen
alt-birimler halinde işler. Token bazen tam bir kelime, bazen bir kelimenin parçası, bazen tek
bir karakter olabilir:

```
"kitaplarımızdan" → ["kitap", "ları", "mız", "dan"]   (örnek bölünme, gerçek tokenizer'a göre değişir)
"hello"           → ["hello"]                          (yaygın bir kelime, tek token olabilir)
```

Neden kelime yerine alt-kelime (subword) birimleri kullanılır? Çünkü:
- Kelime bazlı yaklaşımda sözlük çok büyür ve hiç görülmemiş kelimelerde model çaresiz kalır.
- Karakter bazlı yaklaşımda diziler çok uzar, model uzun bağlamı takip etmekte zorlanır.
- Subword tokenization (BPE, WordPiece gibi algoritmalar), bu ikisi arasında bir denge kurar:
  sık kullanılan kelimeler tek token, nadir/bilinmeyen kelimeler parçalara bölünür.

Türkçe gibi eklemeli dillerde bu özellikle önemlidir — "kitap", "kitaplar", "kitaplarımızdan"
gibi tek bir kökten türeyen onlarca kelime, subword sayesinde ortak bir "kitap" token'ını
paylaşabilir.

## Embedding Nedir?

Bir model matematiksel işlem yapar; ama token'lar birer metin parçasıdır, sayı değildir. Embedding,
her token'ı **sabit uzunlukta bir sayı vektörüne** (örn. 768 boyutlu) çeviren bir dönüşümdür.

```
"kral"    → [0.12, -0.45, 0.98, ..., 0.03]   (ör. 768 sayı)
"kraliçe" → [0.15, -0.40, 0.91, ..., 0.02]   (anlamca yakın → vektörleri de yakın)
"muz"     → [-0.80, 0.11, -0.33, ..., 0.67]  (anlamca uzak → vektörü de uzak)
```

Bu vektörler rastgele değildir — eğitim sırasında öğrenilir, öyle ki **anlamca yakın kelimelerin
vektörleri de vektör uzayında birbirine yakın** düşer. Ünlü örnek: `vektör("kral") - vektör("erkek")
+ vektör("kadın") ≈ vektör("kraliçe")` — embedding uzayı, kelimeler arası anlamsal ilişkileri
geometrik ilişkilere dönüştürür.

`tensor_reshape.ipynb` alıştırmasındaki `(32, 10, 64)` boyutlu örnek tensörün üçüncü boyutu
(64) tam olarak bu embedding boyutuna karşılık geliyordu — yani o alıştırma aslında "10
token'lık, her biri 64 boyutlu embedding'e sahip 32 cümlelik bir batch" üzerinde çalışıyordu.

---

## Transformer Mimarisi

### Neden Geliştirildi?

2017 öncesinde metin işlemede baskın yaklaşım RNN/LSTM idi — bu modeller cümleyi kelime
kelime, **sırayla** işlerdi. Bunun iki büyük sorunu vardı:

1. **Paralelleştirilemez:** Her kelime bir öncekinin işlenmesini beklediği için eğitim yavaştı.
2. **Uzun mesafeli bağımlılık kaybı:** Cümlenin başındaki bir bilginin, cümle uzadıkça sona
   ulaşana kadar "unutulması" (vanishing gradient) yaygın bir sorundu.

2017'de Google'ın yayınladığı **"Attention Is All You Need"** makalesi, RNN'leri tamamen
devre dışı bırakıp yerine **Self-Attention** mekanizmasını koydu — bu, NLP tarihinin dönüm
noktalarından biri kabul edilir (aşağıda ayrı başlıkta ele alınıyor).

### Positional Encoding — Sıra Bilgisi Nereden Geliyor?

Transformer tüm token'ları **paralel/aynı anda** işlediği için, RNN'in aksine, kelimelerin hangi
sırada geldiği bilgisi doğal olarak modelde yoktur. Oysa sıra anlamı değiştirir:

```
"Ali Ayşe'yi gördü."  ≠  "Ayşe Ali'yi gördü."
```

Bunu telafi etmek için her token'ın embedding vektörüne, o token'ın cümledeki **konumunu**
kodlayan ek bir vektör (Positional Encoding) toplanır. Böylece model hem "bu kelime ne"
hem de "bu kelime kaçıncı sırada" bilgisini aynı vektörde taşır.

### Attention — Query, Key, Value (Q, K, V)

Self-Attention'ın özü şu soruya cevap aramaktır: **"Bu kelimeyi anlamlandırırken cümledeki
hangi diğer kelimelere ne kadar dikkat etmeliyim?"**

Bunu yapmak için her token'ın embedding'i üç farklı öğrenilmiş matrisle çarpılarak üç farklı
vektöre dönüştürülür:

| Vektör | Rolü (analoji) |
|---|---|
| **Query (Sorgu)** | "Ben ne arıyorum?" — bu token'ın bakış açısından bir soru |
| **Key (Anahtar)** | "Ben neyim, ne sunuyorum?" — her token'ın kendini tanıttığı etiket |
| **Value (Değer)** | "Eğer bana dikkat edersen, sana vereceğim asıl bilgi bu" |

Somut örnek — **"Ali kitabı Ayşe'ye verdi çünkü o okumayı seviyordu."** cümlesinde "o"
kelimesinin Query'si, cümledeki her kelimenin Key'i ile karşılaştırılır (nokta çarpımıyla bir
"benzerlik skoru" hesaplanır). "o" ile "Ayşe" arasındaki skor, "o" ile "kitabı" arasındaki
skordan daha yüksek çıkar — çünkü anlamca "o"nun kime işaret ettiği daha çok "Ayşe"ye
yakındır. Bu skorlar softmax'tan geçirilip ağırlık haline getirilir ve her token'ın Value'su bu
ağırlıklarla toplanarak "o" kelimesinin yeni, bağlam-farkında temsili elde edilir.

```
Attention(Q, K, V) = softmax( (Q · Kᵀ) / √d_k ) · V
```

(`√d_k` ile bölme, sadece skorların çok büyümesini/softmax'ın aşırı keskinleşmesini önleyen
bir ölçekleme adımıdır.)

### Multi-Head Attention

Tek bir attention hesabı, tek bir "ilişki türünü" yakalamaya eğilimlidir. **Multi-Head Attention**,
aynı işlemi **paralel olarak birden fazla kez, farklı öğrenilmiş Q/K/V matrisleriyle** yapar — her
"head" farklı bir ilişki türüne odaklanabilir (biri gramer ilişkisine, biri konu-nesne ilişkisine,
biri uzak bağlama vb.). Sonunda tüm head'lerin çıktıları birleştirilip (concat) tek bir vektöre
indirgenir.

```
Head 1: "o" ile hangi kelime arasında zamir-referans ilişkisi var?
Head 2: "o" ile hangi kelime dilbilgisel olarak ilişkili (özne-yüklem)?
Head 3: ...
   → hepsi birleştirilip tek bir zengin temsil elde edilir
```

### Transformer Block

Bir Transformer bloğu, Multi-Head Attention'ın etrafına şu bileşenleri ekler:

- **Layer Normalization:** Her katmandan sonra değerlerin ölçeğini stabilize eder (bkz.
  `01_istatistik_temelleri.md`'deki standardizasyon kavramı — burada katman bazında,
  öğrenilebilir parametrelerle uygulanır). Derin ağlarda eğitimi kararlı hale getirir.
- **Feed Forward Network:** Attention'dan çıkan her token temsili, kendi başına (diğer
  token'lardan bağımsız) küçük bir tam bağlantılı ağdan (genelde iki Linear katman + GELU
  aktivasyonu) geçirilerek ek bir dönüşüme uğrar.
- **Residual (Add) Connection:** Her alt bloğun girdisi, çıktısına doğrudan eklenir
  (`çıktı = alt_katman(x) + x`). Bu, derin ağlarda bilginin/gradyanın kaybolmadan akmasını
  sağlayan basit ama kritik bir tekniktir.

```
x  → Multi-Head Attention → Add(x) → Layer Norm → Feed Forward → Add → Layer Norm → sonraki bloğa
```

Bir Transformer modeli, bu bloklardan onlarca/yüzlerce tanesini üst üste dizerek oluşturulur.

### Token Prediction (Bir Sonraki Token'ı Tahmin Etme)

GPT tarzı (decoder-only) bir Transformer'ın nihai görevi basittir: elindeki token dizisine
bakarak **bir sonraki token'ın ne olacağını tahmin etmek**. Son Transformer bloğunun çıktısı,
bir Linear katmandan ve softmax'tan geçirilerek sözlükteki her token için bir olasılık üretir; en
yüksek olasılıklı (veya olasılıklara göre örneklenen) token bir sonraki kelime olarak seçilir ve
süreç bir sonraki adım için tekrarlanır. "Sohbet eden bir yapay zekâ" dediğimiz şey, aslında bu
basit adımın milyonlarca kez, çok büyük bir ölçekte tekrarlanmasından ibarettir.

---

## "Attention Is All You Need" Makalesinin Önemi

2017'de Google araştırmacıları tarafından yayınlanan bu makale, adının da iddia ettiği gibi
"tekrarlayan (recurrent) veya evrişimli (convolutional) katmanlara hiç ihtiyaç yok, sadece
attention mekanizması yeterli" tezini savundu ve bunun pratikte çalıştığını gösterdi.

**Neden devrim niteliğinde kabul edilir?**

1. **Paralelleştirme:** RNN'lerin aksine tüm token'lar aynı anda işlenebildiği için eğitim GPU'lar
   üzerinde çok daha hızlı ölçeklenebildi — bu da "daha büyük modeli, daha büyük veriyle,
   makul sürede eğitebilme" kapısını açtı. Günümüzün "büyük dil modeli" çağı, teknik olarak
   bu paralelleştirme kabiliyeti üzerine kuruludur.
2. **Uzun bağlam:** Self-Attention, iki token arasındaki mesafeden bağımsız olarak (cümlenin
   başı ile sonu arasında bile) doğrudan bir ilişki kurabilir — RNN'lerde bu mesafe arttıkça
   bilgi zayıflardı.
3. **Genellik:** Aynı mimari, ufak değişikliklerle hem çeviri (encoder-decoder), hem metin
   üretme (decoder-only, GPT ailesi), hem de metin anlama (encoder-only, BERT ailesi)
   görevlerine uyarlanabildi. Bugün NLP'nin ötesinde görüntü (Vision Transformer), ses,
   hatta protein yapısı tahmini (AlphaFold) gibi alanlarda da aynı temel mimari kullanılıyor.

Makaleyi kelime kelime anlamaya çalışmak yerine çıkardığım temel sonuç şu: **Attention Is All
You Need, "dizisel veriyi işlemek için sıraya bağlı kalmak zorunda değiliz" fikrini kanıtlayarak,
hem eğitimi radikal biçimde hızlandırdı hem de tek bir mimarinin neredeyse tüm modalitelere
(metin, görüntü, ses) uyarlanabilir olduğunu gösterdi — bugünkü "temel model (foundation
model)" çağının teknik temelini attı.**
