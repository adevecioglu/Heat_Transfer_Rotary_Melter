# Rotary Melter Desktop 1.6

Windows EXE; yerel hesap, Python kurulumu gerekmez. Microsoft Edge WebView2 Runtime gerekir. NumPy, Numba/LLVM ve SciPy paketlidir; ilk ayrıntılı hareket çözümünde yerel derleme birkaç saniye sürebilir.

## Türkçe kullanım

1. Soldan geometriyi, yataydan eksen eğimini, yükü, granül çapını, malzemeyi ve su koşullarını girin. Dönüş yönü RPM grubunda sorulur: **üst açıklıktan mile doğru bakarken saat yönü** varsayılandır. Ters yön seçilebilir. Eğim/çap değişince önizleme yenilenir.
2. **Hesapla**, radyal granül entalpisi + metal/su bölgesel ağını çözer. 15 mm kürenin merkez/yüzey farkı ve erime aralığı hesaplanır; en soğuk merkez izlenir. Granüller ısı hesabında iki popülasyonla temsil edilir; 45 bin granülün sıcaklığı ayrı ayrı çözülmez.
3. **3B dönüş ve ürün hareketi** görünümünde **Ayrıntılı hareketi çöz** düğmesi gerçek çap/kütleden hesaplanan bütün küreleri yerel arka plan çözücüsünde başlatır. 320 büyük temsilci kullanılmaz. Örnek wax koşulunda 45.120 adet 15 mm küre vardır.
4. Temas ayarlarında fiziksel çözüm süresi, başlangıç oturma süresi, azami adım, normal sertlik/mass oranı, sürtünmeler, restitüsyon ve yuvarlanma direnci düzenlenir. Oturma aşamasında kap dönmez. Sonra seçilen yönde döner. **Çözümü durdur**, **Sıfırla** ve hesaplanan kareleri tekrar oynatma vardır.
5. Bilgisayar süresi ile fiziksel zaman farklıdır. Gerçek çaplı yoğun DEM çok yavaş olabilir. Ekran her ikisini gösterir. Fiziksel süre dolana veya kullanıcı durdurana kadar çözüm sürer; tahmini adım adedi nedeniyle otomatik ret yoktur. Sayısal kararlılık için adım küçültme korunur. Gerçek RAM/CPU sınırları ortadan kalkmaz.
6. Başlangıç erime oranı manuel seçilir veya ana ısıl zaman çizgisinden alınır. Hareket koşusu bu başlangıç fazında çalışır. Sıvı seviyesi, kürelerin yer değiştirdiği hacim çıkarılarak hesaplanır. Düşük erimede sıvı granüllerin önünde saydam görünür; bir %30 eşiği yoktur. Sıvı kuvvetleri ve izleri kapanış modelidir, CFD değildir. Fazın seçilmesi, tam iki yönlü termo-DEM bağlaşımı değildir.
7. **Doğruluk ve doğrulama** sekmesinde zaman/ağ duyarlılığına ek olarak **SciPy BDF / Radau** düğmesi aynı koşuyu bağımsız Python denklemleriyle yeniden çözer. Fizik katsayıları ve geometrik alan tablosu paylaşılır; ODE montajı/integrasyonu ayrıdır. Bu, deneysel malzeme doğrulaması anlamına gelmez. Ölçüm CSV'siyle RMSE/bias karşılaştırması da korunmuştur.
8. **Formüller ve çözüm adımları** gerçek radyal ısı ve temas denklemlerini gösterir. Python/Numba/SciPy kaynakları da ekrandadır. JSON girdiler ve hareket ayarları kaydedilir; PDF seçilen Türkçe/İngilizce dilde, hareket anı ve varsa bağımsız karşılaştırmayla dışa aktarılır.

## Fizik ve güven sınırı

- Duvar sürtünmesi granülleri kap yönünde taşır. Katıların kapla aynı açısal hızda dönmesi zorunlu değildir. Kayma, yüzey akışı, geçici tıkaç hareketi veya kısmi sürüklenme; eğim, dolum, sürtünme ve devirle değişir. Model, görsel olarak ters yönde akış üretmeye zorlanmaz.
- Yerçekimi dünya koordinatlarında düşeydir. Başlangıç küreleri küresel yüksekliğe göre yerleştirilir; görünümde düşey yerçekimi oku bulunur. Serbest katı yüzeyi, kabın eksen açısına paralel olmak zorunda değildir; başlangıç ideal kafes, ardından temas dinamiği vardır. Yığın açısı için malzeme kalibrasyonu gerekir.
- Normal temas yay/sönüm, teğetsel yay geçmişi/Coulomb ve yuvarlanma direnci kullanılır. Varsayılan katsayılar gerçek wax veya çikolata için ölçülmedi. Yapışma, düzensiz şekil, kırılma, gerçek viskoz eriyik akışı ve gerçek 3B ceket dağıtımı çözülmez. Çap 15 mm küre varsayımı kullanıcı tarafından onaylanmıştır.
- Büyük temas örtüşmesi yumuşak temas hatasına işaret edebilir. Daha yüksek sertlik/daha küçük adımla hassasiyet araştırılmalıdır. Tam yoğun yatak hareketinin nicel yakınsaması ve deneysel geçerliliği kurulmuş değildir. Uzun süre çalışması tek başına doğruluk kanıtı değildir.
- Isı modelindeki temas/RPM yenilenme katsayıları DEM'den otomatik çıkarılmaz. Isıl sonuç ile ayrıntılı hareket arasında kalibre edilmiş iki yönlü bağlaşım yoktur. İki popülasyon ortalamaları gerçek yerel son parçayı garanti etmez.
- Örnek, 600 mm çap × 800 mm boy, 150 mm varsayılan küresel bombe, 45°, 10 RPM, 110 °C/10 m³/h su, izolasyonsuz 316/2B ve geçici wax kartıdır. %50 yığın dolumu, 893 kg/m³ katı yoğunluğu ve 0,64 paketlenmeyle **71,2 kg** verir. Kütle alanındaki 180 kg bu modda aktif değildir. Çikolata yoğunluğu 1652 kg/m³ ve gerçek DSC/cp/k/viskozite kartı ayrıca uygulanmalıdır. Wax sonucunu çikolataya doğrudan taşımayın.
- Sac kalınlığı bu yazılımda ısı girdisidir; mekanik basınçlı kap uygunluğu hesaplanmaz. Joint/hat verileri varsayımsal olabilir. Sıcak su sadece ayrı mil besleme/dönüşü ile ceket içinde dolaşır; ürünle karışmaz.

## Kontroller ve yeniden üretim

`Verification_Report.md` ve `validation_*.json` dosyaları gerçek çalıştırma sonuçlarıdır. 20 dakikalık test, **bilgisayarda geçen duvar saati süresidir**; çözülen fiziksel saniye ayrıca yazılır. Test süresi, bütün bir erime çevrimi veya tam devir garantisi değildir. Testlerde örnek geçici wax kartı kullanılır.

- `node tests_v16.js`: güncel enerji, sıcaklık sınırı, kaynak gücü ve eski ince-ağ reddinin kaldırılması kontrolleri.
- `python reference_solver.py spec.json javascript_result.json output.json`: ayrı SciPy BDF/Radau ısıl montaj/çözümü, QUADPACK geometri ve brentq Colebrook basınç kaybı kontrolü. Paketlenen referans girdi dosyaları örnek koşuyu tekrar üretir.
- `python check_dem_reference.py`: ayrı SciPy DOP853 ikili çarpışma çözümü, analitik duvar/yerçekimi kontrolleri, fiziksel granül sayısı.
- `Rotary_Melter_Desktop.exe --self-test C:\absolute\diagnostic.json`: gizli uygulama testi; gerçek WebView2, yerel JIT, arka plan hareket işi, SciPy karşılaştırma, dil/eğim/PDF kontrolleri.
- `build_desktop.ps1`: paketleme. Kaynak geliştirme ortamında `requirements-desktop.txt` kurulmalıdır. Dağıtılan EXE bunları zaten içerir.

## English

Rotation direction is defined **viewed from the upper opening toward the shaft**; clockwise is the default. Geometry edits update the preview immediately. The thermal solver uses radial finite-volume enthalpy cells inside two granule populations, plus zonal metal/water nodes. It tracks center/surface temperature differences; it does not solve the temperature of each moving granule individually.

Detailed motion uses every sphere calculated from physical diameter and charge mass: 45,120 physical 15 mm spheres in the default temporary-wax case. The native NumPy/Numba solver runs in the background with normal spring/damping, tangential history/Coulomb friction and rolling resistance. Duration/count/estimated-step rejection is removed; stability time steps and physical resource constraints remain. Settling is a separate initial stage with stationary walls. The UI distinguishes computation time from physical simulation time. Stop/reset/replay are available.

World gravity is vertical. A granular free surface does not have to follow the vessel axis. Wall entrainment, slip, avalanching or transient plug motion depend on material and operating conditions. Liquid visibility includes displaced solids and starts below 30% melt. Liquid forces/tracers are prescribed closures, not CFD. Motion at a selected phase is not calibrated two-way thermal/DEM coupling.

The accuracy tab runs a separately assembled Python/SciPy BDF/Radau solution with shared documented coefficients; source code and numerical reports are supplied. This verifies numerical implementation, not experimental validity. Dense-bed contact-stiffness convergence, actual wax/chocolate friction/adhesion, material properties, CAD geometry and experimental melting performance remain unvalidated. Review maximum overlaps and the physical duration actually reached in the endurance test. Independent measurements remain necessary before treating modeled capacity/heater power as guaranteed equipment performance.


## Reproducible endurance / tekrar çalıştırma

`python performance_checks.py --seconds 1200 --engine fast --out my_test` runs a new physical-size 20-minute computer endurance case. `--engine grid` selects the original independently retained neighbor enumeration. `python performance_checks.py --compare Example_DEM_end_state.npz --out comparison` compares 100 steps from the same supplied dense-bed state. Timing warm-up is excluded by this portable runner. Raw example state files are in the desktop package.

Primary method references: [LAMMPS granular contacts](https://docs.lammps.org/pair_granular.html), [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html). LAMMPS itself is not executed by this application.
