# Literatür ve model kararları — 21 Ekim 2026

Bu sürüm ağ ve zaman hassasiyetini geliştirir. Tam bağlaşık CFD–DEM veya deneyle doğrulanmış wax/çikolata modeli değildir. Kaynaklardan farklı malzemeye ait katsayılar doğrudan aktarılmadı.

| Birincil kaynak | Bu çalışma için çıkarım ve uygulamadaki durum |
|---|---|
| [NASA NPARC, Examining Spatial (Grid) Convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html) | Üç sistematik ağla gözlenen mertebe ve koşullu GCI hesaplanır. Sayısal yakınsama fiziksel geçerlilikten ayrılır. v1.7 yüzey ağlarını aynı dt ve radyal çözünürlükte çözer, zaman ve radyal inceltmeyi ayrıca test eder. Monotonluk, küçülen fark ve zaman çözünürlüğü koşulları sağlanmazsa GCI verilmez. Üç noktalı GCI tek başına asimptotik rejimi kanıtlamaz. |
| [Mellmann (2001), The transverse motion of solids in rotating cylinders](https://doi.org/10.1016/S0032-5910(00)00402-2) | Hareket rejimi; Froude sayısı, dolum, duvar sürtünmesi, parça/kap çap oranı ve yatak özelliklerine bağlıdır. Yalnız RPM üzerinden gerçek bir optimum ilan edilemez. Eğimli, eriyen ve yapışabilen wax için kuru tambur rejim haritası doğrudan doğrulama sayılmaz. |
| [Experimental validation of a particle-based method for heat transfer incorporating interstitial gas conduction in dense granular flow using a rotary drum (2022)](https://www.sciencedirect.com/science/article/pii/S0921883122000036) | İndirekt ısıtılan tamburdaki cam küre deneyleri, temasla birlikte gözenek gazı iletiminin de modellenmesini destekler. Uygulama şimdilik iki granül popülasyonlu etkin yatak kapanışı kullanır; makaledeki parçacık bazlı termal ağı uygulamaz. |
| [Rangel et al. (2024), Efficient discrete element modeling of heat generation and transfer in granular flows](https://doi.org/10.1016/j.powtec.2024.119719) | Yapay mekanik yumuşatma termal temas alanını etkileyebilir. Bu nedenle mevcut DEM örtüşmelerinden doğrudan termal temas iletkenliği üretilmedi. Yoğun yatak sertlik/adım yakınsaması ve malzeme kalibrasyonu tamamlanmadan DEM'den gerçek erime süresi türetilemez. |

## Sıradaki fiziksel doğrulama

Gerçek granül DSC/entalpi eğrisi, cp, k, yoğunluk, eriyik viskozitesi ve granül–granül / granül–316 sürtünmesi ölçülmeli. Gerçek bombe ve ceket dağıtıcı geometrisi gerekli. Duvar/su/ürün sıcaklıkları, debi ve giriş gücü farklı RPM/yüklerde eşzamanlı kaydedilmeli. Bir veri setiyle kalibre edilen model ayrı bir koşuyla sınanmalı. Bu bilgiler olmadan daha fazla hücre, bilinmeyen fiziksel katsayıların yerini tutmaz.

## English

The update separates spatial, temporal and intragranule resolution studies. Three surface grids share dt and radial cell count. Conditional GCI is withheld for oscillating, noncontracting or time-resolution-limited sequences. Numerical agreement does not determine material/contact coefficients. Current motion DEM and the two-population radial enthalpy solver are not a fully coupled thermal DEM or melt-flow CFD model. The cited experiments use other materials/geometries and do not validate this vessel.
