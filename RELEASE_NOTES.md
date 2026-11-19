# Automatic releases

## 3.0.21 — Analiz raporuna genel hata durumu eklendi

Markdown raporu, başarısız koşu içeren analizlerde sonuç tablosunun üstünde `FAILED` gösteriyor. İptal bildirildiğinde genel durum `CANCELLED` olarak kalıyor ve başarısız koşular tabloda ayrıca işaretleniyor.

Base commit: `e6b4046f497a64afe6c6816a247018ccb478c8d8`. Local tag: `auto/v3.0.21`.

Limitations:

- Genel hata durumu kontrollü rapor verileriyle doğrulandı. Masaüstü öz sınaması çalıştırılmadı.

## 3.0.20 — Analiz raporuna son çekirdek sıcaklığı ve ısı kaybı eklendi

Markdown analiz tablosu, CSV’de zaten bulunan son çekirdek sıcaklığını °C ve ısı kaybını kWh cinsinden gösteriyor. Eksik sayısal değerler uzun çizgiyle, sıfır değerleri 0 olarak gösteriliyor.

Base commit: `1bcd3af0e57e3ba62f03a74cfb19dab878c11f1a`. Local tag: `auto/v3.0.20`.

Limitations:

- Rapor değerleri kontrollü test verileriyle doğrulandı. Masaüstü öz sınaması çalıştırılmadı.

## 3.0.19 — `--require-gpu` için `--self-test` zorunlu

Başlatıcı, `--require-gpu` seçeneği tek başına veya başka bir işlemle verildiğinde işlem başlamadan açıklayıcı bir hata ve çıkış kodu 2 döndürüyor. `--self-test` ile birlikte kullanıldığında seçenek masaüstü öz sınamasına iletiliyor. Kullanım kuralı README’ye eklendi.

Base commit: `a9c9a14e1ba43d863dc737be539fade48785e40f`. Local tag: `auto/v3.0.19`.

Limitations:

- Masaüstü çağrısı testte taklit edildi. WebView2 öz sınaması ve NVIDIA alan denetimi çalıştırılmadı.
- PowerShell yürütme politikası `AKTIF_ET.ps1` betiğini engelledi. Kontroller proje sanal ortamındaki Python çalıştırılabilir dosyasıyla doğrudan yürütüldü.

## 3.0.18 — Koşu iptali analiz manifestine yansıtılıyor

Motor analizin tamamı veya herhangi bir koşu için iptal bildirdiğinde Markdown raporu genel durumu `CANCELLED` olarak gösteriyor ve manifestte `cancelled: true` yazılıyor. Hem hata hem iptal bildiren koşular tabloda `FAILED` olarak gösterilmeye devam ediyor.

Base commit: `9320e61765db3e3f42e9fe37f149b6b92745d848`. Local tag: `auto/v3.0.18`.

Limitations:

- Kontroller başsız yürütüldü. WebView2 masaüstü testi çalıştırılmadı.
- PowerShell yürütme politikası `AKTIF_ET.ps1` betiğini engelledi. Kontrollerde proje sanal ortamının Python çalıştırılabilir dosyası doğrudan kullanıldı.

## 3.0.17 — Güç boyutlandırmasında iptal doğru raporlanıyor

C++ motoru, üst güç sınırındaki çözüm iptal edildiğinde veya arama ara adımlarda durdurulduğunda `cancelled: true` döndürüyor. İptal edilen arama için güç tahmini ya da hedefe ulaşılamadı sonucu üretilmiyor. Denklem kataloğu yeni davranışı açıklıyor.

Base commit: `e43ced4988847d4e49dcbe974b3d3579018814a8`. Local tag: `auto/v3.0.17`.

Limitations:

- Kontroller başsız yürütüldü. Masaüstü WebView2 testi çalıştırılmadı.
- PowerShell yürütme politikası `AKTIF_ET.ps1` betiğini engelledi. Kontrollerde proje sanal ortamındaki çalıştırılabilir dosyalar doğrudan çağrıldı.

## 3.0.16 — JavaScript koşularında C++ seçenekleri reddediliyor

JavaScript referans koşusunda `--integrator`, `--threads` veya `--water-model` açıkça verilirse komut, senaryoyu okumadan ilgili seçeneği bildiriyor ve çıkış kodu 2 döndürüyor. JavaScript motoruyla analiz isteği de senaryo okunmadan reddediliyor. README yeni davranışı açıklıyor.

Base commit: `f5cfd81240e0bdb3fcbdcfb2bcbaec24d28a3f0e`. Local tag: `auto/v3.0.16`.

Limitations:

- Değişiklik komut satırı doğrulamasıyla sınırlıydı. Masaüstü entegrasyon testi çalıştırılmadı.
- PowerShell yürütme politikası `AKTIF_ET.ps1` betiğini engelledi. Kontroller proje sanal ortamındaki Python doğrudan çağrılarak yürütüldü.

## 3.0.15 — Çakışan komut satırı işlemleri reddediliyor

Altı ana komut satırı seçeneği aynı ayrıştırma kuralına bağlandı. Bir komutta birden fazla ana işlem seçildiğinde uygulama herhangi bir işleme başlamadan çakışan seçenekleri bildiriyor ve çıkış kodu 2 döndürüyor. README yeni davranışı açıklıyor.

Base commit: `cbe2ac06b493547ec491f24aeda6c116f29a8b05`. Local tag: `auto/v3.0.15`.

Limitations:

- Çalışma komut satırı ayrıştırmasıyla sınırlıydı. Masaüstü entegrasyon testi çalıştırılmadı.
- PowerShell yürütme politikası `AKTIF_ET.ps1` betiğini engelledi. Kontroller proje sanal ortamındaki Python doğrudan çağrılarak yürütüldü.

## 3.0.14 — Güç boyutlandırmasında iptal durumu doğru raporlanıyor

Motor analizi iptal edilmiş olarak döndürdüğünde komut satırı raporları kaydedip çıkış kodu 1 veriyor. Markdown raporu ve manifest iptali belirtiyor. Tamamlanmamış güç aramasının ham sonucu analysis.json dosyasında saklanıyor.

Base commit: `2908e2867e0f90a90608c27137dc6f6c7d079322`. Local tag: `auto/v3.0.14`.

Limitations:

- Düzeltme, motorun sonuç döndürdüğü iptal durumlarını kapsıyor. Komut satırı ve rapor regresyonlarında motor yanıtı taklit edildi, gerçek motorun iptal yanıtı ayrıca doğrulandı.
- PowerShell yürütme politikası AKTIF_ET.ps1 betiğini engelledi. Kontroller proje sanal ortamındaki Python doğrudan çağrılarak tamamlandı.

## 3.0.13 — Analiz raporlarında yakınsama bölümü düzeltildi

Markdown raporu, yakınsama tanılarını ve yorumunu yalnızca yakınsama analizinde gösteriyor. Toplu analiz ve devir taraması raporları koşu sonuçlarını göstermeye devam ediyor.

Base commit: `00821ae688c6a0cdf1260234bd0e2391d831c2fa`. Local tag: `auto/v3.0.13`.

Limitations:

- Değişiklik Markdown raporlamasıyla sınırlı. Yeni regresyon testi örnek analiz sonuçlarıyla çalıştı.
- PowerShell yürütme politikası AKTIF_ET.ps1 betiğini engelledi. Kontroller proje sanal ortamının Python yürütücüsü doğrudan çağrılarak tamamlandı.

## 3.0.12 — Duyarlılık raporunda elastisite tablosu

Markdown raporu, hedef süresi ve giriş enerjisi için boyutsuz elastisiteleri parametre bazında gösteriyor. Motor bir elastisite hesaplayamadığında rapor ilgili gerekçeyi açıklıyor.

Base commit: `aa9ac89512a6e8579b1b55b9eb7e3bb5d014aa0a`. Local tag: `auto/v3.0.12`.

Limitations:

- Değişiklik Markdown raporuyla sınırlı. Yeni test, C++ motorunun sonuç biçimini temsil eden örnek verilerle çalıştı.
- PowerShell yürütme politikası AKTIF_ET.ps1 dosyasını engelledi. Kontroller proje sanal ortamının Python yürütücüsü doğrudan çağrılarak tamamlandı.

## 3.0.11 — Güç boyutlandırma raporu arama sonucunu açıklıyor

Markdown raporu, hedefe ulaşılabildiğinde koşullu güç tahminini kW cinsinden gösteriyor. Hedefe ulaşılamadığında aramanın güç üst sınırını ve C++ motorunun bildirdiği gerekçeyi gösteriyor. Boyutlandırma raporundan boş koşu tablosu ve yakınsama bölümü çıkarıldı.

Base commit: `d244b38c5755252c8a42c9ac546028120a560cbb`. Local tag: `auto/v3.0.11`.

Limitations:

- Değişiklik Markdown raporlamasıyla sınırlı. Regresyon testi, C++ motorunun sonuç biçimini temsil eden örnek verilerle çalıştı.

## 3.0.10 — Yeniden kullanılan klasörde eski zaman serisi temizleniyor

Tek hesap dışa aktarımında yeni sonuç zaman serisi içermiyorsa, aynı klasördeki önceki history.csv içeriği temizleniyor. Davranış README’ye ve ardışık dışa aktarımları sınayan regresyon testine eklendi.

Base commit: `e350eafd15a8a716a0d9033b690ea7eeca6fedd3`. Local tag: `auto/v3.0.10`.

Limitations:

- Boş zaman serisinde mevcut history.csv dosyası silinmez; içeriği boşaltılır.
- Masaüstü paketi yeniden üretilmedi.

## 3.0.9 — Boş analizlerde eski CSV satırlarının kalması düzeltildi

Analiz CSV’si artık her dışa aktarımda yeniden yazılıyor. Koşusuz analizlerde yalnızca sütun başlıkları kalıyor. Klasörün yeniden kullanımını doğrulayan regresyon testi ve README açıklaması eklendi.

Base commit: `00d3a00a49a5bf50508c009a24af9351a7123269`. Local tag: `auto/v3.0.9`.

Limitations:

- Hesap modelleri ve kayıt biçimleri değiştirilmedi.
- Masaüstü EXE paketi yeniden üretilmedi.

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
