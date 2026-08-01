# Olasılık ve İstatistiğin Yapay Zeka ile Bağlantısı

## Bağlantı nereden geliyor?

Bir modelin "öğrenmesi" aslında elindeki veriden bir **olasılık dağılımı çıkarma** işidir. Bir
görüntü sınıflandırıcı "%92 kedi" dediğinde, bu doğrudan bir olasılık değeridir. Bir dil modeli
bir sonraki kelimeyi tahmin ederken de aslında "sözlükteki her kelimenin bu bağlamda gelme
olasılığı nedir?" sorusuna cevap arar (softmax çıktısı = bir olasılık dağılımı).

İstatistik ise bu sürecin **öncesinde ve sonrasında** devreye girer:

- **Öncesinde (veri anlama):** Modeli eğitmeden önce verinin nasıl dağıldığını, dengesiz olup
  olmadığını, aykırı değer barındırıp barındırmadığını bilmeden model kurmak, "körlemesine"
  eğitim yapmaktır.
- **Sırasında (Loss ve Gradient):** Loss fonksiyonları (ör. Cross Entropy) doğrudan olasılık
  teorisinden gelir — model tahminiyle gerçek dağılım arasındaki "uzaklığı" ölçer.
- **Sonrasında (değerlendirme):** Bir modelin gerçekten iyi olup olmadığını anlamak
  (Accuracy, Precision, Recall, güven aralıkları) yine istatistiksel araçlarla yapılır.

Kısacası: **Olasılık ve istatistik, YZ'nin "dili"dir.** Bir mühendis olarak bu dili bilmeden bir
modelin çıktısını "gerçekten güvenilir mi, yoksa şans eseri mi doğru çıktı?" diye sorgulayamazsınız.

---

## Temel Kavramlar

### Merkezi Eğilim Ölçüleri

| Kavram | Ne yapar | Örnek |
|---|---|---|
| **Ortalama (Mean)** | Tüm değerlerin toplamı / eleman sayısı | `[10,20,30,40,50]` → 30 |
| **Medyan (Median)** | Sıralanmış verinin ortanca değeri | `[10,20,30,40,1000]` → 30 (ortalama 220 olurdu, yanıltıcı!) |
| **Mod (Mode)** | En sık tekrar eden değer | `[1,2,2,2,3]` → 2 |

**Neden ikisi de gerekli?** Ortalama, aykırı değerlerden (outlier) kolayca etkilenir. Bir veri
setinde 9 kişi 20.000 TL, 1 kişi 5.000.000 TL maaş alıyorsa, ortalama "yanıltıcı bir zenginlik"
gösterir; medyan gerçek tabloyu daha iyi yansıtır. Bir ML mühendisi olarak veri setinizin
"tipik" bir örneğini merak ettiğinizde önce medyana bakmak daha güvenlidir.

### Yayılım (Dağılım) Ölçüleri

**Varyans**, verilerin ortalamadan ne kadar uzaklaştığının karesidir; **standart sapma**
(varyansın karekökü) ise aynı bilgiyi orijinal birimde verir — bu yüzden pratikte daha çok
standart sapma kullanılır.

```
Veri: [48, 49, 50, 51, 52]  → düşük std sapma (veriler sıkı kümelenmiş)
Veri: [10, 30, 50, 70, 90]  → yüksek std sapma (veriler dağınık)
```

Bu neden önemli? Bir özelliğin (feature) standart sapması çok küçükse, o özellik model için
neredeyse "sabit" demektir ve ayırt edici bilgi taşımayabilir. Standart sapması aşırı büyük
özellikler ise modelin öğrenmesini "domine edip" diğer özellikleri gölgede bırakabilir — bu
yüzden normalizasyon/standardizasyon gerekir (aşağıda).

### Veri Dağılımı ve Dengesizlik

Bir veri setinin sınıflara göre nasıl dağıldığına bakmak kritik önemdedir. Örneğin bir dolandırıcılık
tespit modelinde 100.000 işlemden sadece 200'ü dolandırıcılık ise (**dengesiz veri seti /
imbalanced dataset**), model "hiçbir zaman dolandırıcılık yok" dese bile %99.8 doğruluk (accuracy)
elde eder — ama bu model tamamen işe yaramazdır. Bu yüzden yalnızca Accuracy'e bakmak
yeterli değildir (bkz. `03_ml_temelleri.md` içindeki Precision/Recall bölümü).

### Normalizasyon vs Standardizasyon

Bu iki kavram sıkça karıştırılır:

| | Normalizasyon | Standardizasyon |
|---|---|---|
| **Ne yapar** | Değerleri sabit bir aralığa (genelde [0,1]) sıkıştırır | Ortalamayı 0, std sapmayı 1 yapar |
| **Formül** | `(x - min) / (max - min)` | `(x - ortalama) / std_sapma` |
| **Ne zaman tercih edilir** | Değerlerin sınırları biliniyorsa (ör. piksel değerleri 0-255) | Dağılım normale yakınsa, aykırı değer az ise |

Bir Transformer modelinde embedding vektörlerinin makul bir ölçekte kalması (patlamaması
veya sıfıra yakınsamaması) için **Layer Normalization** kullanılır — bu da aslında
standardizasyonun katman bazında, öğrenilebilir parametrelerle yapılan bir versiyonudur. Yani
istatistikteki bu basit kavram, doğrudan Transformer mimarisinin içine gömülü durumda
(bkz. `06_nlp_ve_transformer_temelleri.md`).

---

## Özet

Modern bir YZ modelinin eğitim döngüsü aslında uçtan uca istatistiksel bir süreçtir:

```
Ham veri
  → İstatistiksel analiz (dağılım, aykırı değer, dengesizlik kontrolü)
  → Normalizasyon/Standardizasyon
  → Model (olasılık tahmini üretir)
  → Loss (olasılık farkını ölçer)
  → Değerlendirme (Accuracy/Precision/Recall — yine istatistik)
```

Bu yüzden olasılık ve istatistik, "ayrı bir ders" gibi görünse de aslında makine öğrenmesinin
temel dilidir; üstüne inşa edilen her şey (Loss fonksiyonları, değerlendirme metrikleri,
normalizasyon teknikleri, hatta modelin ürettiği "tahmin" kavramının kendisi) bu temelden gelir.
