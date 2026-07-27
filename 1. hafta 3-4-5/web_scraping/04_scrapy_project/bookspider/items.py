import scrapy


class BookItem(scrapy.Item):
    baslik = scrapy.Field()
    yazar = scrapy.Field()
    ulke = scrapy.Field()
    konu = scrapy.Field()
    tur = scrapy.Field()
    yayim_yili = scrapy.Field()
    yayimci = scrapy.Field()
    sayfa_sayisi = scrapy.Field()
    isbn = scrapy.Field()
    ozet = scrapy.Field()
    kategori = scrapy.Field()
    detail_url = scrapy.Field()
