# v1.8 - Dönüş ve granül hareketi doğrulama kaydı

## Ekrandaki sorunun düzeltilmesi

Önceki ekranda yalnız başlangıç geometrisi görünüyordu; hareket çok yavaş bir elastik DEM düğmesinin arkasındaydı. v1.8'de eşleşen varsayılan senaryonun hesaplanmış hareketi açılışta oynatılır. Yeni hesap, gövde önizlemesi ve kayıt oynatma ayrıdır. Fiziksel zaman / bilgisayarda geçen zaman ayrılır. Kısa işlerde son kareden önceki karelerin kaybolması ve kaydın yalnız dönüş zamanını sayarak ön oturmayı atlaması da düzeltildi. Sonlanma karşılaştırmalarına kayan nokta toleransı eklendi.

## Tam boy örnek

600 mm iç çap, 800 mm silindir, varsayımsal 150 mm küresel bombe, 45°, 10 RPM saat yönü, %50 yığın dolumu, geçici wax, 15 mm gerçek çap. Sayı: **45120**; kütle 71.202124 kg. Normal/teğetsel kısıtlar her küre için çözülür. Bir tanecik çok sayıda büyük taneciği temsil etmez.

- Adım: 0.001041666667 s; hız/konum iterasyonu: 64 / 12.
- Kaydedilen ön oturma: 0.400000 s; dönüş: 2.000000 s = 120°.
- Bu kesite kadar bilgisayar süresi: **1366.48 s = 22.77 dakika**. Bu fiziksel dakika değildir.
- Kaydedilen kare sayısı: 49. Her kare aynı gerçek granüllerin hesaplanan konumlarıdır. Oynatmada kareler arasında doğrusal enterpolasyon kullanılır.
- Son kare artık örtüşme/r: %0.130860; süreçteki en büyük değer: %4.257919. En büyük geçici değer ilk oturma/dönüş başlangıcını da içerir. Bu wax deformasyonu veya termal temas alanı değildir.
- Son kare ortalama granül yörünge devri: -9.278229 RPM; gövde -10 RPM. Zıt yönde hareket eden tanecik oranı: %4.816046. Tanecikler gövde hızına zorlanmadı.
- Kaydedilen karelerde kaçış yok, konumlar sonlu. İki saniye bir tam tur/kararlı rejim kanıtı değildir.

Kayıt, aynı denklemleri kullanan önceki aritmetik düzenle hesaplandı. Güncel birleşik normal/teğetsel darbe uygulamasıyla A/B kontrolünde tam boy kısa koşudaki konum farkı 7.61e-14 m, hız farkı 3.39e-11 m/s idi. Küçük sistemde 150 adımda konum farkı 4.59e-10 m. Bu kontrol performans düzenlemesinin yöntemini sınar; fiziksel kalibrasyon değildir. Önceki uygulama da kaynak pakette bulunur.

## Analitik ve alternatif yöntem kontrolleri

15 odaklı kontrol geçti: analitik iki küre restitüsyonu, lineer/açısal momentum, eğimli eksende serbest düşme, 217 gerçek küreli küçük tankta her iki dönüş yönü, sıfır duvar sürtünmesi, yarım zaman adımı, kaçış/sonluluk ve arka plan duraklat/devam davranışı.

Aynı 217 küreli küçük kapta elastik DEM ile rijit temas ayrıca çözüldü. Ortalama yörünge devri farkı %1.437; ortalama tanecik hızı farkı **%24.243**. Bu iki mekanik kapanışın tamamen aynı sonucu vermediğini gösterir. Küçük sistemde adım yarıya inince de metrikler değişir; yoğun tam boy yatağın mekanik yakınsaması tamamlanmış ilan edilmedi. Gerçek sürtünme/yapışma ve deney verisi gerekir.

## Uygulama testleri

Paketli EXE'de başlatma, gerçek granül konumlarının değişmesi, negatif CW fazı, ön oturma kareleri, oynatma, duraklatma, zaman çizgisi, gövde saat adımı, iki dil, PDF, SciPy ısıl çapraz çözüm ve paketlenmiş örnek kayıt sınandı. Başka bir eğimde kayıt kullanımı reddedildi. Tanı çıktısı validation_desktop_v18.json içindedir.

İlk rijit denemelerde kabul edilemez örtüşme görüldü; o ayarlar kullanılmadı. Reddedilen/geçersizleşen denemeler ayrı durum etiketiyle saklandı. Küçük enerji artığı veya küçük örtüşme gerçek malzeme doğruluğunun kanıtı değildir.

## Sınırlar

Bu bir koşullu mekanik görselleştirmedir. Rijit küre yöntemi yumuşak/yapışan waxın malzeme modeli değildir. Tam iki yönlü termo-DEM ve eriyik CFD yoktur. Isıl model iki granül popülasyonunun radyal entalpi ağıdır. Gerçek 180 kg çikolata kapasitesi, gerçek erime süresi veya üretim performansı bu kayıtla doğrulanmadı. Malzeme kartı ve farklı devir/yüklerde bağımsız ölçüm karşılaştırması gereklidir.

Yöntem kaynakları Motion_Research_v18.md dosyasındadır. Önceki ısıl ağ kontrolleri kendi sürüm numaralarıyla korunur; bu sürümde değişmeyen ısıl motorun ağ mertebesi yeniymiş gibi raporlanmadı.
