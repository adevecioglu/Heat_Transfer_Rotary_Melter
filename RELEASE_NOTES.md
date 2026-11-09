# Automatic releases

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


