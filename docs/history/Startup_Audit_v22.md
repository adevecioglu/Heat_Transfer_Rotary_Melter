# Su giriş–çıkış ΔT başlangıç denetimi — v2.2

## Kullanıcının doğruladığı koşul

Ceket suyu yaklaşık 25 °C, metal ve ürün 25 °C; ceket girişine 110 °C su gelmeye başlıyor. Yeni varsayılan `waterInitial=25`, `metalInitial=25`, `tin=110`, `sourceMode=1` bu sınır koşulunu kullanır. Sabit giriş kaynağının anlık gücü hesaplanır; 30 kW boiler varsayımı uygulanmaz. Gerçek 110 °C kaynağının rezervuar, ısıtıcı ve kontrolü ayrı tasarım konusudur.

Önceki kayıtlı taslak `waterInitial=110`, `metalInitial=25`, `sourceMode=0`, `boiler=30`, `efficiency=0.95` idi. Bu hem sıcak suyla önceden dolu devreyi hem güç sınırlı kaynağı tanımlıyordu. Kullanıcının tarif ettiği soğuk ceket / sabit 110 °C giriş koşulu değildi.

## 2,56 K neden çıkıyordu?

Model girdileriyle ṁ=10/3600×950=2,63889 kg/s; ṁcp=11,13611 kW/K.

Doğrudan dönüş–ısıtıcı bağlantısında net boiler gücü en çok 30×0,95=28,5 kW: Tin−Tout ≤ 28,5/11,13611 = 2,55924 K. Bu modda Tin 110 °C'de kalmaz. Örneğin yaklaşık 15 s'de Tin=97,18 °C, Tout=94,62 °C idi.

Bu sınır bütün gerçek kapalı devreler için evrensel bir sınır değildir. Buradaki doğrudan, gecikmesiz kaynak bağlantısı ve eşdeğer su hacmi modeline aittir. Harici sıcak depo veya devre ısıl kapasitesi ayrı elemanlarla çözülmüyor.

## Sabit girişle karşılaştırma

| Başlangıç suyu / kaynak | t≈0: Tin / Tout | t≈15 s: Tin / Tout | t≈30 s: Tin / Tout |
|---|---|---|---|
| Eski: 110 °C / güç sınırlı | 110 / 110 | 97,18 / 94,62 | 95,49 / 92,93 |
| 110 °C / sabit giriş 110 °C | 110 / 110 | 110 / 95,08 | 110 / 101,62 |
| Doğrulanan: 25 °C / sabit giriş 110 °C | 110 / 25 | 110 / 44,40 | 110 / 95,04 |
| 25 °C / güç sınırlı | 27,56 / 25 | 28,14 / 25,58 | 29,98 / 27,42 |

Bunlar mevcut geçici film/malzeme/geometri değerleriyle çözülen senaryolardır, gerçek ekipman ölçümü değildir. Soğuk ceket / sabit girişte ilk ΔT 85 K'dir. Bu ilk sıcak–soğuk su değişimi ve su/metal enerji depolamasıyla ilgilidir; 85 K'nin tüm eritme süresince kalacağı veya buna göre sürekli yaklaşık 0,95 MW boiler satın alınacağı anlamına gelmez. Gerekli anlık net kaynak, sıcak su deposu kapasitesi ve sürdürülebilir ısıtıcı gücü ayrı değerlendirilmelidir.

## Su enerji dengesi

F(Tin−Tout) = Q_su→metal + Q_ek_devre_kaybı + dE_su/dt.

Ürüne geçen güç tek başına FΔT'ye eşitlenemez. İlk anda bütün su ve metal 25 °C ise su→metal akısı tam t=0'da sıfırdır; giren akışın net enerjisi önce su hacminde depolanır. Sıcak suyla önceden dolu eski örnekte bunun tersi olur: FΔT=0 iken yaklaşık 421,7 kW su→metal akısı, suyun depolanmış enerjisinden karşılanır.

Önceki sıcak-su başlangıcının ortam 25 °C'ye göre yaklaşık 4,625 kWh hazır su enerjisi vardı. Başlangıç suyunu ön ısıtmanın enerjisi eski koşunun kaynak tüketimine dahil değildi. Soğuk başlangıç bu hazır enerjiyi varsaymaz.

## Görüntüleme sorunu da düzeltildi

Eski uzun analizde ilk saklanan iki nokta 0 ve yaklaşık 30 s idi. Arada çözücü çok daha küçük adımlarla çalışsa da grafik/oynatma bu seyrek kayıtları kullanıyor ve ilk saniyelerdeki geçişi yumuşatıyordu. Yeni kayıt: ilk 2 s'de 0,1 s, 2–20 s'de 0,5 s, 20–120 s'de 2 s; daha sonra önceki kayıt aralığı. Gerçek örnek zamanları çözücü adımına denk gelen yakın anlardır. Çözücü adımı ve 16×16 / radyal 24 hassasiyet değiştirilmedi.

## Bağımsız kontrol ve sınırlar

Dört başlangıç/kaynak senaryosu ilk 120 s için ayrı NumPy/SciPy BDF ve Radau montajıyla çözüldü. JS orta-nokta RK2 ile çıkış sıcaklığı farkı en çok yaklaşık 0,001 °C idi. Paylaşılan geometri, film ve malzeme katsayıları vardır; bu karşılaştırma deneysel doğrulama değildir.

Ek 20 L devre hacmi hâlâ eşdeğer eksenel su düğümlerine dağıtılmıştır. Toplam su yaklaşık 48,86 L, bunun eşdeğer geçiş süresi 17,59 s'dir; bunu yalnız gerçek ceket geçiş süresi diye yorumlamamak gerekir. Gerçek boru/mil gecikmeleri, sensör dinamiği, sıcaklıkla değişen su özellikleri ve ayrı sıcak depo/boiler kontrolü bu modelde çözülmez. Hidrolik basınç ve tek-faz sıvı su uygunluğu ayrıca doğrulanmalıdır.

## Kaynaklar

- Spirax Sarco, ısıtılan tanklarda sıvı, metal ve kayıp bileşenlerinin ayrı enerji hesabı: https://www.spiraxsarco.com/learn-about-steam/steam-engineering-principles-and-heat-transfer/energy-consumption-of-tanks-and-vats
- Spirax Sarco, debi–ısı yükü ve sıcaklık kontrollü kaynak ilişkisi: https://www.spiraxsarco.com/learn-about-steam/condensate-removal/the-heat-load-heat-exchanger-and-steam-load-relationship

