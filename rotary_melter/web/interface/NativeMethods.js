/* Actual native methods for the UI/PDF. Reference explanations remain available
   when a retained V11 result is explicitly used for comparison. */
(function () {
  const referenceMethods = methodSections;
  methodSections = function (r, lang) {
    if (!r?.engine?.name?.includes("C++")) return referenceMethods(r, lang);
    const en = lang === "en",
      t = (tr, english) => (en ? english : tr);
    const rows = [
      [
        "Geometri ve yük",
        "Geometry and charge",
        "Kapasite ve aktarım alanı silindir ile küresel kapaklardan hesaplanır. Dolum modunda gerçek kütle, dolum ve paketleme oranından türetilir.",
        "Cylinder and spherical-cap geometry define capacity and heat-transfer area. Fill mode derives actual mass from fill and packing fractions.",
        "V = πR²L + n_h πh(3R²+h²)/6\nA = 2πRL + n_h π(R²+h²)\nm = V × fill × packing × ρ_s",
      ],
      [
        "Eğimli dolum",
        "Inclined fill",
        "Yerçekimine göre yatay serbest yüzey, kesit integrali ve Boost.Math TOMS748 kök çözümüyle bulunur. Dikey limit ayrı ele alınır.",
        "Slice quadrature and Boost.Math TOMS748 find the gravity-oriented free surface. The vertical limit is handled separately.",
        "u = (H − z sinθ)/(r cosθ)\nF_V = 1/2 + [asin(u)+u√(1−u²)]/π\nF_A = 1/2 + asin(u)/π",
      ],
      [
        "Bölgesel ağ ve ıslanma",
        "Regional grid and wetting",
        "Alan ağırlıkları metal/su kapasitelerini dağıtır. Dokuz faz tablosu arasındaki interpolasyon, erimeyle değişen temas alanını verir.",
        "Area weights distribute metal/water capacities. Interpolation between nine phase tables supplies changing wet contact area.",
        "w_a = Σ(slice area in zone a) / total area\nA_cell = A w_a/P\nf_wet = interpolate(table[f_liquid])",
      ],
      [
        "Entalpi ve erime",
        "Enthalpy and melting",
        "Her radyal hücre joule cinsinden enerji taşır. Gizli ısı solidus–liquidus aralığındaki görünür ısı kapasitesine eklenir.",
        "Every radial cell stores energy in joules. Apparent heat capacity distributes latent heat across the solidus–liquidus interval.",
        "c_m = (c_s+c_l)/2 + latent/(T_l−T_s)\nh(T) = piecewise sensible + melting enthalpy\nE_j = m_j h(T_j); f_l = clip((T−T_s)/(T_l−T_s),0,1)",
      ],
      [
        "IAPWS su özellikleri",
        "IAPWS water properties",
        "Doyma basıncını IF97 hesaplar. İsteğe bağlı IF97 su özellikleri, belirtilen referans sıcaklıkta bir kez değerlendirilir ve enerji çözümünde sabit tutulur.",
        "IF97 evaluates saturation pressure. Optional IF97 water properties are evaluated once at the recorded reference temperature and remain constant in the energy solve.",
        "T_K = T_C + 273.15; p_Pa = 100000 p_bar(abs)\nT_ref = (T_water,initial + T_in,set)/2\nρ, cp, μ, p_sat ← CoolProp/IF97",
      ],
      [
        "Film ve metal dirençleri",
        "Film and metal resistances",
        "Newton taşınımı ile yarım cidar iletimi seri bağlanır; aktarım akısı iki düğüme eşit ve zıt işaretle yazılır.",
        "Newton convection and half-wall conduction resistances act in series; each transfer appears with opposite signs in its two nodes.",
        "G = A / (1/h + δ/(2k))\nQ = G (T_1−T_2)",
      ],
      [
        "Devir ve yatak kapanışları",
        "RPM and bed closures",
        "Devir-film katsayısı, temas topolojisi ve yatak yolu kalibre edilmesi gereken varsayımlardır. Seri/paralel iletkenlik sınırları arasında seçilen topoloji kullanılır.",
        "RPM-film dependence, contact topology and bed path are calibratable assumptions. The selected topology interpolates between series/parallel conductivity bounds.",
        "h_p = min(h_limit, h_static+(h_ref−h_static)(RPM/RPM_ref)^b)\nk_bed = k_series + topology (k_parallel−k_series)\nG_bed = k_bed V_bed^(2/3)/max(d_particle,path_factor D)",
      ],
      [
        "Radyal granül iletimi",
        "Radial granule conduction",
        "Duvara yakın ve iç yatak popülasyonlarının her birinde K küresel kabuk çözülür. Komşu kabuklarda harmonik iletkenlik kullanılır.",
        "Each near-wall/core population has K spherical shells. Adjacent shells use harmonic conductivity.",
        "w_j = ((j+1)³−j³)/K³; m_j = m_population w_j\nG_(j+1/2) = N_particle 4πr_face² k_harmonic/Δr\ndE_j/dt += G_(j+1/2)(T_(j+1)−T_j)",
      ],
      [
        "Yüzey sıcaklıkları ve yenilenme",
        "Surface temperatures and renewal",
        "Kütlesiz iki yüzeyin enerji dengesi Eigen LDLT ile çözülür. Yatak yenilenmesi sıcaklık yerine özgül entalpi taşır; aynı aktarım iki kez sayılmaz.",
        "Eigen LDLT solves the massless two-surface energy balance. Bed renewal transports specific enthalpy rather than temperature; the transfer is not counted twice.",
        "[G_n+F+B, −B; −B, G_c+B] [T_ns,T_cs]ᵀ = RHS\nṁ_exchange = m × renewal_per_rev × RPM/60\nQ_exchange,j = ṁ_exchange w_j (h_near,j−h_core,j)",
      ],
      [
        "Su devresi ve kaynak",
        "Water circuit and source",
        "Ceket halkaları seri karışmış su düğümleridir. Sabit giriş modunda gereken güç hesaplanır; sınırlı kaynak modunda verimli boiler gücüyle kesilir. İlk suyun depolaması korunur.",
        "Jacket rings are serial mixed-water nodes. Fixed inlet calculates required power; limited source caps it by delivered heater power. Initial water storage is retained.",
        "F = ρ V̇ cp; Q_req = max(0,F(T_set−T_return))\nQ_source = Q_req OR min(Q_req,ηP_boiler)\nT_in = T_return + Q_source/F\nCw dTw/dt = F(T_up−Tw) − ΣQ_water→metal − Q_extra",
      ],
      [
        "Metal iletimi ve dönme",
        "Metal conduction and rotation",
        "Eksenel/çevresel iletim ve birinci mertebe yukarı-akım dönme terimi birlikte çözülür. Yüzey hücreleri ortak belleğe yazmadığından büyük ağda OpenMP uygulanabilir.",
        "Axial/circumferential conduction and first-order upwind rotation are solved together. Surface cells write separate slots, allowing OpenMP on large meshes.",
        "C_k dT_k/dt = Q_water − Q_product/loss + ΣG_kl(T_l−T_k)\n                     + C_k(RPM P/60)(T_upwind−T_k)",
      ],
      [
        "Çevre ve izolasyon",
        "Ambient and insulation",
        "Her hücrede taşınım ve Kelvin sıcaklıklarıyla ışınım hesaplanır. İzolasyon varsa yüzey sıcaklığı Boost.Math ile iletim–çevre dengesinden bulunur.",
        "Each cell includes convection and radiation in kelvin. With insulation, Boost.Math solves the surface conduction/ambient balance.",
        "Q_conv = h_ext A(T_surface−T_ambient)\nQ_rad = εσA[(T_surface+273.15)^4−(T_ambient+273.15)^4]\n(k_ins A/δ_ins)(T_metal−T_surface) = Q_conv+Q_rad",
      ],
      [
        "Kütüphane ile zaman ilerletme",
        "Library time integration",
        "Seçili Boost.Odeint yöntemi: " +
          r.engine.integrator +
          ". Kaynak/kayıp integralleri aynı RK aşamalarında ilerler. Adaptif yöntem de açık kararlılık sınırını aşmaz.",
        "Selected Boost.Odeint method: " +
          r.engine.integrator +
          ". Source/loss integrals advance in the same RK stages. The adaptive method also respects the explicit stability cap.",
        r.engine.integrator === "midpoint"
          ? "k1 = RHS(t_n,y_n)\nk2 = RHS(t_n+Δt/2,y_n+Δt k1/2)\ny_(n+1) = y_n + Δt k2"
          : r.engine.integrator === "rk4"
            ? "Boost.Odeint runge_kutta4\ny_(n+1) = y_n + Δt(k1+2k2+2k3+k4)/6"
            : "Boost.Odeint controlled runge_kutta_dopri5\nembedded 5(4) error estimate; rejected steps do not advance time",
      ],
      [
        "Enerji dengesi ve durma",
        "Energy closure and stopping",
        "Hedef, iki popülasyondaki tüm radyal hücreler hedef entalpisine erişince sağlanır. Raporlanan zaman kabul edilen bir adımın sonudur; küçük enerji artığı deneysel doğruluk değildir.",
        "Target requires every radial cell in both populations to reach target enthalpy. Reported time is an accepted step endpoint; a small energy residual does not establish experimental accuracy.",
        "R_E = E_source − E_loss − ΔE_product − ΔE_metal − ΔE_water\nr_E = |R_E|/max(1 J,|E_source|,Σ|energy terms|)\nstop: E_j ≥ m_j h(T_target) for ALL product shells",
      ],
      [
        "Hidrolik kayıplar",
        "Hydraulic losses",
        "Boru ve halka kesitleri ayrı çözülür. Darcy faktörü türbülanslı rejimde Boost.Math ile Colebrook denkleminden bulunur; gerçek joint verileri ayrıca gereklidir.",
        "Pipe and annular segments are evaluated separately. Boost.Math solves the Colebrook Darcy factor for turbulent flow; actual joint data remain necessary.",
        "Re = ρvDh/μ\n1/√f = −2log10(roughness/(3.7Dh)+2.51/(Re√f))\nΔp = Σ(f L/Dh+K)ρv²/2 + component losses\nP_pump = V̇ Δp/η_pump",
      ],
      [
        "Yakınsama ve duyarlılık",
        "Convergence and sensitivity",
        "Üç yüzey ağı ortak zaman adımıyla karşılaştırılır; zaman ve radyal inceltme ayrıdır. Bağımsız koşular BS_thread_pool ile paraleldir. Geçersiz veya hedefe ulaşmayan koşuya süre hassasiyeti verilmez.",
        "Three surface grids share a common step; time and radial refinements are separate. BS_thread_pool runs independent cases in parallel. Invalid/unreached cases do not receive target-time sensitivities.",
        "p = ln(|(F_coarse−F_base)/(F_base−F_fine)|)/ln2\nGCI_fine = 1.25 |(F_base−F_fine)/F_fine|/(2^p−1)\nS_F,p = (F_high−F_low)/(p_high−p_low) × p_base/F_base",
      ],
      [
        "Gerçek boyutlu granüller",
        "Physical-size granules",
        "FCC adayları duvar açıklığına göre elenir, en düşük yerçekimi yüksekliğinden seçilir. Tekrarlanabilir bağ sırası kullanılır; parçacık sayısı görsel amaçla azaltılmaz.",
        "FCC candidates are filtered by wall clearance and selected from the lowest gravitational height. Explicit tie order is reproducible; particle count is not reduced for display.",
        "N = round(m/(ρ_s 4πr0³/3))\nr_solid = r0(1−f_liquid)^(1/3)\na_FCC = 2√2 r × 1.025; nearest-wall clearance > 1.005r",
      ],
      [
        "Rijit granül teması",
        "Rigid granule contacts",
        "Eigen vektörleriyle sıralı impuls, birikimli Coulomb sürtünmesi ve küre dönmesi hesaplanır. Ortak granülleri etkileyen temasların sırası korunur. Bu bir CFD veya ölçülmüş wax malzeme modeli değildir.",
        "Sequential impulses, accumulated Coulomb friction and sphere spin use Eigen vectors. Contacts sharing particles retain their update order. This is not CFD or a measured wax constitutive model.",
        "λ_n ← max(0, λ_n+(v_target−v_normal)/inverse_effective_mass)\n|λ_t| ≤ μλ_n; I_sphere = 2mr²/5\nposition correction is split from kinetic velocity",
      ],
      [
        "Elastik temas alternatifi",
        "Compliant contact alternative",
        "Sönümlü doğrusal yay ve teğetsel yer değiştirme geçmişi kullanılır. Zaman adımı sertliğe göre sınırlanır; girilen normalleştirilmiş katsayı doğrudan malzeme modülü değildir.",
        "A damped linear spring and tangential displacement history provide the alternative. Stiffness limits the step; the entered normalized coefficient is not directly a material modulus.",
        "ζ = −ln(e)/√(π²+ln²(e)); γ = 2ζ√kn\nFn = max(0,kn overlap − γ_pair vn)\nFt = clip_Coulomb(−kt ξ − γ_pair vt)",
      ],
      [
        "Boşluk sıvı seviyesi ve sınırlar",
        "Interstitial liquid level and limits",
        "Sıvının kap içindeki hacmi, granüllerin kapladığı küresel kapaklar çıkarılarak Boost.Math ile eşlenir. Yüzeyin dinamik akışı çözülmez; ısıl–mekanik aktarım tek yönlüdür.",
        "Boost.Math matches liquid volume after subtracting sphere-cap occupancy. Dynamic free-surface flow is not solved; thermal-to-mechanical phase transfer is one way.",
        "V_void(H) = V_vessel,below(H) − Σπc_i²(r−c_i/3)\nV_void(H) = m f_liquid/ρ_l\nSource lines, literature and full derivation: docs/CPP_CALCULATION_EQUATIONS.md",
      ],
    ];
    return rows.map((row, i) => ({
      title: i + 1 + ". " + t(row[0], row[1]),
      text: t(row[2], row[3]),
      formula: row[4],
    }));
  };
  const previousRender = renderMethods;
  renderMethods = function () {
    previousRender();
    const r = state.result;
    if (!r?.engine?.name?.includes("C++")) return;
    $("methodIntro").textContent = tx(
      "Bu koşuda çalışan C++ yöntemleri aşağıdadır. Ayrıntılı türetme, literatür ve kaynak satırları Markdown formül raporundadır.",
      "The C++ methods actually used in this run are shown below. The Markdown catalogue includes derivations, literature and source-line references.",
    );
    $("executedCode").textContent = $("cppSource").value;
    $("codeTitle").textContent =
      tx(
        "C++ hesap kaynakları · derleme parmak izi: ",
        "C++ calculation sources · build fingerprint: ",
      ) + r.engine.sourceFingerprint;
    const header = $("audit").querySelector("th");
    if (header) header.textContent = "RHS evaluation time (s)";
  };
})();
