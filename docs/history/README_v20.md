# Rotary Melter Desktop 2.0

ZIP'i çıkarıp **Rotary_Melter_Desktop_2_0.exe** dosyasını açın. Başlıkta 2.0 yazmalıdır. Windows 64 bit ve WebView2 gerekir; Python paketin içindedir.

## Daha kullanışlı çalışma alanı

- Altı sekmenin tamamı görünürdür. Önceki sürümde aktif olmayan sekme düğmelerinin gizlenmesine yol açan seçici düzeltildi.
- Üstte her sekmeden erişilen **Hesapla / Isıl hesabı durdur**, geçen hesap süresi ve **Sonuçlar güncel / Girdiler değişti / Hesaplanıyor** durumu vardır. Süre sayacı bilgisayarda geçen zamandır; modelin fiziksel erime süresi ayrı gösterilir.
- Üst özet geometri, hesaplanan yük, koşullu hedef süresi ve su hattı kaybını gösterir. Girdiler değişince eski süre ve basınç kaybı güncelmiş gibi gösterilmez.
- Türkçe/İngilizce girdi araması; temel/tüm gelişmiş girdiler görünümü. Gizli değerler hesapta kullanılmaya devam eder. Yük dolumdan belirleniyorsa kg alanı, kütleden belirleniyorsa dolum alanı kullanılmaz ve pasif gösterilir.
- **Girdileri gizle/göster** ile simülasyon ve rapor alanı büyütülür. **Ctrl+Enter** hesaplar; **/** girdi aramasını açar.
- Ağ bilgisi açılır ayrıntıya taşındı; kararlılık adımı ve kullanıcı zaman adımının farkı korunur.

## Projeler ve karşılaştırma

1. Girdileri düzenleyin ve analizi çalıştırın.
2. **Projeler ve karşılaştırma** sekmesinde bir senaryo adı ve mühendislik notu yazın.
3. **Yeni senaryo olarak kaydet** deyin. Güncel sonuç varsa koşu özeti de saklanır; değiştirilmiş girdiler yalnız ayar olarak kaydedilir.
4. Farklı çap, yük, RPM veya su koşulları için tekrarlayın. Hesaplanmış kayıtlar yük, süre, kaynak kWh/kg, ısı kaybı ve su basınç kaybıyla karşılaştırılır.

Karşılaştırma kayıt anındaki özetleri gösterir. Hedefe ulaşmayan veya çalışma hacmine sığmayan koşulda özgül enerji verilmez. Senaryoyu **Girdileri yükle** ile açmak yeni analiz başlatmaz; yeni sonuç için Hesapla gerekir. İsimler aynı olsa bile yeni senaryo eski kaydı ezmez. Silinen son kayıt **Son silmeyi geri al** ile geri alınabilir; bu geri alma bilgisi uygulama oturumuna aittir.

**Proje JSON dışa aktar** kütüphaneyi ve mevcut girdi taslağını taşınabilir dosyaya yazar. **Proje JSON birleştir** mevcut kayıtları silmeden ekler. Aynı kimlikli ve tamamen aynı kayıt tekrar eklenmez. Aynı kimlikli farklı içerik yeni kimlikle korunur. Geçersiz proje dosyası bütün olarak reddedilir. Üstteki eski **JSON yükle** düğmesi de proje dosyasını tanır; eski tek-koşu girdi dosyaları desteklenmeye devam eder.

## Otomatik taslak ve yerel kayıt

Son girdi taslağı, değişiklikten 0,6 saniye sonra yerel olarak kaydedilir. Açılışta kendiliğinden yeni analize uygulanmaz: **Taslağı girdilere geri yükle** ile devam edilir. Bu işlem geçmiş sonuçları geri getirmez. Tam simülasyon dizileri ve bütün hareket kareleri proje kütüphanesinde saklanmaz; ayarlar ve özetler saklanır.

Yerel kayıt Windows'ta **%LOCALAPPDATA%\RotaryMelter\workspace.json** dosyasındadır. Yazma önce geçici dosyaya yapılır, ardından atomik olarak değiştirilir. Dosya kilidi ve revizyon kontrolü iki pencerenin birbirinin verisini ezmesini engeller. Başka pencerede kayıt değişmişse **Yerel kayıtları yeniden oku** ile güncel kütüphaneyi alın; açık girdileriniz değişmez. Okuma/yazma başarısızsa ekranda hata gösterilir ve otomatik üzerine yazma engellenir. Açık veriler proje JSON olarak dışa aktarılabilir.

Kütüphane en çok 500 senaryo / 8 MB tutar. Bunlar yalnız kayıt sınırlarıdır; analiz ağı veya çözüm süresi sınırı değildir. Büyük çalışmalar ayrı proje JSON dosyalarına ayrılabilir. Çıktılar kullanıcı tarafından seçilen konuma kaydedilir.

## Analiz ve simülasyonun kapsamı

v1.9'un **Çözüm adımları ve formüller** ile **Simülasyon · erime** sekmeleri korunur: 20 adım, gerçek ara değerler, entalpiye bağlı katı küçülmesi/sıvı seviyesi, radyal sıcaklık kesitleri, giriş/çıkış suyu, yüzey haritası ve PDF/CSV/JSON. Ayrıntılar README_v19.md içindedir. Ayrı mekanik dönüş kaydı ve yeni temas hesabı da korunur.

Bu sürümde ısıl ve mekanik çözücü denklemleri değiştirilmedi. Sayısal korunum fiziksel kalibrasyon değildir. Varsayılan wax kartı, temas/RPM katsayıları ve bazı geometri/hat ölçüleri geçicidir. Örnek yaklaşık 71,2 kg / 45.120 granüldür; 180 kg çikolata kapasitesini doğrulamaz. Tam erime görünümü entalpi sonuçlarının eşdeğer hacimli gösterimidir, tüm süre boyunca iki yönlü termo-DEM veya eriyik CFD değildir.

## Kontroller

- `validation_desktop_v20.json`: Paketlenen gerçek EXE/WebView2 üzerinde senaryo kaydı, yerel yeniden okuma, taslak geri yükleme, birleştirme, kimlik çakışması, sil/geri al, eski sonuçların kullanılmaması, iki dil, arama/temel görünüm ve odak görünümü. Önceki erime/dönüş/PDF ve bağımsız SciPy BDF/Radau kontrolü de çalışır.
- `validation_workspace_v20.json`: Ayrı geçici dizinde UTF-8, atomik kayıt, revizyon çakışması, eşzamanlı yazma, bozuk kaydı koruma, NaN/çift kimlik reddi.
- `validation_visual_v20.json`: Gerçek Edge ile 1440/1000 px görünüm, altı görünür sekme, taşma kontrolü, arama, odak modu ve 20 adım. Önizleme resimlerindeki 5 ve 10 RPM sonuçları ayrı olarak hesaplandı; kalibrasyon değildir.

## English

Run **Rotary_Melter_Desktop_2_0.exe**. Version 2.0 adds a persistent local scenario library, engineering notes, recorded result comparisons, project JSON merge/export, draft recovery, bilingual input search, basic/advanced fields, focus mode, global calculate/stop controls and clear stale/current status. All six navigation tabs remain visible.

Saving changed inputs stores no stale result summary. Loading a scenario or draft requires a new calculation. Full result arrays are not restored. Local storage is atomic and revision-checked; concurrent conflicts and corrupt records are not silently overwritten. A library is limited to 500 scenarios / 8 MB, independently of solver resolution. The calculation equations and physical validation status are unchanged from v1.9. See the earlier README files for modeling limitations.
