# V11 aktarımı ve doğrulama

## Kaynak seçimi

V11 dizininde yalnız paketli EXE ve dağıtım verileri vardı. Düzenlenebilir kaynaklar V10 içindeki `Rotary_Melter_Source_v2_2.zip` arşivinden alındı. V10'un eşlik eden v2.2 EXE'si ile V11 EXE'sinin SHA-256 değerleri eşit; varsayılan girdiler, README ve doğrulanan başlangıç kaydı da eşleşiyor. Bu nedenle daha eski bir model kullanılmadı. Checksum kayıtları `V11_SOURCE_PROVENANCE.json` dosyasında.

## Korunan davranış

- 25 °C su/metal/ürün başlangıcı ve sabit 110 °C giriş varsayılanı.
- 16×16 yüzey ve 24 radyal granül çözünürlüğü.
- Su depolaması dahil geçici enerji dengesi, yoğun başlangıç örneklemesi.
- Türkçe/İngilizce arayüz, PDF/CSV/JSON, erime oynatımı ve yerel parçacık hareketi.
- Revizyon kontrollü senaryo kütüphanesi ve eski JSON uyumluluğu.
- Üretim JavaScript denklemleri ve bağımsız Python referans hesabı.

## Testlerin güncellenmesi

Kaynak paketinin bazı testleri eski sürümün varsayılanlarını kullanıyordu. Güç sınırı testleri, V11'de varsayılan olan sabit giriş modunda boiler sınırı arıyordu. Bu test girdilerine **`sourceMode=0` açıkça eklendi**; üretim hesabı ve varsayılanları değiştirilmedi.

Yalnız bölgesel öncül modeli yükleyen `tests_v14.js` ve 320 temsilci parçacık bekleyen `tests_motion.js`, güncel V11 üretim zincirinin testleri değildir. Asıl dosyalar orijinal kaynak arşivinde korunur; tarihsel kopyaları `validation/legacy_tests/` altındadır. Güncel radyal ısı ve gerçek çaplı yerel parçacık kontrolleri bunların yerine çalıştırılır. Tarihsel testleri başarılıymış gibi raporlamıyoruz.

## Yeniden çalıştırma

```powershell
.\.venv\Scripts\python.exe -m tools.RunChecks --desktop
```

Python iş akışı/kayıt testleri, beş JavaScript test grubu, yerel rijit cisim kontrolleri ve gizli WebView2 masaüstü testi çalışır. Sonuç dosyası `outputs/checks/<koşu>/results.json` içindedir. Testler mevcut kullanıcı kütüphanesi yerine izole kayıt dosyaları kullanır.

Yeni EXE ayrıca `--self-test` ile test edilir; EXE derlenmiş olması tek başına uygulamanın açıldığının kanıtı sayılmaz. Son geçiş sonuçları `validation/migration_verification.json` dosyasına kaydedilir.

Sayısal eşleşme ve enerji korunumu deneysel doğrulama değildir. Kullanıcıya gösterilen fiziksel kapsam ve kalibrasyon notları korunmuştur.

## GitHub'a yayınlama

Oluşturduğunuz `adevecioglu/Heat_Transfer_Rotary_Melter` reposu kullanılır. İlk yerel commit (`74e9df2`) eski büyük dağıtım dosyalarını da içeriyordu. Bu commit yerel `archive/pre-publication-74e9df2` dalında korunur; kaynak kodunun ilk yayın commit'i arşivleri içermez. Dosyaların kendileri `releases/original/` altında durur. GitHub normal Git nesnelerinde 100 MiB üzerindeki dosyaları engeller: [resmî boyut sınırları](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
