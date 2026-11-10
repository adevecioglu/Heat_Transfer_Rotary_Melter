# Automatic releases

## 3.0.3 — Tek hesap raporlarında iptal durumu görünür hale getirildi

Markdown raporuna CANCELLED/COMPLETED durumu ve iptal edilen koşular için kısmi sonuç açıklaması eklendi. Koşu manifestine cancelled alanı eklendi. Sonuç JSON'u korundu; regresyon testi ve README güncellendi.

Base commit: `1dd2014b9f461afa11cbe7e24c43207c2cb4d73c`. Local tag: `auto/v3.0.3`.

Limitations:

- Hesap modelleri değiştirilmedi.
- Masaüstü görsel testi çalıştırılmadı; değişiklik Markdown ve JSON manifestiyle sınırlı.

## 3.0.2 — Analiz raporlarında iptal durumunun görünürlüğü düzeltildi

İptal edilen analiz koşuları Markdown raporunda CANCELLED olarak gösteriliyor ve kısmi sonuç açıklaması ekleniyor. CSV çıktısına cancelled sütunu eklendi. Hata bilgileri ve JSON biçimi korundu; regresyon testi ve README güncellendi.

Base commit: `e00f47c601420b7ba7a5d0297f73db038cb51e12`. Local tag: `auto/v3.0.2`.

Limitations:

- Masaüstü görsel testi çalıştırılmadı; değişiklik Markdown ve CSV raporlamasıyla sınırlı.
- Hesap modelleri değiştirilmedi.

## 3.0.1 — İptal edilen tek hesap için çıkış kodu düzeltildi

--run, iptal edilmiş hesabın raporunu kaydettikten sonra artık çıkış kodu 1 döndürüyor. Tamamlanıp hedef sıcaklığa ulaşamayan hesaplar başarı kodunu koruyor. README ve regresyon testleri güncellendi.

Base commit: `e109de64a239591f98982e0bbad5a2a99ca19d92`. Local tag: `auto/v3.0.1`.

Limitations:

- İptal sonucu kontrollü test verisiyle doğrulandı; masaüstünde canlı iptal testi yapılmadı.

Included earlier upgrades:

- e109de6 auto: İptal edilen tek hesap için çıkış kodu düzeltildi
- 87c457f auto: Çelişkili hesap komutları engellendi
- 35ea625 auto: Başarısız analizler komut çıkış koduna yansıtıldı
- 475e3f7 auto: Analiz raporlarında başarısız koşular görünür hale getirildi
