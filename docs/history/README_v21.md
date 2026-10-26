# Rotary Melter Desktop 2.1 — Akıcılık düzeltmesi

ZIP'i çıkarın, **Rotary_Melter_Desktop_2_1.exe** dosyasını açın. Başlıkta **2.1** görünmeli. Önceki EXE bu düzeltmeleri içermez. Windows 64 bit / WebView2 gerekir. v2.0 senaryoları aynı yerel depodan okunur; ayrıca taşımak gerekmez.

## Düzeltilen nedenler

Önceki sürüm her çizimde 45.120 granülü sıralayıp her birine ayrı Canvas yay/dolgu/çizgi çağrıları yapıyordu. Gövde konturu ve bazı istatistikler tekrar hesaplanıyordu. Girdi yazılırken veya eğim kaydırılırken bütün fiziksel granül yerleşimi yeniden kuruluyordu. Örnek hareket kaydı yüklenirken her kare için bütün nesneler yeniden güncelleniyordu. Gizli Model sekmesi de bazı arka plan yollarından çiziliyordu.

Yeni sürüm:

- Bütün fiziksel granülleri WebGL nokta geçişi ve derinlik tamponuyla çizer. Adet/çap/ağ azaltılmaz.
- WebGL yoksa aynı bütün granülleri yeniden kullanılabilir yazılımsal görüntü/derinlik tamponuna çizer; binlerce ayrı Canvas çağrısı yapmaz. Otomatik geçiş vardır.
- Geometri konturunu ve sabit parçacık görüntüsünü önbellekte tutar. Yalnız gövde dönerken sabit granül görüntüsü yeniden üretilmez; gerçek hareket kaydında konumlar güncellenir.
- Girdi düzenlerken hızlı, açıkça etiketlenmiş geometri önizlemesi gösterir. Ayrıntılı granül yerleşimi Hesapla sonrasında veya hareket istendiğinde hazırlanır. Eski ısıl sonuç güncelmiş gibi gösterilmez.
- Hareket kaydındaki Float32 konumlarını bir kez çözüp saklar. Bütün kareleri korur, yükleme sırasında her kare için nesne konumlarını tekrar tekrar yazmaz.
- Gizli sekmelerde çizimi atlar. Görünüm animasyonları yaklaşık 30 kare/s hedefiyle zamanlanır; fiziksel çözücü zaman adımı bu hızdan bağımsızdır.

## Ölçümler

Aynı bilgisayarda, aynı Edge başsız testinde; 600×800 mm, 45°, 45.120 granül, 16×16 yüzey / radyal 24. Değerler çizim/girdi işlevlerinin ortanca işlem süreleridir; uçtan uca çözüm süresi veya garanti edilen FPS değildir.

| İşlem | v2.0 | v2.1 |
|---|---:|---:|
| Erime görünümü | 63,2 ms | 4,2 ms |
| Yalnız gövde dönüşü | 2.110,3 ms | 1,4 ms |
| Girdi/eğim güncellemesi | 1.521,2 ms | 8,0 ms |

Önceden hesaplanmış **gerçek hareket** kaydı ayrıca test edildi: 45.120 granülle ortanca 2,7 ms, %95 değeri 4,2 ms; testte en uzun kare 13,9 ms. WebGL kapatılarak yazılımsal yedek yol test edildi: ortanca 8,0 ms, %95 değeri 8,8 ms. Bu ayrı hareket testi, fiziksel temas hesabını tekrar çözmek değil kaydı çizme testidir. Ölçümler donanıma, pencereye ve arka plan yüküne göre değişebilir.

## Doğruluk ve kontroller

`validation_render_v21.json`: 49 karenin çözülmüş konum baytları eski base64 yoluyla karşılaştırıldı; bütün baytlar aynı. Son karedeki her granülün x/y/z değeri kayıtla birebir aynı. WebGL ve yedek yolda 45.120 parçacık korunuyor. Kütle/enerji kontrolü, gizli görünümde çizim olmaması ve girdi değişiminde bütün granüllerin tekrar kurulmaması sınandı.

`validation_desktop_v21.json`: Paketlenen gerçek EXE üzerinde erime, dönüş, yerel senaryolar, iki dil, PDF, yerel DEM başlangıcı ve bağımsız SciPy BDF/Radau kontrolleri. `drawingBackend` o WebView2 çalışmasında kullanılan çizim yolunu gösterir.

`validation_physics_unchanged_v21.json`: Isıl, hidrolik, mekanik çözücü ve erime hacmi/entalpi dosyaları v2.0 ile aynı dosya özetlerine sahiptir. Varsayılan model süresi yine 5345,433788545308 s; bu, geçici wax/temas varsayımlarının model sonucudur.

## Kapsam

Bu düzeltme arayüzü ve kayıt yükleme/çizmeyi hızlandırır. Yoğun DEM hesabının fiziksel süresini çözmek hâlâ pahalıdır; daha az granül, daha kaba ağ veya daha büyük çözücü adımı kullanılarak hızlandırılmadı. Fiziksel kalibrasyon ve deneysel doğrulama durumu değişmedi. Tam erime görünümü entalpiye bağlı eşdeğer hacimli gösterimdir, tüm süreyi çözen iki yönlü termo-DEM/CFD değildir. Önceki özellikler ve sınırlar README_v20.md / README_v19.md içinde korunur.

## English

Run **Rotary_Melter_Desktop_2_1.exe**. Version 2.1 fixes UI stalls with depth-buffered rendering of all physical particles, a software raster fallback, geometry/static-image caching, deferred granule construction during edits, faster exact recording decoding and no hidden-tab painting. Solver equations, grid, physical granule count and recorded coordinates are retained. The timing table measures rendering/input processing on one machine, not total simulation runtime or guaranteed frame rate. Dense contact solving remains computationally expensive.
