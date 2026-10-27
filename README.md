# Rotary Melter — C++ Engineering Workstation 3.0

V11 / Desktop 2.2 temel alınarak geliştirilen döner eritici analiz programı. Ana ısıl hesap, parametre analizleri ve granül temas çözümleri **C++20** ile çalışır. Python masaüstü pencereyi, dosyaları ve C++ bağlantısını; JavaScript kullanıcı arayüzünü ve görselleştirmeyi yönetir.

Çalışma klasörü: `C:\Projects\Heat_Transfer_Rotary_Melter`. Önceki `Heat_Transfer` projesi bu çalışma kapsamında değiştirilmez. GitHub: [Heat_Transfer_Rotary_Melter](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter).

## Başlatma

**`BASLAT.cmd`** dosyasını çalıştırın. İlk kurulumda **`KURULUM.cmd`** kullanın: yerel `.venv`, Python bağımlılıkları, referans testleri için Node ve sabitlenmiş C++ derleyici/kütüphaneleri hazırlanır. Windows'ta Edge WebView2 ve Python 3.10–3.12 gerekir. Derleme araçları `.tools/`, derlenmiş motor `outputs/native/bin/` içinde kalır.

```powershell
. .\AKTIF_ET.ps1
.venv\Scripts\python.exe app.py
```

Bağımsız EXE: `releases/current/Rotary_Melter_Cpp.exe`; NVIDIA sürümü: `releases/current/Rotary_Melter_Cpp_GPU.exe`. EXE yerel Python/Node kurulumu istemez; WebView2 gerektirir. Mevcut V11 EXE ve özgün V1–V11 dosyaları diskte korunur.

NVIDIA kurulumu: `KURULUM_GPU.cmd`. Dashboard'daki NVIDIA eylemi, kaydedilmiş dış yüzey sıcaklıklarında CUDA C++ ile bağımsız taşınım/radyasyon alan kontrolü yapar. Ana zamana bağlı C++ çözümü CPU'dadır. RTX 4070 üzerinde float64 CPU/GPU farkı 1e-7 W eşiğinin altındadır; ilk derleme ve aktarım süresi ayrıca raporlanır. Küçük alanlarda CPU daha hızlıdır. GPU içeren EXE üretmek için `python -m tools.BuildDesktop --with-gpu` komutunu proje ortamında kullanın.

## Yeni çalışma akışı

1. Girdileri soldan düzenleyin; `/` ile arayın. `Ctrl+Enter` ile hesaplayın. Değişiklikler önceki sonucu güncel sonuç olarak göstermez.
2. Hesap merkezinden RK2 midpoint, RK4 veya adaptif Dormand–Prince seçin. Varsayılan RK2, V11 karşılaştırması için korunur.
3. Bağımsız analiz koşularının iş parçacığı sayısını seçin. Zaman adımları ve ortak granülleri etkileyen temaslar sırayla çözülür; büyük yüzey ağlarında bağımsız hücreler OpenMP kullanabilir.
4. **Ağ / zaman kontrolü**, yüzey ağını, zaman adımını ve granül radyal ağını ayrı karşılaştırır. **Duyarlılık ±%10**, RPM/debi/film/yenilenme etkilerini ve yerel elastisiteleri gösterir.
5. **İzlenebilirlik** bölümünden önceki çalıştırmaları açın. Sonuçlar, tam girdiler, seçili yöntem ve SHA-256 kayıtları birlikte saklanır.
6. **Markdown raporu**, PDF, CSV ve JSON çıktılarıyla sonucu inceleyin. Granül görünümünde temel oynatma kontrolleri modelin üzerinde, ayrıntılı hareket ayarları açılır bölümde bulunur.

Varsayılan başlangıç: ürün, metal ve ceket suyu 25 °C; su girişi 110 °C, sabit giriş modu. Dolum modunda kütle geometri/dolumdan hesaplanır: varsayılan gerçek yük yaklaşık 71,202 kg'dır. Güç sınırlı boiler modu ayrıca seçilebilir. Kullanıcının kayıtlı senaryoları otomatik olarak değiştirilmez.

`constant` su modeli girilen V11 sabitlerini korur. `if97_reference`, IAPWS-IF97 özelliklerini başlangıç/giriş sıcaklıklarının ortalamasında bir kez hesaplar; bu özellikler enerji çözümünde sabit kalır. Tek faz su varsayımı korunur.

## Kod ve kütüphaneler

| Sorumluluk | Kaynak |
| --- | --- |
| Isıl enerji denklemleri ve Odeint çözümü | [Calculation.cpp](native/src/Calculation.cpp) |
| Geometri, ıslanma, hidrolik, kapasiteler | [Geometry.cpp](native/src/Geometry.cpp) |
| Entalpi, IF97, izolasyon/çevre dengesi | [Thermodynamics.cpp](native/src/Thermodynamics.cpp) |
| Tipli girdi ve doğrulama | [Configuration.cpp](native/src/Configuration.cpp) |
| Paralel analiz ve yakınsama | [Analysis.cpp](native/src/Analysis.cpp) |
| Rijit/elastik granül temas çözümleri | [ContactDynamics.cpp](native/src/ContactDynamics.cpp) |
| Python–C++ taşıma katmanı | [NativeEngine.py](rotary_melter/NativeEngine.py), [NativeContactEngine.py](rotary_melter/dynamics/NativeContactEngine.py) |
| Dashboard, yöntem açıklamaları ve görünüm | `rotary_melter/web/interface/`, `visualization/` |
| Raporlar ve kullanıcı senaryo kütüphanesi | `Reporting.py`, `AnalysisReporting.py`, `Workspace.py` |

**Boost 1.90.0**: Odeint integratörleri ve TOMS748 kök çözümü. **Eigen 5.0.0**: LDLT ve vektör cebiri. **CoolProp/IF97 2.2.1**: su özellikleri. **BS_thread_pool 5.1.0**: bağımsız koşu paralelliği. **nlohmann/json 3.12.0**: veri sınırı. [Sürümler ve SHA-256](native/dependencies.lock.json), [lisans bildirimleri](native/third_party_licenses/).

V11 JavaScript ve bağımsız SciPy modeli regresyon için korunur; önceki Mixing Vessel modeliyle değiştirilmez.

## Denklemler ve raporlar

- [C++ formül kataloğu](docs/CPP_CALCULATION_EQUATIONS.md): 20 hesap aşaması; amaç, denklem, birim, kaynak satırları, kullanılan kütüphane ve literatür.
- [Calculation.py formül kataloğu](docs/CALCULATION_EQUATIONS.md): bağımsız Python referansının önceki ayrıntılı raporu.
- [C++ doğrulama ölçümleri](docs/CPP_VALIDATION_REPORT.md): V11 karşılaştırması, sayısal hassasiyet ve ölçülmüş çalışma süreleri.
- [Kod yapısı](docs/KOD_YAPISI.md), [geliştirme komutları](docs/CPP_DEVELOPMENT.md), [V11 kaynak kökeni](docs/V11_SOURCE_PROVENANCE.json).

VS Code'da Markdown önizlemesi **Ctrl+Shift+V**; yanında açma **Ctrl+K, V**. Markdown Preview Enhanced, C/C++ ve CMake Tools önerileri `.vscode/extensions.json` içindedir. Bu bilgisayarda ilgili uzantılar kurulmuştur.

Her masaüstü hesabı `outputs/runs/<run-id>/` içine sonuç JSON'u, zaman serisi CSV'si, Markdown raporu, formül kataloğu kopyası ve manifest yazar. Analizler ayrıca koşu CSV'si ve analiz raporu üretir. Senaryo kütüphanesi `%LOCALAPPDATA%\RotaryMelter\workspace.json` konumunda korunur. Paketli EXE'nin sonuçları EXE yanındaki `outputs/` içinde kalır; geçici açılma klasörüne yazılmaz.

## Komut satırı ve doğrulama

```powershell
.venv\Scripts\python.exe -m tools.BuildCpp
.venv\Scripts\python.exe app.py --run --output outputs/ornek_kosu
.venv\Scripts\python.exe app.py --analyse convergence --threads 4 --output outputs/yakinsama
.venv\Scripts\python.exe app.py --analyse sensitivity --threads 4 --output outputs/duyarlilik
.venv\Scripts\python.exe app.py --run --engine javascript --output outputs/v11_referans
.venv\Scripts\python.exe -m tools.RunChecks --desktop
.venv\Scripts\python.exe -m tools.DocumentCppEquations --check
```

Python gerektirmeyen C++ komut satırı motoru da üretilir:

```powershell
outputs\native\bin\rotary_melter_cpp.exe --input config\default_inputs.json --output outputs\native_cli.json
```

EXE derlemek için `.venv\Scripts\python.exe -m pip install -r requirements-build.txt` ardından `.venv\Scripts\python.exe -m tools.BuildDesktop` kullanın. Orijinal sürümler `releases/original/` altında korunur. `.venv`, `.tools`, önbellekler, hesap çıktıları ve EXE arşivleri Git'e eklenmez.

Enerji korunumu ve eski kodla sayısal uyum, gerçek ekipmanın erime süresini doğrulamaz. Malzeme özellikleri ile temas/devir katsayıları ölçümle kalibre edilmelidir; 3B görünüm bir CFD çözümü değildir.
