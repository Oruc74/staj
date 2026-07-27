# 2. Hafta — Yapay Zekâ Temelleri

Bu hafta hocanın verdiği araştırma görevi kapsamında hazırlanan notlar ve uygulama.
Amaç, "yapay zekâ gerçekten düşünüyor mu, arkada nasıl bir işleyiş var?" sorusuna,
temellerden (istatistik) başlayıp güncel LLM mimarilerine kadar giden bir çizgide cevap
aramak.

## İçindekiler

| # | Dosya | Konu |
|---|---|---|
| 1 | [01_istatistik_temelleri.md](01_istatistik_temelleri.md) | Olasılık/istatistiğin YZ ile bağlantısı — ortalama/medyan/mod, varyans/std sapma, veri dağılımı, dengesizlik, normalizasyon/standardizasyon |
| 2 | [02_notebook_tabanli_programlama.md](02_notebook_tabanli_programlama.md) | Hücre tabanlı programlama nedir, neden önemli, ne zaman notebook ne zaman script tercih edilmeli |
| 3 | [03_ml_temelleri.md](03_ml_temelleri.md) | ML türleri (gözetimli/gözetimsiz/pekiştirmeli), Model/Parametre/Training/Loss, Train-Validation-Test, Precision/Recall/F1 |
| 4 | [04_deep_learning_temelleri.md](04_deep_learning_temelleri.md) | Neural Network, Layer, Weight, Forward Pass, Backpropagation, Gradient Descent, Optimizer, Activation Functions (ReLU/GELU), Batch/Epoch, Overfitting |
| 5 | [05_pytorch_tensorflow_karsilastirma.md](05_pytorch_tensorflow_karsilastirma.md) | PyTorch vs TensorFlow — yapısal farklar, hangi projede hangisi |
| 6 | [06_nlp_ve_transformer_temelleri.md](06_nlp_ve_transformer_temelleri.md) | NLP nedir, Token, Embedding, Positional Encoding, Attention (Q/K/V), Multi-Head Attention, Transformer Block, Token Prediction, "Attention Is All You Need" makalesinin önemi |
| 7 | [07_llm_mimari_karsilastirma.md](07_llm_mimari_karsilastirma.md) | Güncel LLM'lerin kullandığı mimari teknikler (RoPE, GQA/MQA, MoE, Sliding Window Attention, Pre-LN/Post-LN) — avantaj/dezavantajları ve kişisel değerlendirme |
| 8 | [08_huggingface_kesif_notlari.md](08_huggingface_kesif_notlari.md) | HuggingFace Hub keşfi — Models/Datasets/Spaces, güncel trend modeller, pratik faydası |
| 9 | [09_attention_transformer_uygulamasi.ipynb](09_attention_transformer_uygulamasi.ipynb) | **Uygulama:** PyTorch ile sıfırdan Multi-Head Attention + Transformer Block implementasyonu (Positional Encoding → Q/K/V → Multi-Head Attention → Transformer Block → Token Prediction), her adımda `print(tensor.shape)` ile takip edilebilir |

## Okuma Sırası Önerisi

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 sırasıyla okunursa, temelden (istatistik) başlayıp güncel
LLM mimarilerine kadar mantıklı bir çizgi izlenmiş olur. 9 numaralı notebook, 6. dosyada
anlatılan Transformer bileşenlerinin kod karşılığıdır — 6'yı okuduktan sonra notebook'u
çalıştırmak en anlaşılır sırasıdır.

## İlgili Diğer Çalışma

Bu klasörün dışında, aynı hafta kapsamında ayrı bir alıştırma olarak
[`../pytorch_tensor_egzersiz/tensor_reshape.ipynb`](../pytorch_tensor_egzersiz/tensor_reshape.ipynb)
dosyası da hazırlandı — `view`/`reshape`/`contiguous` kavramlarını işleyen bu alıştırma,
9 numaralı notebook'taki tensör manipülasyonlarının ön hazırlığı niteliğindedir.
