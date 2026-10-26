# Rotary Melter Desktop 1.7

## Türkçe

ZIP'i bir klasöre çıkarıp **Rotary_Melter_Desktop_1_7.exe** dosyasını açın. Başlıkta **1.7** yazdığını kontrol edin. Eski EXE güncellenmez; yeni dosyayı çalıştırın. Python kurulumu gerekmez. Windows 64 bit ve WebView2 kullanır.

- Varsayılan eksenel × çevresel ağ: **16 × 16**; granül içi radyal hücre: **24**.
- Sol üstte 8×8 / 16×16 / 32×32 hazır seçimleri var. Manuel olarak başka tam sayılar da girilebilir. Program bölge sayılarını kendiliğinden düşürmez. JSON'da seçilen sayılar korunur.
- Eski sürümlerdeki 3.500.000 tahmini zaman adımı reddi ve 24/32 yüzey bölgesi üst sınırları yoktur. Bilgisayar belleği/işlem gücü yine çözüm maliyetini belirler; hesap kullanıcı tarafından durdurulabilir.
- `Azami zaman adımı = 1 s`, her adımın 1 s olacağı anlamına gelmez. Kararlılık ve radyal iletim daha küçük adım gerektirebilir. Etkin dt sol panelde gösterilir.
- `Azami fiziksel süre = 24 saat`, bilgisayarda 24 saat çalışma sınırı değildir. Model hedefe ulaşırsa daha önce durur; fiziksel süre dolduğunda hedefe ulaşılamadıysa bunu belirtir.
- Doğruluk ve doğrulama sekmesinde **Zaman adımı ve bölge yakınsamasını çalıştır** düğmesiyle beş koşu çözülür. 16×16 seçiliyken yüzey ağları 8×8, 16×16 ve 32×32 olur. Tümü aynı dt/radyal hücre sayısını kullanır. dt/2 ve iki kat radyal hücre ayrıca çözülür. Sayılar CSV ve PDF raporunda görünür.
- `SciPy BDF / Radau`, aynı fizik katsayılarıyla ayrı Python denklem montajını ve iki farklı integratörü çalıştırır. Bu ticari CFD veya deneysel validasyon değildir.

`Case_8x8_radial24.json`, `Case_16x16_radial24.json`, `Case_32x32_radial24.json` dosyaları JSON yükle ile açılabilir. `Mesh_Convergence_v17.csv` tamamlanmış örnek koşunun gerçek çıktılarıdır.

Bu örnek **geçici wax kartı**, 600×800 mm silindir, varsayımsal 150 mm küresel bombe, %50 yığın dolumu, **71,202 kg**, 15 mm küre içindir. Kullanıcının 180 kg hedefini veya gerçek çikolata performansını doğrulamaz. Küçük ağ farkı fiziksel model hatasının küçük olduğunu göstermez. Hareket DEM'i ile ısıl ağ tam iki yönlü bağlı değildir; malzeme/temas/yenilenme katsayıları kalibre edilmelidir. Önceki 1.6 sürümündeki yoğun DEM örtüşme uyarıları geçerlidir. Yeni bir 20–30 dakikalık yoğun DEM testi bu sürümde yapılmadı; değişiklik ağırlıklı olarak ısıl ağ ve doğrulama iş akışıdır.

## English

Extract the ZIP and run **Rotary_Melter_Desktop_1_7.exe**. Confirm version **1.7** in the window header. The previous executable is not overwritten. Windows 64-bit/WebView2 is required; Python is bundled.

Defaults are 16 axial × 16 circumferential zones and 24 radial cells per granule population. Presets 8/16/32 are available; arbitrary valid integer counts remain editable. There is no automatic zone reduction or former estimated-step-count rejection. Input dt is a maximum; the solver uses a smaller stable step. Maximum hours means physical simulation horizon, not computer runtime.

The validation tab solves coarse/selected/fine spatial grids at identical dt/radial resolution, then a separate dt/2 and doubled-radial test. CSV and PDF include convergence results. Conditional GCI is withheld when its checks fail. Numerical convergence is not physical validation. Independent SciPy BDF/Radau shares documented geometry and physical coefficients but assembles/integrates the equations separately.

The shipped example is a provisional 71.202 kg wax case, not a verified 180 kg chocolate capacity. Consult Verification_Report_v17.md and Research_Notes_v17.md.
