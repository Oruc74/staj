# 3. Hafta (Gün 2) — PyTorch Görev 3: Mini-Beyin (nn.Module)

PyTorch modellerinin nesne yönelimli (OOP) nasıl yazıldığını, `nn.Module`'den
türeyen basit bir MLP (`MiniBrain`) örneğiyle incelediğim notebook.

## İçindekiler

| Dosya | Konu |
|---|---|
| [gorev3_mini_beyin.ipynb](gorev3_mini_beyin.ipynb) | `nn.Module`'den türeyen `MiniBrain` sınıfı (3 `nn.Linear` katmanı + `F.relu`), `print(model)` ile mimari özeti, örnek girdi-çıktı testi, `forward` metodunun önemi üzerine değerlendirme |

## Gereksinimler

```powershell
pip install torch
```

## Nasıl Çalıştırılır

```powershell
jupyter notebook gorev3_mini_beyin.ipynb
```

veya VS Code'da açıp hücreleri sırayla çalıştır.
