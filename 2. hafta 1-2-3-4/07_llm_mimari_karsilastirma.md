# Güncel LLM Mimarilerinin Karşılaştırması

> **Kaynak notu:** Aşağıdaki teknikler (RoPE, GQA/MQA, MoE, Sliding Window Attention vb.)
> ilgili modellerin yayınlanmış teknik raporlarında/makalelerinde açıklanan, genel olarak
> bilinen mimari tercihleridir. Kesin sayısal benchmark skorlarını (ör. "%X SWE-Bench skoru")
> burada iddia etmiyorum çünkü bunlar sürekli güncellenen, sağlamasını doğrudan
> yapamadığım rakamlar — bunun yerine hangi modelin hangi **mimari tekniği** neden tercih
> ettiğine ve bu tercihin ne kazandırıp neden ödün verdiğine odaklandım.

## Ortak Temel

İncelenen tüm güncel büyük dil modelleri (GPT ailesi, Claude ailesi, Gemini ailesi, Llama,
DeepSeek, Qwen, Mistral vb.) temelde aynı iskeleti paylaşır:

```
Tokenization → Embedding → Positional Encoding → [Transformer Block × N] → Next Token Prediction
```

Modeller arasındaki gerçek fark, bu iskeletin **temelinden değil, üzerine eklenen
optimizasyonlardan** gelir. Aşağıda en yaygın/dikkat çekici teknikleri, hangi sorunu çözdükleri
üzerinden karşılaştırıyorum.

## Dikkat Çeken Mimari Teknikler

### 1. Positional Encoding Çeşitleri: Sinüzoidal vs RoPE

Orijinal "Attention Is All You Need" makalesi sabit, öğrenilmeyen sinüzoidal (sin/cos tabanlı)
positional encoding kullanıyordu. Günümüz modellerinin büyoğu çoğunluğu (Llama, Mistral,
Qwen ve birçok açık modelde) **RoPE (Rotary Positional Embedding)** kullanır:

- **Avantajı:** Token'lar arası *göreli* mesafeyi doğal olarak kodlar (mutlak pozisyon yerine),
  bu da modelin eğitimde görmediği uzunluktaki dizilere daha iyi genellemesini sağlar.
- **Dezavantajı:** Standart sinüzoidal kodlamaya göre implementasyonu biraz daha karmaşıktır
  ve çok uzun bağlamlarda (yüz binlerce token) ek düzenlemeler (ör. NTK-aware scaling)
  gerektirebilir.

### 2. Attention Verimliliği: Multi-Head → Multi-Query → Grouped-Query

Standart Multi-Head Attention'da her "head" kendi Key ve Value matrisine sahiptir — bu,
özellikle çıkarım (inference) sırasında bellek (KV cache) açısından pahalıdır. Bu sorunu çözmek
için iki yaygın optimizasyon geliştirildi:

| Teknik | Fikir | Ödün |
|---|---|---|
| **Multi-Query Attention (MQA)** | Tüm head'ler tek bir ortak Key/Value setini paylaşır | Bellek çok azalır, ama model kalitesinde küçük bir kayıp olabilir |
| **Grouped-Query Attention (GQA)** | Head'ler küçük gruplara bölünür, her grup kendi K/V'sini paylaşır | MHA ile MQA arasında bir denge — günümüz büyük modellerinin çoğunda (Llama 2/3 ailesi dahil) tercih edilen yöntem budur |

Bu, "Query-Key-Value" temelinin üzerine kurulan, saf mühendislik/verimlilik odaklı bir
optimizasyona güzel bir örnektir.

### 3. Sparse Mixture of Experts (MoE)

Standart bir Transformer bloğundaki Feed Forward Network, **her token için** aynı ağırlıklarla
çalışır. MoE mimarisinde ise tek bir Feed Forward yerine, birden fazla "uzman" (expert) alt-ağ
bulunur ve her token, küçük bir "yönlendirici (router)" tarafından bu uzmanlardan sadece
birkaçına (ör. 8 uzmandan 2'sine) yönlendirilir.

- **Avantajı:** Modelin toplam parametre sayısı çok büyük olabilir (daha fazla "bilgi kapasitesi"),
  ama her token için gerçekten çalıştırılan (aktifleşen) parametre sayısı çok daha küçük kalır
  — yani "dev bir model gibi bilgili, orta boy bir model gibi hızlı" bir denge kurulur.
- **Dezavantajı:** Eğitimi ve dağıtık altyapısı standart (dense) modellere göre daha karmaşıktır;
  router'ın uzmanlar arası yükü dengeli dağıtması gerekir, aksi halde bazı uzmanlar
  "aç" kalıp yeterince eğitilmez.

### 4. Uzun Bağlam Yönetimi: Sliding Window Attention

Standart self-attention'ın maliyeti dizinin uzunluğunun **karesiyle** (O(n²)) artar — bu, çok
uzun metinlerde (ör. bir kitap) hesaplama maliyetini patlatır. Sliding Window Attention, her
token'ın *tüm* geçmişe değil, sadece yakın bir pencereye (ör. son 4096 token) dikkat etmesini
sağlayarak bu maliyeti doğrusala (O(n)) yaklaştırır; uzak bağlam bilgisi katmanlar üstünden
dolaylı olarak yine de yayılabilir.

- **Avantajı:** Çok daha uzun dizileri, çok daha az bellek/hesaplama ile işleyebilme.
- **Dezavantajı:** Tek bir katmanda çok uzak iki token arasında doğrudan bir ilişki kurulamaz;
  bu bilginin katmanlar arasında "aktarılması" gerekir, bu da bazı görevlerde (çok uzak
  bağlamdaki tek bir detayı hatırlama) MHA'ya göre dezavantajlı olabilir.

### 5. Katman Normalizasyonu Yeri: Post-LN vs Pre-LN

Orijinal Transformer, Layer Normalization'ı alt-katmandan **sonra** uygular (Post-LN). Günümüz
modellerinin çoğu ise normalizasyonu alt-katmandan **önce** uygular (Pre-LN):

- **Pre-LN avantajı:** Çok derin modellerde (onlarca/yüzlerce katman) eğitimi belirgin şekilde
  daha kararlı hale getirir, özel bir "warm-up" ayarına daha az bağımlı kalır.
- **Ödün:** Bazı araştırmalar Pre-LN'in çok derin ağlarda, katmanların etkisini biraz
  "zayıflatabildiğini" (temsil gücünde küçük bir kayba yol açabildiğini) öne sürüyor — bu yüzden
  bazı yeni çalışmalar hibrit (ör. "sandwich" normalizasyon) yaklaşımlar deniyor.

## Genel Gözlem: Rekabet Artık Neyin Üzerinden Şekilleniyor?

Tüm bu teknikler incelendiğinde ortaya çıkan tablo şu: modeller arasındaki fark artık "kim daha
çok parametreye sahip" sorusundan çok, **"aynı hesaplama bütçesiyle kim daha verimli
çalışıyor"** sorusuna kaymış durumda. MoE, GQA, Sliding Window Attention gibi tekniklerin
hepsi aslında aynı temel dengeyi farklı açılardan optimize ediyor: **kalite / hız / bellek
maliyeti** üçgeni.

## Kişisel Değerlendirme: Bana Mantıklı Gelen Kombinasyon

Görevde sorulduğu üzere, öğrendiklerimi birleştirip kendi fikrimi de eklemek istiyorum:

Bana en "dengeli" gelen yaklaşım, **GQA + Sliding Window Attention + MoE**'nin birlikte
kullanılmasıdır — bunların hiçbiri birbirini dışlamaz, aksine tamamlayıcıdır: GQA çıkarım
belleğini düşürür, Sliding Window uzun bağlamı ucuzlatır, MoE ise toplam "bilgi kapasitesini"
aktif hesaplama maliyetini artırmadan büyütür. Bazı açık modellerin (ör. Mistral ailesinin
erken sürümleri) zaten sliding window + GQA kombinasyonunu denediğini biliyorum; MoE'yi de
buna eklemek mantıklı bir sonraki adım gibi duruyor — ki günümüzde birçok büyük model
(Mixtral, DeepSeek-MoE gibi) tam olarak bu yönde ilerliyor.

Üzerinde daha az konuşulan ama ilginç bulduğum bir nokta da şu: **"router'ın kendisinin de
öğrenilebilir olması"** aslında modele "bu soruyu nasıl parçalara böleceğime ben karar
vereyim" gibi bir esneklik veriyor — bu, ileride belki de "hangi katmanların hangi görev için
gerekli olduğuna modelin kendisinin karar verdiği" daha dinamik mimarilere (statik katman
sayısı yerine, girdiye göre değişen "derinlikte" işlem yapan modellere) evrilebilir gibi
görünüyor. Bu, benim şu an literatürde net bir standardı olmadığını düşündüğüm, ama
mantıklı bulduğum bir yön.
