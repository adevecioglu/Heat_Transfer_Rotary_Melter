# Rotary Melter — V11 çalışma projesi

GitHub: [adevecioglu/Heat_Transfer_Rotary_Melter](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter).

Eğimli, dönen eritme tankının **V11 / Desktop 2.2.0** sürümünü temel alan geliştirme alanı. Doğrulanan başlangıç korunur: ürün, metal ve ceket suyu 25 °C; girişe 110 °C su gelir (`sourceMode=1`). Gücü sınırlı kaynak ayrıca seçilebilir. Kayıtlı kullanıcı senaryoları sessizce değiştirilmez.

## Başlatma

**`BASLAT.cmd`** dosyasını çalıştırın. Bağımlılıklar eksikse önce **`KURULUM.cmd`** kullanın. Uygulama yerel `.venv` ortamıyla açılır; Edge WebView2 çalışma zamanı gerekir. Ortam Python 3.10 ile hazırlanmıştır; sabitlenmiş bağımlılıklar için Python 3.10–3.12 kullanın.

PowerShell:

```powershell
. .\AKTIF_ET.ps1
.\.venv\Scripts\python.exe app.py
```

PowerShell betik çalıştırmayı engelliyorsa yalnız açık oturum için:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
. .\AKTIF_ET.ps1
```

## Kod nerede?

| Görev | Kaynak |
| --- | --- |
| Masaüstünde kullanılan ana hesap modeli | [web/calculations/Calculation.js](rotary_melter/web/calculations/Calculation.js) ve aynı klasördeki görev modülleri |
| Bağımsız SciPy ısıl çözümü ve hidrolik karşılaştırma | [Calculation.py](rotary_melter/Calculation.py) |
| JSON girdileri | [Configuration.py](rotary_melter/Configuration.py), `config/` |
| Masaüstü pencere ve Python–JavaScript köprüsü | [Interface.py](rotary_melter/Interface.py) |
| Yerel proje/senaryo kütüphanesi | [Workspace.py](rotary_melter/Workspace.py) |
| Parçacık temas ve rijit cisim dinamiği | `rotary_melter/dynamics/` |
| Formlar, görselleştirme, PDF raporu | `rotary_melter/web/interface/`, `visualization/`, `reporting/` |
| Arayüzsüz JSON/CSV/HTML raporu | [Reporting.py](rotary_melter/Reporting.py) |
| Testler ve derleme araçları | `tests/`, `tools/` |

Dosya ağacı ve eski/yeni adlar: [Kod yapısı](docs/KOD_YAPISI.md). Denklemler, değişkenler, literatür ve kaynak satırları: [Equation catalogue](docs/CALCULATION_EQUATIONS.md). VS Code'da **Ctrl+Shift+V** ile matematik önizlemesini açabilirsiniz; Markdown Preview Enhanced önerisi ve KaTeX ayarları hazırdır.

## Kurulum ve arayüzsüz hesap

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m tools.SetupNode
.\.venv\Scripts\python.exe app.py --build
.\.venv\Scripts\python.exe app.py --run --config config/default_inputs.json --output outputs/ornek_kosu
```

Hesap motorunun komut satırından çalıştırılması ve JavaScript testleri Node.js kullanır. Bu bilgisayarda checksum doğrulaması yapılmış Node.js 24 LTS `.tools/node/` içine kurulmuştur; yeni kurulumda `SetupNode` bunu hazırlar. Masaüstü hesapları WebView2 içinde çalışır ve Node gerektirmez. `.venv`, `.tools` ve `outputs` Git'e eklenmez.

`--run`, arayüzle aynı V11 hesap motorunu kullanır; `result.json`, `history.csv`, `summary.json` ve `report.html` üretir. Masaüstündeki mevcut PDF, CSV, JSON, erime oynatımı ve parçacık hareketi özellikleri korunmuştur.

## Doğrulama

```powershell
.\.venv\Scripts\python.exe -m tools.RunChecks
.\.venv\Scripts\python.exe -m tools.RunChecks --desktop
.\.venv\Scripts\python.exe app.py --self-test outputs/desktop_check.json
```

Kontroller çıktıları ayrı `outputs/checks/` klasörlerine yazar. Gerçek kullanıcı kütüphanesini değiştirmez. Aktarım kontrolleri ve eski testlerin durumu: [Doğrulama notları](docs/MIGRATION_VERIFICATION.md).

## EXE üretme

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m tools.BuildDesktop
```

Yeni EXE: `releases/current/Rotary_Melter_V11.exe`. Kaynaktan çalıştırma her açılışta HTML arayüzünü günceller; paketli EXE derleme sırasında gömülen arayüzü kullanır. EXE'deki komut satırı hesap modu ayrıca Node kurulumu ister; normal masaüstü modu istemez.

## Sürümler ve kayıtlar

- `releases/original/`: V1–V11 orijinal dağıtımları ve ZIP'leri; silinmedi, Git dışında tutulur.
- `docs/history/`: Önceki kullanım, araştırma ve doğrulama belgeleri.
- `validation/original/`: Kaynak paketinin değişmeden korunan doğrulama kayıtları.
- `reference/`: Bağımsız çözücü karşılaştırması ve hesaplanmış örnek hareket kaydı.
- `docs/V11_SOURCE_PROVENANCE.json`: V11 dağıtımı ile kaynak arşivinin eşleşme ve dosya checksum bilgileri.

Mevcut kullanıcı kütüphanesi `%LOCALAPPDATA%\RotaryMelter\workspace.json` konumunda kalır. Otomatik testler kendilerine ayrılmış proje içi dosyaları kullanır.

## Modelin kapsamı

Bu bir ısıl ağ, granül radyal iletimi ve yaklaşık temas/dinamik modelidir. CFD veya deneysel olarak doğrulanmış eritme ekipmanı tasarımı değildir. Bağımsız BDF/Radau çözümleri ve korunum kontrolleri sayısal doğrulamadır; malzeme, temas, film katsayıları ve kaynak/rezervuar sınır koşulları gerçek ekipmana göre ayrıca belirlenmelidir. Önceki Heat_Transfer projesinin fiziksel modeli bu projeye kopyalanmamıştır; o projede kurulan geliştirme düzeni bu uygulamaya uyarlanmıştır.
