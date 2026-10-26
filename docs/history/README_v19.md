# Rotary Melter Desktop 1.9

ZIP'i çıkarıp **Rotary_Melter_Desktop_1_9.exe** dosyasını açın. Başlıkta 1.9 yazmalıdır. Windows 64 bit ve WebView2 gerekir; Python pakete dahildir.

## Yeni sekmeler

**Çözüm adımları ve formüller:** Girdi kontrolünden geometriye, eğimli doluma, hidrolik kayba, radyal entalpiye, ceket/metal ısı dengesine, RK2 zaman adımlarına, kayıplara ve sonuç gösterimine kadar 20 adım. Her adım denklemi, ne zaman çalıştığını ve etkin kod dosyasını verir. Sayı düğmeleri adımlara götürür. Saklanan çözüm anı seçilerek sıcaklık, faz oranı, ısı akıları, enerji depolaması, enerji artığı ve örnek kapasite/iletkenlik değerleri görülür. İlk dört gerçek orta-nokta adımı ve etkin kaynak kodu gösterilir. Adımlar ve denetim verileri JSON olarak dışa aktarılır. Girdiler değişince eski koşunun ara değerleri güncelmiş gibi gösterilmez.

**Simülasyon · erime:** Tamamlanan ısıl analizin başından sonuna kadar oynatma, duraklatma, başa alma, zaman çizgisi ve dakika seçimi. Görünümde 45° eğimli gövde ve mil döner; kap içindeki su yolu üründen ayrıdır. Granüller başlangıçta gerçek 15 mm çapındadır. Katı kütle azaldıkça eşdeğer çap küçülür. Hesaplanan sıvı hacmi yatay düzlem altında gösterilir; görünür olmak için %30 erime koşulu yoktur. Sıvı seviyesi bulunurken katıların suya değil eriyiğe yer değiştirdiği hacim hesaba katılır. Ortalama ürün sıcaklığı granül rengini belirler. İki ayrı büyütülmüş radyal kesit duvara yakın/iç yatak granül sıcaklıklarını gösterir. Ceket giriş/çıkışı, katı/sıvı kg, faz oranı, ürün gücü, kayıp ve dış yüzey haritası aynı seçili ana aittir. CSV ve seçili anın kütle/enerji JSON'u alınabilir.

Isıl zaman 60× / 300× / 600× hızlandırılır. Varsayılan izlenebilir gövde dönüşü ayrı bir gösterim saati kullanır; binlerce gerçek dönüşün videoda aynı fazda göründüğü iddia edilmez. Bu seçenek kapatılırsa gövde fazı hızlandırılmış ısıl zamana bağlanır ve stroboskopik görünebilir. Fiziksel toplam devir ayrıca yazılır.

Simülasyon sekmesi açıkken PDF raporu seçili erime modelini, yüzey haritasını ve katı/sıvı denetimini içerir. Formüller ve tüm koşu özeti de rapordadır. Türkçe/İngilizce kullanılabilir.

## Modelin anlamı

Bu görünüm **radyal entalpi çözümünün eşdeğer hacimli gösterimidir**. Bütün granüllere toplam kalan katı hacmiyle uyumlu eşdeğer yarıçap uygulanır. Konumların alt sınır noktasına benzerlik dönüşümüyle yaklaşması geometrik çökme gösterimidir; gerçek çökme dinamiği yeniden çözülmez. Radyal sıcaklık kesitleri iki popülasyonun sonuçlarıdır, her hareketli granülün bağımsız sıcaklık çözümü değildir. Eriyik CFD ve tüm erime süresince iki yönlü termo-DEM yoktur.

Önceki ayrıntılı mekanik hareket kaydı ve yeni temas hesabı **Model ve sonuçlar** sekmesindedir. v1.8'in eşleşen örnek kaydı 0,4 s oturma + 2 s fiziksel dönüştür; tüm erime çevrimi değildir. Yeni sürümde bu kısa kayıt uzun erime hesabıymış gibi uzatılmadı. Mekanik denetimler README_v18.md ve Verification_Motion_v18.md içinde korunur.

Varsayılan geçici wax örneği 600×800 mm, varsayımsal 150 mm bombe, 45°, 10 RPM saat yönü ve %50 yığın dolumudur. Yaklaşık **71,2 kg / 45.120 granül** verir. Kullanıcının 180 kg çikolata hedefi bu örnekle doğrulanmış değildir. Gerçek çikolata kartı, ekipman ölçüleri ve ölçümle kalibrasyon gerekir. Ağ varsayılanı 16×16 / radyal 24'tür; bölge sayısı otomatik düşürülmez.

## Sayısal kontroller

validation_melting_v19.json: 201 ara zamanda kütle/enerji/hacim kapanması; bağımsız tek tek küresel kap hacmi toplamına karşı hızlandırılmış hacim hesabı; 0°/45°/90° geometri; küçük erime oranlarının görünümü; başlangıç/son durum.

validation_desktop_v19.json: Paketlenen EXE'nin gerçek WebView2 arayüzü; iki yeni sekme, 20 adım, ara değerler, iki dil, zaman kontrolü, erime PDF'i, diğer dönüş kontrolleri ve bağımsız SciPy BDF/Radau ısıl karşılaştırması.

Isıl entegrasyon denklemleri değiştirilmedi. Görünüm için sonuç kaydı sıklaştırıldı: varsayılan tam koşuda 180 saklanan durum. Kayıt aralığı çözüm zaman adımı değildir. Önceki ağ/radyal/zaman yakınsama kontrolleri kendi sürüm numaralarıyla korunur. Sayısal korunum deneysel doğrulama değildir.

## English

Run **Rotary_Melter_Desktop_1_9.exe**. The new **Solution steps and equations** tab documents 20 ordered stages, execution timing, active code, worked values, actual stored-state audit, the first four midpoint steps and JSON export.

The separate **Simulation · melting** tab replays the complete thermal result with a rotating inclined vessel, volume-equivalent shrinking solids, liquid volume/level, mean-temperature colors, radial population profiles, water inlet/outlet and surface maps. Play/pause/rewind, minute selection, CSV/JSON and PDF export are available. Legible vessel rotation uses a clearly identified separate clock by default.

This is an enthalpy-result visualization with geometric settlement, not full-duration coupled thermo-DEM or melt CFD. The separate short mechanical recording remains available. Defaults are provisional wax, about 71.2 kg, and do not validate the intended 180 kg chocolate capacity. Numerical tests do not replace equipment measurements and calibration.
