# Dönüş ve temas yöntemi - v1.8

İki ayrı yöntem seçilebilir: önceki elastik normal/teğetsel yaylı DEM ve yeni 3B rijit küre temas kısıtları. Rijit yöntem de her gerçek 15 mm granülü ayrı ilerletir; büyütülmüş temsilci parçacık kullanılmaz. Duvar hızı seçilen RPM/yöndedir; parçacık hızları zorla aynı RPM yapılmaz.

## Birincil yöntem kaynakları

- [Erin Catto, Solver2D (2024)](https://box2d.org/posts/2024/02/solver2d/): biriken normal/teğetsel darbeler, warm start ve hızdan ayrılmış konum düzeltmesi için yöntem açıklaması. Bu program Box2D çalıştırmaz; küresel 3B temaslar için ayrı bir uygulama kullanır.
- [Catto, Modeling and Solving Constraints (2009)](https://box2d.org/files/ErinCatto_ModelingAndSolvingConstraints_GDC2009.pdf): ardışık darbe çözümünün temeli. 2B örnekler wax/çikolata için deneysel doğrulama değildir.
- [Baraff (1994), Fast contact force computation for nonpenetrating rigid bodies](https://doi.org/10.1145/192161.192168): rijit cisim/sürtünme temasının genel fiziksel çerçevesi. Buradaki algoritma makalenin tam uygulaması değildir.

## Bu uygulamada yapılanlar

Kürenin dönme ataleti I=2mr²/5 alınır. Komşuluk araması, yerçekimi, normal bağıl hız kısıtı, biriken Coulomb teğetsel darbeleri ve duvarın temas noktasındaki açısal hızı çözülür. Bir önceki adımdaki temas darbeleri yalnız temas kimliği/geçerli adım eşleşirse başlangıç tahminine taşınır. Konum düzeltmesi doğrudan kinetik hız olarak eklenmez. Temas hatasını aşırı büyüten kaba ayarlar reddedilir; ayrıklaştırma hatasının küçük olması için adım/iterasyon incelemesi yine gereklidir.

Küre yarıçapı 7,5 mm korunur. Rijit yöntemde kalan örtüşme sayısal artık olup wax deformasyonu değildir. Ceket/mil suyu ürün hacmine girmez. Eğim yerçekimi bileşenlerine uygulanır; dünyada düşey sabittir.

## Sınırlar

Temas katsayıları ölçülmedi. Rijit küre yöntemi yumuşayan/yapışan gerçek waxın tam malzeme yasası değildir. Gaz/eriyik akışı ve sıcaklığın granül bazında temas alanına geri beslemesi çözülmez; kısmi erime seçili bir başlangıç fazı olarak kullanılır. Isıl model ayrı iki granül popülasyonu/radyal entalpi ağıdır. Bu nedenle hareket kaydı bir görselleştirme ve koşullu mekanik çözüm olarak değerlendirilmelidir; gerçek erime süresi veya kapasite validasyonu değildir.

Gövde önizlemesi, yeni mekanik hesap ve önceden hesaplanan eşleşen örnek kayıt arayüzde ayrı etiketlenir. Örnek; geometri, devir/yön, dolum, granül çapı, yoğunluk ve temas ayarları eşleşmezse kullanılmaz. Kayıt başa döndüğünde yeni bir fiziksel çevrim hesaplanmış olmaz; yalnız kayıt tekrar oynatılır.
