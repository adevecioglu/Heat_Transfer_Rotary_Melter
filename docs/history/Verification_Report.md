# Rotary Melter 1.6 — Verification report / Doğrulama raporu

Bu rapor sayısal doğrulamayı fiziksel geçerlilikten ayırır. Gerçek wax/çikolata malzeme katsayıları ve tank erime performansı bağımsız deneyle doğrulanmamıştır.

## Isıl çapraz çözüm

Ayrı Python/NumPy denklemleri SciPy BDF ve Radau ile çözüldü. JavaScript orta-nokta RK2 kullanır. Geometri, ıslanan alan tablosu ve fizik katsayıları açıkça paylaşılır; ODE montajı ve integrasyonu ayrıdır. Bu, bağımsız ticari CFD veya deneysel validasyon değildir.

| Çözücü | Hedef süre (s) | JS ile süre farkı | Su çıkışı (°C) |
|---|---:|---:|---:|
| JavaScript RK2 | 5353.874390823 | — | — |
| SciPy BDF | 5353.789857507 | 0.001579% | 109.640808021 |
| SciPy Radau | 5353.789878585 | 0.001579% | 109.640808022 |

Bağımsız QUADPACK hacim/alan farkı: 0 / 0. Bağımsız brentq Colebrook basınç kaybı: 1.746559371 bar; bağıl fark 1.92e-14. Bu basınç karşılaştırması aynı hat varsayımlarını kullanır; üretici joint verisinin eksikliğini gidermez.

Ek RPM/debi/çap koşuları `validation_independent_cases_v16.json` dosyasındadır. Güncel sayısal kontroller 11 adettir. Radyal hücre sayısı 12→24 olduğunda süre farkı %0.11034; eksenel/çevresel ince ağ farkı %0.03698; yarım adım farkı %0.00103. Bu farklar seçili koşul içindir.

## Eski analiz engeli

32×48 yüzey bölgesi + 12 radyal hücre koşusu çalıştırıldı. Azami süreye göre tahmin 4387431 adım olup eski 3.500.000 engelini aşar; artık peşinen reddedilmez. Kontrol koşusu 9321 adımda hedefe ulaştı; enerji artığı bağıl 6.46e-15. Bu, çok uzun ince-ağ koşularının anında biteceğini göstermez.

## Ayrık granül temasının bağımsız kontrolü

İkili çarpışma ayrı SciPy DOP853 denklemiyle çözüldü. 1 µs adımda hız farkı başlangıç hızının yaklaşık %0.05429; adım yarıya inince hata azaldı. İtme eşit/zıt, analitik duvar uzaklığı ve yerçekimi dönüşümü kontrol edildi. Bu, yoğun yatak malzeme katsayılarını doğrulamaz.

Verlet aday listesi/temas geçmişi dizisi hızlandırması aynı kuvvet yasasını kullanır. 45.120 küre, 100 adımlık doğrudan A/B karşılaştırmada en büyük durum farkı 6.21e-11; sıcak çalışma süresi oranı 2.74×. İlk çağrı JIT süresi içerebilir; tek ölçüm donanım garantisi değildir. Hareketli aday listesi yeniden oluşturma kontrolü de geçti.

## Gerçek duvar saatiyle uzun testler

| Test | Bilgisayarda geçen süre | Fiziksel ön oturma | Fiziksel dönme | Küre sayısı | Kaçış |
|---|---:|---:|---:|---:|---:|
| İlk yerel uygulama | 1200.13 s | 0.750480 s | 0.776475 s | 45120 | 0 |
| Hızlandırılmış uygulama | 480.26 s | 0.751319 s | 0.959273 s | 45120 | 0 |

Toplam yaklaşık 28.01 dakika bilgisayar testi yapıldı. Bunlar 28 dakika fiziksel hareket değildir. Henüz bir tam erime çevrimi veya çok sayıda devir çözülmüş değildir. Uzun testlerin geçmesi yalnızca sonluluk/kaçış/çalışma kararlılığı kanıtıdır.

**Yoğun yatak hareketi nicel olarak doğrulanmış kabul edilmedi.** En büyük örtüşme/yarıçap ilk koşuda %8.334, hızlandırılmış koşuda %8.340. Son karede parçacık-çiftleri örtüşmesinin p99 değeri %0.455. Duvar temasları genel maksimumda ayrıca yer alır. Sertlik ve zaman adımı yakınsaması ile gerçek sürtünme/yapışma ölçümü gerekir. Son kare verileri CSV/NPZ olarak eklenmiştir.

## Sınırlar ve sonraki fiziksel doğrulama

Bu sonuçlar geçici wax kartı, 71,2 kg örnek %50 dolum, 15 mm küre ve varsayımsal küresel bombe içindir. 180 kg çalışma kapasitesi veya gerçek çikolata erime garantisi değildir. Isı hesabı iki radyal granül popülasyonudur; hareket modülü bütün küreleri çözer ancak kalibre edilmiş iki yönlü termo-DEM bağlaşımı yoktur. Sıvı kuvvetleri CFD değildir.

Gerçek malzeme DSC/cp/k/yoğunluk/viskozite ve sürtünmesini doğrulayın. Debi, boiler giriş gücü, ceket giriş/çıkış sıcaklığı ve basıncı, ürün merkez/yüzey sıcaklıkları ve erime bitişini birden fazla devir/yükte ölçün. Kalibrasyondan ayrı bir koşuda süre, enerji ve sıcaklık eğrilerini karşılaştırın. Ölçüm belirsizliğini raporlayın.

## English interpretation

Thermal equations were independently assembled/integrated with SciPy BDF/Radau, explicitly sharing documented geometry and physical coefficients. The pressure-loss root solve and geometry quadrature were checked separately. Normal collision was compared with SciPy DOP853. The original and accelerated contact implementations agreed in direct A/B checks.

The endurance durations above are computer wall-clock time, not physical simulated minutes. Dense-flow quantitative convergence and experimental validity remain unestablished; the maximum soft overlaps are explicitly disclosed. Do not treat numerical agreement or uninterrupted execution as guaranteed real chocolate melting capacity. Full inputs, scripts and machine-readable results are supplied for review.
