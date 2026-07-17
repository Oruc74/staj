"""
Türk Romanları - Scrapy Spider
=================================
Hedef Site : https://tr.wikipedia.org (Kategori:Türk romanları)
Yöntem     : Scrapy — kategori + alt kategori gezinmesi
Açıklama   : "Kategori:Türk romanları" ana kategorisinden başlar, hem
             doğrudan üye roman sayfalarını hem de bir seviye altındaki
             alt kategorilerin (ör. "20. yüzyıl Türk romanları",
             "Klasik Türk romanları") üye sayfalarını takip eder. Her
             roman sayfasının infobox'ından yazar, yayım yılı, yayımcı,
             sayfa sayısı, ISBN bilgilerini ve özet paragrafını çıkarır.

             01_requests_beautifulsoup/books_scraper.py ile aynı ana
             kategoriyi hedefler, ancak o script'in aksine burada
             Scrapy'nin otomatik istek kuyruğu sayesinde alt
             kategoriler de takip edilerek daha geniş bir veri seti
             toplanır — bu da Scrapy'nin çoklu sayfa/kategori gezinmesi
             gerektiren işlerde requests+BS4'e göre ne kadar az kodla
             daha fazlasını yapabildiğini gösterir.
"""

import scrapy

from bookspider.items import BookItem

# Roman içeriğiyle doğrudan ilgisiz alt kategorileri (film/dizi uyarlamaları,
# roman serileri listesi vb.) dışarıda bırakıyoruz — amaç roman *makalelerini*
# toplamak, türev medya kategorilerini değil.
HARIC_TUTULAN_ALT_KATEGORILER = {
    "türk romanlarından uyarlanan filmler",
    "türk romanlarından uyarlanan televizyon dizileri",
    "türk roman serileri",
    "diziye uyarlanmış türk romanları",
}

INFOBOX_ALAN_HARITASI = {
    "yazar": "yazar",
    "ülke": "ulke",
    "konu": "konu",
    "tür": "tur",
    "yayım": "yayim_yili",
    "yayımlanma tarihi": "yayim_yili",
    "yayımcı": "yayimci",
    "sayfa": "sayfa_sayisi",
    "isbn": "isbn",
}


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["tr.wikipedia.org"]
    start_urls = [
        "https://tr.wikipedia.org/wiki/Kategori:T%C3%BCrk_romanlar%C4%B1"
    ]

    def parse(self, response, derinlik=0):
        """Kategori sayfasındaki roman linklerini ve alt kategorileri işler."""
        # Kategori başlığı da (roman başlıkları gibi) iç içe <span> etiketleri
        # içinde geliyor, bu yüzden ::text yerine tüm alt metinleri birleştiriyoruz.
        kategori_adi = "".join(
            response.css("#firstHeading ::text").getall()
        ).replace("Kategori:", "").strip()

        # Doğrudan üye roman sayfaları
        sayfa_linkleri = response.css("#mw-pages .mw-category-group ul li a")
        for link in sayfa_linkleri:
            yield response.follow(
                link,
                callback=self.parse_roman,
                cb_kwargs={"kategori": kategori_adi},
            )

        # Bir seviye altındaki alt kategorileri takip et (daha derine inme)
        if derinlik == 0:
            alt_kategori_linkleri = response.css(
                "#mw-subcategories .CategoryTreeItem a"
            )
            for link in alt_kategori_linkleri:
                ad = link.css("::text").get("").strip().lower()
                href = link.attrib.get("href", "")
                if not ad or not href or ad in HARIC_TUTULAN_ALT_KATEGORILER:
                    continue
                yield response.follow(
                    link,
                    callback=self.parse,
                    cb_kwargs={"derinlik": derinlik + 1},
                )

        # Kategori sayfalama ("sonraki sayfa" linki — büyük kategorilerde olur)
        sonraki = response.css("a:contains('sonraki sayfa')::attr(href)").get()
        if sonraki:
            yield response.follow(
                sonraki, callback=self.parse, cb_kwargs={"derinlik": derinlik}
            )

    def parse_roman(self, response, kategori):
        """Roman detay sayfasından infobox ve özet bilgilerini çıkarır."""
        item = BookItem()

        # Roman adları Vikipedi'de genelde <i> içinde italik yazılır
        # (ör. <h1 id="firstHeading"><i>Cemo</i> (roman)</h1>), bu yüzden
        # "::text" tek başına sadece <i> DIŞINDAKİ metni yakalar. Tüm
        # metin düğümlerini birleştirmek gerekir.
        baslik_parcalari = response.css("#firstHeading ::text").getall()
        if not baslik_parcalari:
            baslik_parcalari = response.css("#firstHeading::text").getall()
        item["baslik"] = " ".join(baslik_parcalari).split(" (roman)")[0].strip()
        item["kategori"] = kategori
        item["detail_url"] = response.url

        for alan in set(INFOBOX_ALAN_HARITASI.values()):
            item[alan] = ""

        for row in response.css("table.infobox tr"):
            th_text = " ".join(row.css("th ::text").getall()).strip().lower()
            alan = INFOBOX_ALAN_HARITASI.get(th_text)
            if alan and not item.get(alan):
                td_text = " ".join(row.css("td ::text").getall()).strip()
                item[alan] = td_text

        # İlk anlamlı paragrafı özet olarak al
        ozet = ""
        for p in response.css("#mw-content-text .mw-parser-output > p"):
            metin = " ".join(p.css("::text").getall()).strip()
            if len(metin) > 30:
                ozet = metin
                break
        item["ozet"] = ozet[:400]

        yield item
