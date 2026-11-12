# Automatic releases

## 3.0.8 — Denklem eki hesap motoruyla eşleştirildi

JavaScript referans koşularına artık V11 denklem kataloğu ekleniyor. C++ koşuları kendi kataloğunu ve kaynak kopyasını koruyor. Masaüstü paketine V11 kataloğu eklendi; README güncellendi.

Base commit: `60574ac24b8ebbac5b6ec05c84d01d39e9955c0c`. Local tag: `auto/v3.0.8`.

Limitations:

- Hesap modelleri ve kayıt biçimleri değiştirilmedi.
- Masaüstü EXE paketi yeniden üretilmedi; önceki raporlar güncellenmedi.

## 3.0.7 — Markdown raporunda hesap motoru açıklaması düzeltildi

Tek hesap raporu artık kullanılan motoru belirtir. JavaScript referans sonuçlarında yanlış Eigen/Boost.Odeint açıklamaları yerine V11 yöntem açıklaması ve ilgili denklem belgesi gösterilir. README ve regresyon testi güncellendi.

Base commit: `d6497dd9c9ea8efe564960c885ad1faed6b63d71`. Local tag: `auto/v3.0.7`.

Limitations:

- Hesap modelleri ve kayıt biçimleri değiştirilmedi.
- Önceden üretilmiş raporlar güncellenmedi.

## 3.0.6 — Analiz raporlarının SHA-256 doğrulaması düzeltildi

Windows satır sonlarından kaynaklanan hash uyuşmazlığı yeniden üretildi ve giderildi. Manifest ve Markdown raporu artık analysis.json dosyasının gerçek baytlarını doğruluyor. Regresyon testi ve README güncellendi.

Base commit: `2d86aa050c7f2681b799d21cbe67ae76b0ea1ab1`. Local tag: `auto/v3.0.6`.

Limitations:

- Hesap modelleri ve kayıt biçimleri değiştirilmedi.
- Önceden üretilmiş raporlar güncellenmedi.

## 3.0.5 — Boş zaman serisinde hatalı CSV bağlantısı düzeltildi

HTML raporu artık yalnızca zaman serisi örnekleri varsa CSV bağlantısı gösteriyor; örnek yoksa açık bir açıklama sunuyor. Regresyon testi ve README güncellendi.

Base commit: `cf703fcbf87e8ee0d2f0efcaee20eb7da86fe709`. Local tag: `auto/v3.0.5`.

Limitations:

- Hesap modelleri ve kayıt biçimleri değiştirilmedi.
- HTML içeriği otomatik testle doğrulandı; tarayıcıda görsel inceleme yapılmadı.

## 3.0.4 — HTML hesap raporuna açık iptal durumu eklendi

HTML raporu artık CANCELLED/COMPLETED durumunu ve iptal edilen koşuların kısmi sonuç açıklamasını gösteriyor. Regresyon testi ve README güncellendi; sonuç veri biçimi korundu.

Base commit: `30b3ed58ac1f95296a029afe3f21b566c1a871cb`. Local tag: `auto/v3.0.4`.

Limitations:

- Hesap modelleri değiştirilmedi.
- HTML içeriği otomatik testle doğrulandı; tarayıcıda görsel inceleme yapılmadı.

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
