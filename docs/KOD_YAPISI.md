# Rotary Melter kod ve klasör yapısı

**3.0 güncellemesi:** üretim hesabı ve temas dinamiği `native/src/` altındaki
C++20 motoruna taşındı. Güncel sorumluluklar ve komutlar:
[C++ geliştirme yapısı](CPP_DEVELOPMENT.md). Aşağıdaki V11 JavaScript/Python
dosya eşleştirmeleri, korunan referans uygulamaları ve arayüzü açıklamaya devam eder.

Kök dizin: `C:\Projects\Heat_Transfer_Rotary_Melter`.

```text
Heat_Transfer_Rotary_Melter/
├── app.py                       Küçük başlatıcı
├── BASLAT.cmd / KURULUM.cmd      Yerel ortamla açılış ve kurulum
├── AKTIF_ET.ps1 / DERLE.ps1      Terminal ortamı ve EXE derleme
├── requirements*.txt            Sabitlenmiş Python bağımlılıkları
├── rotary_melter/
│   ├── Calculation.py           Bağımsız SciPy ısıl/hidrolik çözümü
│   ├── Configuration.py         JSON senaryosu okuma/yazma
│   ├── Interface.py             WebView2 penceresi ve yerel API
│   ├── JavaScriptEngine.py      Arayüzle aynı hesabı Node'da çalıştırma
│   ├── Reporting.py             Arayüzsüz JSON/CSV/HTML çıktıları
│   ├── Workspace.py             Atomik, revizyon kontrollü senaryo kaydı
│   ├── CommandLine.py           Komut satırı ve açılış akışı
│   ├── Paths.py                 Proje, kaynak ve paketli dosya yolları
│   ├── dynamics/
│   │   ├── ContactDynamics.py          Yerel DEM ve arka plan işleri
│   │   ├── FastContactDynamics.py      Hızlı temas araması/entegrasyonu
│   │   ├── RigidBodyDynamics.py        Rijit cisim darbeleri
│   │   └── BaselineRigidDynamics.py    Önceki rijit çözücü karşılaştırması
│   └── web/
│       ├── calculations/        Ana hesap, geometri/hidrolik, su devresi,
│       │                        bölgesel ısı, granül iletimi, yakınsama, erime
│       ├── interface/           Formlar, denetim panelleri ve senaryolar
│       ├── visualization/       Tank, granül hareketi ve erime çizimleri
│       ├── reporting/           Masaüstünün mevcut PDF raporları
│       ├── assets/              Tank/mil/bağlantı referans görselleri
│       ├── Interface.template.html
│       ├── manifest.json        Modüllerin açık yükleme sırası
│       └── RunCalculation.cjs   Node hesap giriş noktası
├── tests/                       Python iş akışı ve yerel temas testleri
│   └── javascript/              Güncel ısıl/hidrolik/yakınsama kontrolleri
├── tools/                       Arayüz/EXE üretimi, test ve Node kurulumu
├── config/                      V11 varsayılan ve örnek JSON girdileri
├── docs/                        Kod, denklem ve geçiş belgeleri
│   └── history/                 Önceki araştırma ve kullanım notları
├── reference/                   Karşılaştırma verileri ve hareket kaydı
├── validation/original/          Önceki sayısal doğrulama çıktıları
├── outputs/                     Yeni hesap/test/derleme çıktıları; Git dışında
├── releases/                    Orijinal sürümler ve yeni EXE; Git dışında
├── .venv/                       Projeye ait Python ortamı; Git dışında
└── .tools/                      Projeye ait Node.js; Git dışında
```

## Hesap kodunu takip etme

Masaüstü hesapları `web/calculations/` altında JavaScript olarak çalışır. `manifest.json` içindeki `ENGINE` sırası önemlidir: temel `Calculation.js` yüklendikten sonra geometri/hidrolik, devre, bölgesel ısı, granül iletimi ve yakınsama modülleri aynı `RotaryModel` arayüzünü genişletir. Son üretim modeli granül ısı iletimi modülünden gelir. Yalnız temel dosyayı yüklemek, tam V11 modeliyle aynı hesap değildir.

`Calculation.py`, dışa aktarılmış aynı geometri ve katsayılarla ısı akılarını Python'da yeniden kurup SciPy BDF/Radau ile çözen bağımsız karşılaştırmadır. JavaScript'in yerine sessizce kullanılmaz. `JavaScriptEngine.py` ise `--run` komutunda doğrudan üretim modelini çalıştırır.

## Eski dosya → yeni yer

| Önce | Şimdi |
| --- | --- |
| `desktop.py` | `rotary_melter/Interface.py` |
| `reference_solver.py` | `rotary_melter/Calculation.py` |
| `workspace_store.py` | `rotary_melter/Workspace.py` |
| `dem_native.py`, `dem_fast.py`, `dem_rigid.py` | `rotary_melter/dynamics/` altındaki görev adları |
| `model.js` | `web/calculations/Calculation.js` |
| `mechanics.js` | `web/calculations/GeometryAndHydraulics.js` |
| `regional.js`, `particle_thermal.js` | `RegionalHeatTransfer.js`, `ParticleHeatTransfer.js` |
| `accuracy.js`, `melt_model.js` | `Convergence.js`, `Melting.js` |
| `app.js`, `*_ui.js` | `web/interface/` |
| `view.js`, `*_view.js`, `particle_renderer.js` | `web/visualization/` |
| `report.js`, `report_v14.js` | `web/reporting/` |
| `build.py`, `build_desktop.ps1` | `tools/BuildInterface.py`, `tools/BuildDesktop.py`, `DERLE.ps1` |

Kaynaktan açılış ve `--build`, tek HTML dosyasını `outputs/web/` içine üretir. Üretilmiş HTML kaynak dosyası olarak Git'e eklenmez. `tools.RunChecks` bütün test çıktılarını ayrı klasöre yazar; orijinal doğrulama kayıtlarını yenileriyle karıştırmaz.
