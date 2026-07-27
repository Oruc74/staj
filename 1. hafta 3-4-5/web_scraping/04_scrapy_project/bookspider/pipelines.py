import re

from itemadapter import ItemAdapter


class CleanTextPipeline:
    """Metin alanlarındaki fazla boşlukları temizler, sayfa sayısını int'e çevirir."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in ("baslik", "yazar", "ulke", "konu", "tur",
                      "yayimci", "ozet", "kategori"):
            value = adapter.get(field)
            if isinstance(value, str):
                adapter[field] = " ".join(value.split()).strip()

        sayfa_text = adapter.get("sayfa_sayisi") or ""
        match = re.search(r"(\d+)", sayfa_text.replace(".", ""))
        adapter["sayfa_sayisi"] = int(match.group(1)) if match else None

        return item


class DropMissingTitlePipeline:
    """Başlığı olmayan (bozuk ayrıştırılmış) öğeleri filtreler."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if not adapter.get("baslik"):
            from scrapy.exceptions import DropItem
            raise DropItem("Başlık bulunamadı, öğe atlandı")
        return item


class DuplicatesPipeline:
    """Aynı başlık birden fazla kategori altında keşfedilirse tekrarını at."""

    def __init__(self):
        self.gorulen_basliklar = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        baslik = adapter.get("baslik")
        if baslik in self.gorulen_basliklar:
            from scrapy.exceptions import DropItem
            raise DropItem(f"Tekrar eden roman atlandı: {baslik}")
        self.gorulen_basliklar.add(baslik)
        return item
