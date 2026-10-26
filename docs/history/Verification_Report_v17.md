# v1.7 - Ağ hassasiyeti ve bağımsız çözüm denetimi

Örnek: geçici wax, %50 yığın dolumu, 71,202124 kg; 600 mm iç çap, 800 mm silindir, 150 mm varsayımsal küresel bombe; 45°, 10 RPM saat yönü; 15 mm granül; 110°C su seti, 10 m³/h. Model her iki granül popülasyonundaki tüm radyal hücreler 75°C hedefine gelince durur. Bu bir gerçek kapasite ölçümü değildir.

## Gerçekten tamamlanan koşular

| Koşu | Eksenel × çevresel | Radyal | dt (s) | Hedef süre (h) | Kaynak giriş enerjisi (kWh) |
|---|---:|---:|---:|---:|---:|
| Kaba | 8 × 8 | 24 | 0.008714672 | 1.485384293 | 10.431427007 |
| Temel | 16 × 16 | 24 | 0.008714672 | 1.484837205 | 10.431838878 |
| İnce | 32 × 32 | 24 | 0.008714672 | 1.484478936 | 10.431903371 |
| Yarım dt | 16 × 16 | 24 | 0.004357336 | 1.484835995 | 10.431833777 |
| İnce radyal | 16 × 16 | 48 | 0.008714672 | 1.484413576 | 10.431114304 |

Üç yüzey ağında aynı dt ve radyal hücre sayısı kullanıldı. Temel/ince süre farkı **%0.024134**; dt/2 etkisi **%0.000082**; 24→48 radyal hücre etkisi **%0.028539**. Beş koşunun toplam bilgisayar süresi bu testte 229.984 saniye; donanım garantisi değildir. Her koşu 600 binden fazla gerçek adım çözdü. En büyük bağıl enerji artığı 9.68e-14.

Üç noktalı koşullu GCI: p=0.610726, ince ağ için %0.057242. Bu, fiziksel belirsizlik veya gerçek erime süresi hatası değildir. Gözlenen düşük mertebe nedeniyle daha geniş ağ serisi gerekebilir; üç noktanın verdiği asimptotik oran tek başına bağımsız kanıt değildir. Kod, zaman çözünürlüğünün ayırt edemediği / salınımlı / büyüyen farklarda GCI vermez.

## Ayrı Python/SciPy montajı

Varsayılan 16×16, radyal24 koşusu etkin dt=0.034786507 s ile de ayrı çalıştırıldı. JavaScript hedefi 5345.433788545 s. Python aynı fizik katsayılarını, dışa aktarılmış geometri ve ıslanan alan tablosunu kullanır; montaj ve integrasyonu ayrıdır.

| İntegratör | Hedef (s) | JS süre farkı (%) | Enerji farkı (%) |
|---|---:|---:|---:|
| BDF | 5345.406920581 | 0.0005026 | 0.0003022 |
| Radau | 5345.406829211 | 0.0005043 | 0.0003026 |

SciPy'nin yapısal olarak sıfır enerji-akümülatörü sütunlarında fark katsayısını sürekli artırmasını önlemek için sabit adımlı sonlu fark Jacobian kullanıldı. Önceki adaptif seyrek Jacobian ile süre farkları 0,005 s altında kontrol edildi. Bu, fizik denklemlerini değiştirmez.

## Uygulama denetimleri

12 odaklı test geçti: yüksek ağ kabulü, 8/16/32 çözümünde bölge sayısının korunması, eski üst sınırların kalkması, JSON girdilerinin korunması, ortak dt, ayrı radyal/zaman inceltme ve GCI yanlış olumlu durumları. Paketli Windows EXE gizli testle açıldı; Türkçe/İngilizce, canlı eğim, gerçek granül boyutu, yerel DEM, SciPy karşılaştırması, 8 ve 32 hazır seçimleri, yakınsama tablosu/CSV düğmesi, iki dilde PDF üretimi geçti. JSON kanıtları pakette bulunur.

## Fiziksel sınırlar

Isıl model iki granül popülasyonunun radyal ortalamalarını çözer. Her hareketli granül için ayrı termal temas ağı veya iki yönlü eriyik CFD'si yoktur. DEM'in yoğun yatak sertlik/adım yakınsaması ve gerçek malzeme kalibrasyonu tamamlanmamıştır. 1.6 sürümündeki uzun hareket testleri bu sürümde tekrar edilmedi. Radyal ve yüzey ağını inceltmek malzeme, temas ve RPM kapanışlarını doğrulamaz. 180 kg çikolata kapasitesi ve boiler satın alma gücü bu geçici wax koşusundan garanti edilemez.

Literatürden model kararları ve sınırlar Research_Notes_v17.md dosyasındadır. Gerçek malzeme kartı ve bağımsız ekipman ölçümleriyle kalibrasyon/validasyon gerekir.
