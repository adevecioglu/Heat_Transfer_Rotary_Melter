# Rotary Melter Desktop 1.8

## Kullanım

ZIP'i çıkarıp **Rotary_Melter_Desktop_1_8.exe** dosyasını açın. Başlıkta **1.8** yazmalı. Eski EXE dosyasını açmak bu değişiklikleri göstermez. Windows 64 bit/WebView2 gerekir; Python pakete dahildir.

**Dönüş açılışta görünür:** varsayılan 600×800 mm / 45° / 10 RPM saat yönü / %50 yığın dolumu / 15 mm wax granülleriyle eşleşen önceden hesaplanmış hareket otomatik oynar. Üstte `DÖNÜŞÜ VE GRANÜLLERİ OYNAT`, `Duraklat`, `Hesaplanan hareketi oynat` ve ayrı hareket zaman çizgisi vardır. Turuncu/mavi gövde işaretleri dönüşü görünür kılar. İşaretleri ve dış gövdeyi incelemek için `Yalnız gövde dönüşü` kullanılabilir; bu seçenek granül hesabı değildir.

Örnek kayıt **0,4 saniye ön oturma + 2 saniye fiziksel dönüş** içerir. Bu 120° dönüş gösterir; tam devir, kararlı rejim veya erime çevrimi değildir. `Hesaplanan kaydı tekrarla` açıkken aynı kayıt baştan oynar; yeni fizik hesaplanmaz. Ekranda kayıt kaynağı açıkça yazılır.

**Geometri/RPM/yön/dolum/çap veya temas ayarlarını değiştirince** örnek kayıt kullanılmaz. `Yeni hareket hesabı` ile yeni senaryo çözülür. Dönüş süresini 6 s girerseniz 10 RPM'de bir tam tur hesaplanır. Gerçek 45.120 küreyi temaslarıyla çözmek gerçek zamandan çok yavaştır; fiziksel saniye ile bilgisayarda geçen saniye ayrıdır. Adet/bölge sayısı otomatik azaltılmaz. Ayrıntılı parametrelerde adım ve hız/konum iterasyonları değiştirilebilir. Elastik temas DEM ayrıca seçilebilir. Yüksek örtüşme/kaçış sonuçları reddedilir.

`İçini göster`, granül izleri ve kareler arası hız renkleri seçenekleri var. Eğim dünya düşeyine göre uygulanır. Gövde, shaft ve görünür işaretler birlikte döner; joint yan portu sabit gösterilir. Sıcak su yalnız milin ayrı kanalları ve ceket içindedir. Hareket kaydı/konumlar JSON ve CSV, genel rapor PDF olarak alınabilir. Türkçe/İngilizce desteklenir.

## Fiziksel anlamı

Hareket artık yalnız statik bir granül çizimi değildir: rijit küre temasında yerçekimi, normal temas kısıtları, Coulomb sürtünmesi, duvarın temas hızı ve küre ataleti ilerletilir. Granüller aynı RPM'ye zorlanmaz. Yük %50 dolumdan hesaplanan yaklaşık **71,2 kg geçici wax**tır. Kullanıcının 180 kg çikolata hedefi doğrulanmış değildir.

Wax/çikolatanın gerçek sürtünme, şekil, yumuşama ve yapışma verisi yok. Rijit yöntem bir malzeme deformasyon modeli değildir; eriyik kuvvetleri basitleştirilmiştir ve ısıl ağ iki yönlü termo-DEM/CFD'ye bağlı değildir. Hareket görselleştirmesi gerçek ekipman performans garantisi değildir. Model/sayısal farklar Verification_Motion_v18.md dosyasında açıkça verilir.

## English

Run **Rotary_Melter_Desktop_1_8.exe** and confirm version 1.8. The matching default case automatically plays a computed physical-granule recording. It includes 0.4 s settling and 2 s rotation (120 degrees), not a full revolution or steady-state validation. Looping repeats the same recording. The source is labeled.

Changed geometry, speed/direction, fill, granule size or contact settings require **Compute new motion**. Motion uses all physical-size spheres; no automatic downsampling. Six seconds at 10 RPM gives one revolution, but computation is much slower than real time. Separate play/pause/replay and timeline controls are provided. Vessel-only preview is explicitly separate from particle dynamics. Input settings, positions and reports remain exportable. Thermal-grid functionality from v1.7 is retained.

The example is provisional wax, about 71.2 kg. It is not a validated 180 kg chocolate capacity, fully coupled melt CFD, or a calibrated deformable-material model.
