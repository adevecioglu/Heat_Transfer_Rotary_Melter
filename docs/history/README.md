# Rotary Melter Desktop 2.2 — Doğrulanan soğuk su başlangıcı

ZIP'i çıkarıp **Rotary_Melter_Desktop_2_2.exe** dosyasını açın. Başlık 2.2 olmalıdır. Windows 64 bit / WebView2 gerekir.

## Başlangıç koşulu düzeltildi

Kullanıcı ceket suyunun da başlangıçta yaklaşık 25 °C olduğunu ve 110 °C suyun girişe gelmeye başladığını doğruladı. Yeni varsayılanlar:

- Devre suyu başlangıcı: **25 °C**.
- İç/dış metal başlangıcı: **25 °C**.
- Ürün başlangıcı: **25 °C**.
- Giriş: **110 °C sabit sınır koşulu** (`sourceMode=1`).

Önceki varsayılan, suyu baştan 110 °C kabul ediyor ve 30 kW giriş gücü / %95 verim ile kaynağı sınırlıyordu. Bu koşulda 110 °C yalnız hedefti, gerçek giriş sıcaklığı düşebiliyordu. 10 m³/h, 950 kg/m³, 4220 J/kgK ile ısı kapasite debisi 11,136 kW/K; net 28,5 kW kaynağın doğrudan dönüş–ısıtıcı bağlantısındaki sıcaklık artışı en çok 2,559 K idi. Bu model ayarı gerçek başlangıç tarifine uymuyordu.

Sabit giriş modunda **30 kW alanı kullanılmaz ve pasif gösterilir**. Kaynağın 110 °C'yi korumak için gerektirdiği anlık net güç hesaplanır; bu doğrudan seçilmiş bir boiler kapasitesi değildir. Gücü sınırlı modu seçerseniz gerçek giriş yeniden hesaplanır ve 110 °C'de kalmayabilir. Eski kayıtlı senaryolar kendi ayarlarını korur; sessizce değiştirilmez.

Kendi önceki girdilerinizi koruyarak doğrulanan başlangıca geçmek için paketteki **Confirmed_Cold_Start_110C_v22.json** dosyasını üstteki **JSON yükle** ile açabilirsiniz. Dosya oluşturulurken mevcut yerel taslağın diğer sayısal girdileri korunmuştur. Yerel kütüphaneniz silinmez.

## Su başlangıcı ve ΔT kontrolü

Üstteki açılır **Su başlangıcı ve giriş–çıkış ΔT kontrolü** alanı şunları gösterir:

- Su, metal ve ürünün ayrı başlangıç sıcaklıkları; kaynak modu ve giriş hedefi.
- Seçili andaki Tin, Tout, ΔT, debi ve ısı kapasite debisi.
- Akışın taşıdığı net güç, su→metal gücü, su enerji depolaması ve ek devre kaybı.
- Anlık su denge artığı.
- İlk 120 s için Tin/Tout/iç metal grafiği, ilk ana git düğmesi ve CSV dışa aktarma.
- Suyun başlangıç enerjisi ve modelin eşdeğer su hacmi/geçiş süresi.

Denge: **ṁ cp(Tin−Tout) = Q_su→metal + Q_ek_kayıp + dE_su/dt**. Geçici rejimde yalnız ürüne geçen ısıyı kullanarak su ΔT'si bulunamaz. Başlangıçta su/metal 25 °C ise tam t=0'da su→metal sıcaklık farkı sıfır; gelen net enerji önce su hacminde depolanır. Tin=110 / Tout=25, ilk ΔT=85 K olur. Bu fark tüm eritme boyunca sabit kalmaz.

İlk 2 s yaklaşık 0,1 s, 2–20 s yaklaşık 0,5 s, 20–120 s yaklaşık 2 s aralıkla kaydedilir. Sonrasında önceki kayıt aralığı sürer. Gerçek kayıtlar çözücü adımlarına denk gelir. Böylece önceki 0–30 s arasındaki seyrek grafik enterpolasyonu başlangıç geçişini gizlemez. İntegratör adımı ve 16×16 / radyal 24 çözünürlük azaltılmadı. v2.1'in hızlı çizimi korunur.

## Doğrulama ve rapor

- **Startup_Audit_v22.md**: Bulunan nedenler, dört senaryonun karşılaştırması ve model sınırları.
- **Startup_Comparison_120s.csv**: Dört başlangıç/kaynak senaryosunun ilk 120 s sonuçları.
- **validation_startup_independent_v22.json**: Ayrı SciPy BDF/Radau başlangıç karşılaştırması; sıcaklık farkı en çok yaklaşık 0,001 °C.
- **validation_water_balance_v22.json**: Aynı eski girdilerle kayıt sıklığı/denetim eklemenin hedef süresini, enerjiyi ve son sıcaklığı değiştirmediğinin kontrolü.
- **validation_confirmed_startup_v22.json**: Kullanıcının doğruladığı yeni başlangıçla tam çözüm ve anlık su dengesi.
- **validation_desktop_v22.json / validation_water_ui_v22.json**: Gerçek paketli EXE ve Edge arayüzü, başlangıç denetimi, kaynak alanı, önceki erime/dönüş/PDF/yerel proje ve dil kontrolleri.

## Kapsam

Örneğin yaklaşık 15 s'de Tout≈44,4 °C ve 30 s'de Tout≈95,0 °C değerleri, bu modelin geçici wax/film/geometri değerlerine bağlı tahminlerdir. Gerçek sensör ölçümü değildir. Paylaşılan katsayılarla iki sayısal yöntemin uyuşması deneysel doğrulama değildir.

Başlangıçtaki yüksek net akış gücü, soğuk suyun yer değiştirmesi ve su/metal enerji depolamasıyla ilgilidir; doğrudan sürekli boiler satın alma gücü olarak kullanılmamalıdır. Kaynağın sıcak deposu, ısıtıcısı ve kontrolü ayrıca değerlendirilmelidir. Ek devre hacmi eşdeğer su düğümlerine dağıtılmıştır; gerçek boru/mil gecikmeleri, sensör dinamiği ve ayrı sıcak depo çözülmez. Gerçek malzeme, film katsayıları, su özellikleri ve sıvı-su basınç uygunluğu doğrulanmalıdır.

## English

Run **Rotary_Melter_Desktop_2_2.exe**. The user confirmed an initially cold jacket: water and metal at 25 °C, with 110 °C supplied at the inlet. Defaults now match that condition. Fixed-supply mode calculates required instantaneous net source power and ignores the nominal limited-mode heater field. Old saved cases keep their original settings.

The new expandable water audit shows initial conditions, actual supply/return, transient water storage, water-to-metal power and energy closure. Startup history is denser, with a first-120-second plot and CSV. Four startup/source scenarios were cross-solved using BDF/Radau; numerical agreement is not experimental validation. See the audit report for source/reservoir, transit-time and physical-model limitations.
