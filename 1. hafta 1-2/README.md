# 1. Hafta (Gün 1-2) — Python Temelleri, JSON, NoSQL

Bu klasör stajın ilk iki gününde işlenen konuların dosyalarını içerir: Numpy ve
Nesne Yönelimli Programlama (OOP), ardından JSON formatı ve örnek bir NoSQL
(MongoDB tarzı) veri yapısı incelemesi.

## İçindekiler

| Dosya | Konu |
|---|---|
| [acıklama.md](acıklama.md) | Numpy ve JSON hakkında özet "hap bilgi" notları |
| [numpy.py](numpy.py) | Numpy dizileri, homojenlik kuralı, vektörizasyon, shape/reshape |
| [oop.py](oop.py) | `MailAssistant` sınıfı üzerinden OOP kavramları (`__init__`, metotlar, veri yapıları) |
| [ornek.js](ornek.js) | JSON'ın ne işe yaradığını anlatan örnek bir JS dosyası |
| [SQLQuery1.sql](SQLQuery1.sql) | Boş — bu dosya kullanılmadı |
| [universiteDB.ogrenciler.json](universiteDB.ogrenciler.json) | Örnek NoSQL koleksiyonu — öğrenci belgeleri (şema esnekliği örneği) |
| [universiteDB.addresses.json](universiteDB.addresses.json) | `ogrenciler` koleksiyonundaki `adresId` alanının referans verdiği ikinci koleksiyon |

## Gereksinimler

- **Python 3** + **numpy** (sadece `numpy.py` için)
- `oop.py` için ek bir kütüphane gerekmez (saf Python)
- `ornek.js` çalıştırmak istersen **Node.js** gerekir; ama bu dosya sadece
  okuma/anlama amaçlı, çalıştırmak şart değil
- JSON dosyaları düz metin editörüyle okunabilir

```powershell
pip install numpy
```

## Nasıl Çalıştırılır

```powershell
python numpy.py
python oop.py
```

`ornek.js` çalıştırmak istersen (opsiyonel):

```powershell
node ornek.js
```
