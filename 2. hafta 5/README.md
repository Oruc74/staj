# 2. Hafta (Gün 5) — PyTorch Tensör Boyutu Manipülasyonu

Transformer mimarisinde sık karşılaşılan bir problemin (`Linear` katmanının 2
boyutlu girdi beklemesi, verinin ise `(batch, sequence, embedding)` şeklinde 3
boyutlu olması) uygulamalı incelendiği tek bir notebook.

## İçindekiler

| Dosya | Konu |
|---|---|
| [tensor_reshape.ipynb](tensor_reshape.ipynb) | `(32,10,64)` → `(320,64)` → matris çarpımı → `(32,10,128)`; `view()` ve `reshape()` farkı, `contiguous` kavramı |

## Gereksinimler

```powershell
pip install torch
```

## Nasıl Çalıştırılır

```powershell
jupyter notebook tensor_reshape.ipynb
```

veya VS Code'da açıp hücreleri sırayla çalıştır.
