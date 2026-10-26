# v1.9 — Erime tekrar oynatma ve adım sekmesi denetimi

Yeni sürümün ısıl fiziği v1.8 ile aynıdır. Yalnız sonuç kaydı sıklaştırıldı ve iki yeni arayüz sekmesi eklendi. Varsayılan örnekte 180 kayıt bulunur; gerçek RK2 adımları bunlardan çok daha sıktır.

201 ara zamanda katı+sıvı kütlesi, entalpi enterpolasyonundan toplam depolama enerjisi ve katı yer değiştirme hacmi dahil sıvı seviyesi denetlendi. Hızlandırılmış küresel kap hacmi hesabı bağımsız olarak her kürenin kısmi hacmi tek tek toplanarak karşılaştırıldı. 0°,45°,90° eğimlerde küçülen kürelerin kap içinde kalması ve sıvı hacmi kontrol edildi. İlk denemede dik konumda orta-nokta dilimlerinin hacmi kesikli artırdığı görüldü. Son sürümde her sonlu eksenel dilim boyunca dolu disk oranı analitik olarak entegre edilir; bu hata giderildi. Küresel bombe, sonlu kesit geometrisiyle yaklaşık temsil edilmeye devam eder.

Küçük pozitif erime oranlarında sıvı seviyesi oluşur. Başlangıçta 45.120 adet 15 mm küre, sonda sıfıra yaklaşan toplam katı hacmi vardır. Tam süredeki görsel katı dağılımı homotetik geometrik dönüşümdür; mekanik çökmenin kanıtı değildir.

Gerçek paketli EXE/WebView2 üzerinde Türkçe/İngilizce gezinme, yeni sekmeler, 20 adım, gerçek ilk dört adım kaydı, tüm zaman çizgisi, oynatma saati, duraklatma ve başa alma, erime görünümüyle PDF üretimi sınandı. Önceki hareket sekmesi ve eşleşen kısa kayıt denetlendi. Aynı tam ısıl örnek bağımsız SciPy BDF/Radau ile karşılaştırıldı. Ayrıntılı sonuçlar validation_desktop_v19.json içindedir. Bu karşılaştırma aynı fiziksel katsayılara dayanır; deney değildir.

Önceki v1.8'in yaklaşık 22,8 dakikalık mekanik hesap kaydı korunur; v1.9'da tekrar yapılmış yeni bir uzun performans testi olarak sayılmadı. Bu sürümün testleri yeni arayüz ve erime hacmi/enerji gösterimine odaklanır. Gerçek çikolata ve ekipman ölçümleriyle bağımsız doğrulama henüz yoktur.

## Sayısal sonuçlar

- Interpolated thermal states conserve mass: PASS — {"maxKg": 1.4210854715202004e-14}
- Interpolated radial enthalpy conserves energy: PASS — {"maxRelative": 9.062178694867375e-11}
- Liquid level closes vessel-minus-solid volume: PASS — {"maxM3": 1.8221535391660382e-14}
- Physical 15 mm spheres retained at initial time: PASS — {"count": 45120, "normalization": 1.0000000000000004}
- Prefix sum displaced volume matches independent sphere-cap summation: PASS — {"maxM3": 5.589553125906477e-12}
- Horizontal, inclined and vertical geometry contain shrinking granules: PASS — [{"angle": 0, "maxEscapeM": 0, "liquidVolumeResidualM3": -2.0765724209614866e-15}, {"angle": 45, "maxEscapeM": 0, "liquidVolumeResidualM3": 1.8350121769317163e-15}, {"angle": 90, "maxEscapeM": 0, "liquidVolumeResidualM3": -1.3086320221900039e-16}]
- Liquid volume closes at horizontal, inclined and vertical orientations: PASS — [{"angle": 0, "maxEscapeM": 0, "liquidVolumeResidualM3": -2.0765724209614866e-15}, {"angle": 45, "maxEscapeM": 0, "liquidVolumeResidualM3": 1.8350121769317163e-15}, {"angle": 90, "maxEscapeM": 0, "liquidVolumeResidualM3": -1.3086320221900039e-16}]
- Small melt fractions produce liquid without a 30 percent visibility gate: PASS
- End state has no finite solid mass: PASS
- Dense thermal output history covers start and final state: PASS
