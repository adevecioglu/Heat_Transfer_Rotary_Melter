# v2.0 — Çalışma alanı ve masaüstü doğrulaması

Bu sürümün hedefi proje yönetimi ve kullanılabilirliktir. Isıl/mekanik denklemler ve erime geometri kapanışı v1.9 ile dosya özeti düzeyinde aynıdır (validation_physics_unchanged_v20.json). Yeni fiziksel doğrulama yapıldığı iddia edilmez.

## Gerçek paketli EXE

Son dağıtım EXE'si WebView2 ile gizli test modunda başlatıldı. Varsayılan tam ısıl çözüm, bağımsız SciPy BDF/Radau, kısa gerçek mekanik hesap, paketli eşleşen kayıt, iki dil, erime zaman çizgisi ve PDF kontrolleri çalıştı. Yeni çalışma alanında yerel senaryo kaydı ve yeniden okuma, taslak kaydı/geri yükleme, birleştirmede aynı kaydı çoğaltmama ve kimlik çakışmasında iki içeriği de koruma, geçersiz girdi reddi, silme/geri alma, eski sonucun yeni girdiye bağlanmaması, güvenli ad gösterimi, CSV kaçışları, arama, temel/gelişmiş görünüm, pasif yük girdileri ve odak modu denetlendi. Testler kullanıcının normal kayıt dosyasına yazmaz; ayrı test deposu kullanır.

## Yerel kayıt motoru

Ayrı geçici dizin testleri UTF-8 veriler, revizyon kontrolü, iki eşzamanlı yazıcıdan yalnız birinin kayıt yapması, NaN ve çift kimlik reddi, bozuk dosyanın üzerine yazılmaması ve atomik değiştirmeyi denetledi. Yerel dosya sınırı 8 MB / 500 senaryodur; analiz çözünürlüğü kısıtlanmaz.

## Görsel kontrol

Gerçek Edge başsız tarayıcıda 1440×1050 ve 1000×768 görünüm alındı. Altı sekmenin görünmesi ve tıklanabilmesi, sayfa taşması olmaması, ilk açılışta pasif kg alanı, girdi sayacı, panel gizle/göster ve arama kontrol edildi. Proje görünümündeki 5 ve 10 RPM örnekleri ayrı ısıl hesaplardan üretildi; temsili uydurma sonuçlar kullanılmadı. PNG'ler örnek çalışma ekranıdır, ilk açılışta kullanıcının kütüphanesi boştur veya kendi kayıtlarını içerir.

## Sınırlar

Uygulama düzeyindeki bu kontroller ekipman üzerinde erime süresini, boiler kapasitesini veya RPM kapanışını doğrulamaz. Varsayılan wax ve temas verileri geçicidir. Ayrıntılı kaynak/model sınırları önceki README ve doğrulama dosyalarında korunur. Yeni tam-süre CFD/termo-DEM veya 20–30 dakikalık yeni mekanik performans testi bu sürümde yapılmış gibi raporlanmadı.

Yerel depo: 7 kontrol geçti.

Görsel iş akışı: 12 kontrol geçti.

EXE çalışma alanı: 23 kontrol geçti.
