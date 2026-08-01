# 3. Hafta (Gün 1) — PyTorch Görev 2: Gizli Formülü Bul

PyTorch'un temel öğrenme mekanizmasını (forward pass, backward pass, parametre
güncelleme) sıfırdan bir training loop yazarak uygulamalı incelediğim notebook.

## İçindekiler

| Dosya | Konu |
|---|---|
| [gorev2_gizli_formul.ipynb](gorev2_gizli_formul.ipynb) | `Y = 3X + 2` gizli formülünü, sentetik veri + `nn.Linear` + `MSELoss` + `SGD` ile 1000 epoch'ta öğretme; eğitim öncesi/sonrası görselleştirme |

## Gereksinimler

```powershell
pip install torch matplotlib
```

## Nasıl Çalıştırılır

```powershell
jupyter notebook gorev2_gizli_formul.ipynb
```

veya VS Code'da açıp hücreleri sırayla çalıştır. Not: `torch.manual_seed(42)`
kullanıldığı için her çalıştırmada aynı sonuçlar (weight≈3.00, bias≈2.00) çıkar.
