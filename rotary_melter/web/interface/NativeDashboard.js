/* C++ jobs, analysis and provenance. All DOM text from files/results is escaped. */
(function () {
  "use strict";
  const el = (id) => document.getElementById(id),
    api = () => window.pywebview?.api;
  const text = (tr, en) => (state.lang === "en" ? en : tr);
  const escape = (value) =>
    String(value ?? "—").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const number = (value, digits = 3) =>
    typeof value === "number" && Number.isFinite(value)
      ? value.toLocaleString(state.lang === "en" ? "en-US" : "tr-TR", {
          maximumFractionDigits: digits,
        })
      : "—";
  let active = null,
    generation = 0,
    engine = null,
    lastAnalysis = null,
    lastLang = null,
    booted = false,
    sequence = -1;
  const root = document.createElement("section");
  root.className = "panel nativeWorkbench";
  root.id = "nativeWorkbench";
  root.innerHTML = `<div class="nativeHeading"><div><div class="nativeEyebrow">C++ · BOOST · EIGEN · IAPWS-IF97</div><h2 id="nativeTitle"></h2></div><span id="nativeBackend" class="nativeStatus" role="status"></span></div>
<div class="nativeBody"><div class="nativeControls"><label><span id="nativeMethodLabel"></span><select id="nativeMethod" aria-label="Integrator"><option value="midpoint">RK2 · midpoint</option><option value="rk4">Runge–Kutta 4</option><option value="dopri5">Dormand–Prince 5(4)</option></select></label><label><span id="nativeThreadsLabel"></span><select id="nativeThreads" aria-label="Threads"><option>1</option><option>2</option><option selected>4</option><option>8</option></select></label><label><span id="nativeWaterLabel"></span><select id="nativeWater" aria-label="Water properties"><option value="constant"></option><option value="if97_reference">IAPWS-IF97 · reference</option></select></label><button id="nativeSensitivity"></button><button id="nativeConvergence"></button><button id="nativeMarkdown"></button></div>
<div class="nativeKpis" id="nativeKpis"></div><div id="nativeMessage" class="nativeMessage" role="status" aria-live="polite"></div>
<details class="nativeDetails"><summary id="nativeTraceTitle"></summary><dl id="nativeTrace" class="nativeTrace"></dl><p class="nativeNote" id="nativeTraceNote"></p><div class="toolbar"><button id="nativeRefreshHistory"></button></div><div id="nativeHistory" class="nativeHistory"></div></details>
<details class="nativeDetails nativeAnalysis" id="nativeAnalysisDetails" hidden><summary id="nativeAnalysisTitle"></summary><div id="nativeAnalysis" class="tablewrap"></div></details></div>`;
  el("quickOverview").before(root);
  let gpuInfo=null;
  const gpuButton=document.createElement('button');gpuButton.id='nativeGpu';
  el('nativeMarkdown').after(gpuButton);
  gpuButton.onclick=async()=>{
    const runId=state.result?.traceability?.runId;
    if(!runId)return;
    gpuButton.disabled=true;message(text('NVIDIA alan denetimi çalışıyor…','Running NVIDIA field audit…'));
    try{
      const response=await api().native_gpu_audit(runId);
      if(!response.ok)throw Error(response.error);
      const r=response.result;
      message(`${r.device.name} · ${number(r.evaluations,0)} ${text('alan hesabı','field evaluations')} · CPU/GPU Δ ${r.maxCpuGpuDifferenceW.toExponential(2)} W · ${response.directory}`);
    }catch(error){message(error.message,true);}
    finally{refresh();}
  };
  // Put the model in view before the detailed motion controls. Keep the four
  // routine actions visible and every existing control/ID available below it.
  const motionControls = el("motionControls");
  const motionQuick = document.createElement("div");
  motionQuick.className = "toolbar nativeMotionQuick";
  motionControls.before(motionQuick);
  for (const id of [
    "motionPlay",
    "motionPauseBtn",
    "motionStop",
    "motionReset",
  ])
    motionQuick.append(el(id));
  const motionDetails = document.createElement("details");
  motionDetails.className = "nativeMotionDetails";
  const motionSummary = document.createElement("summary");
  motionSummary.id = "nativeMotionSettingsLabel";
  motionDetails.append(motionSummary);
  el("vessel").after(motionDetails);
  motionDetails.append(motionControls);

  function labels() {
    const labels = {
      nativeTitle: ["Hesap ve analiz merkezi", "Calculation and analysis"],
      nativeGpu:['NVIDIA alan denetimi','NVIDIA field audit'],
      nativeMotionSettingsLabel: [
        "Hareket ayarları ve kayıt",
        "Motion settings and recording",
      ],
      nativeMethodLabel: ["Çözüm yöntemi", "Integrator"],
      nativeThreadsLabel: ["Paralel iş parçacığı", "Parallel threads"],
      nativeWaterLabel: ["Su özellikleri", "Water properties"],
      nativeSensitivity: ["Duyarlılık ±%10", "Sensitivity ±10%"],
      nativeConvergence: ["Ağ / zaman kontrolü", "Grid / time check"],
      nativeMarkdown: ["Markdown raporu", "Markdown report"],
      nativeTraceTitle: [
        "İzlenebilirlik ve önceki çalıştırmalar",
        "Traceability and previous runs",
      ],
      nativeRefreshHistory: ["Geçmişi yenile", "Refresh history"],
      nativeAnalysisTitle: ["Son analiz tablosu", "Latest analysis table"],
      nativeTraceNote: [
        "Değiştirilen girdiler yeni hesap gerektirir. IF97 seçeneği, başlangıç ve giriş sıcaklıklarının ortalamasında sabit su özellikleri kullanır.",
        "Changed inputs require a new solve. IF97 uses constant water properties evaluated at the mean initial/inlet temperature.",
      ],
    };
    for (const [id, pair] of Object.entries(labels))
      el(id).textContent = text(...pair);
    el("nativeWater").options[0].textContent = text(
      "Girilen sabitler · V11",
      "Input constants · V11",
    );
    lastLang = state.lang;
  }
  function message(value, error = false) {
    el("nativeMessage").textContent = value;
    el("nativeMessage").style.color = error ? "#9c3d31" : "";
  }
  function options() {
    return {
      integrator: el("nativeMethod").value,
      threads: Number(el("nativeThreads").value),
      parallelKernel: true,
      waterModel: el("nativeWater").value,
    };
  }
  function refresh() {
    if (lastLang !== state.lang) {
      labels();
      if (lastAnalysis) renderAnalysis(lastAnalysis);
    }
    const r = state.result,
      valid = !!r && !state.dirty && r.engine?.name?.includes("C++");
    el("nativeKpis").classList.toggle("nativeStale", !valid);
    const kpis = [
      [
        text("Hedef süresi", "Time to target"),
        valid && r.targetReached ? number(r.seconds / 3600) : "—",
        valid && !r.targetReached
          ? text(
              "Süre sınırında hedefe ulaşılmadı",
              "Target not reached within limit",
            )
          : "h",
      ],
      [
        text("Giriş enerjisi", "Input energy"),
        valid ? number(r.energyInKWh) : "—",
        "kWh",
      ],
      [
        text("Erimiş kütle oranı", "Liquid mass fraction"),
        valid ? number(r.last.liquidFraction * 100, 2) : "—",
        "%",
      ],
      [
        text("Bağıl enerji artığı", "Relative energy residual"),
        valid ? r.balanceRelative.toExponential(2) : "—",
        valid
          ? text("Sayısal korunum kontrolü", "Numerical conservation check")
          : text("Yeni hesap gerekiyor", "Recalculate inputs"),
      ],
    ];
    el("nativeKpis").innerHTML = kpis
      .map(
        ([label, value, unit]) =>
          `<div class="nativeKpi"><small>${escape(label)}</small><b>${escape(value)}</b><em>${escape(unit)}</em></div>`,
      )
      .join("");
    const trace = r?.traceability || {},
      e = r?.engine || {};
    el("nativeTrace").innerHTML = Object.entries({
      [text("Çalıştırma", "Run")]: trace.runId,
      [text("Yöntem", "Method")]: e.integrator,
      [text("Çekirdek süresi", "Engine wall time")]:
        e.wallSeconds == null ? "—" : number(e.wallSeconds) + " s",
      "Input SHA-256": trace.inputSha256,
      "C++ DLL SHA-256": trace.nativeLibrarySha256,
      "C++ source SHA-256": e.sourceFingerprint,
      [text("Kütüphaneler", "Libraries")]: e.libraries
        ? JSON.stringify(e.libraries)
        : "—",
    })
      .map(([key, value]) => `<dt>${escape(key)}</dt><dd>${escape(value)}</dd>`)
      .join("");
    const busy = !!active;
    gpuButton.disabled=busy||!valid||!gpuInfo?.available;
    for (const id of ["nativeMethod", "nativeThreads", "nativeWater"])
      el(id).disabled = busy;
    for (const id of ["nativeSensitivity", "nativeConvergence"])
      el(id).disabled = busy || !engine?.available;
    el("nativeMarkdown").disabled = !valid;
    if (engine) {
      el("nativeBackend").textContent = engine.available
        ? busy
          ? text("C++ hesaplıyor", "C++ calculating")
          : "C++ · " + engine.version
        : text("C++ kullanılamıyor", "C++ unavailable");
      el("nativeBackend").classList.toggle("error", !engine.available);
    }
  }
  function cancel() {
    generation++;
    if (active?.id) api()?.native_cancel(active.id);
    active = null;
  }
  function busyUi(task) {
    state.task = task;
    el("progressWrap").hidden = false;
    el("stopBtn").hidden = false;
    el("runBtn").disabled = true;
    for (const id of ["verifyBtn", "rpmBtn", "sizingBtn"])
      el(id).disabled = true;
    el("progressBar").value = 0;
    el("errors").textContent = "";
    refresh();
  }
  function convergenceAdapter(result) {
    const mapped = {
      commonDt: result.commonTimeStepSeconds,
      gridIndex: result.targetGci || {
        available: false,
        reason: "target_not_reached",
      },
      timeDifference:
        result.timeDifferencePercent == null
          ? null
          : result.timeDifferencePercent / 100,
      radialDifference:
        result.radialDifferencePercent == null
          ? null
          : result.radialDifferencePercent / 100,
    };
    for (const row of result.cases) {
      if (!row.ok) throw Error(row.error);
      const s = row.summary;
      const key =
        { half_dt: "halfTimeStep", radial_fine: "radialFine" }[row.name] ||
        row.name;
      mapped[key] = {
        axial: s.c.axialZones,
        angular: s.c.angularZones,
        radial: s.c.radialZones,
        dt: s.dt,
        targetHours: s.targetHours,
        targetReached: s.targetReached,
        energyKWh: s.energyInKWh,
        waterOut: s.waterOutC,
        steps: s.steps,
        balanceRelative: s.balanceRelative,
      };
    }
    mapped.gridDifference =
      mapped.base.targetReached && mapped.fine.targetReached
        ? Math.abs(mapped.base.targetHours - mapped.fine.targetHours) /
          Math.max(1e-12, mapped.fine.targetHours)
        : null;
    return mapped;
  }
  function accept(task, result, inputs) {
    if (task === "verify")
      acceptResult(task, convergenceAdapter(result), inputs);
    else if (task === "rpm")
      acceptResult(
        task,
        result.cases.map((row) => {
          if (!row.ok) throw Error(row.error);
          const s = row.summary;
          return {
            rpm: s.c.rpm,
            h: s.hp,
            hours: s.targetHours,
            meltHours: s.meltingTime == null ? null : s.meltingTime / 3600,
            sourceKWhPerKg: s.targetReached ? s.energyInKWh / s.c.mass : null,
            lossKWh: s.lossKWh,
            Tin: s.waterInC,
            Tout: s.waterOutC,
          };
        }),
        inputs,
      );
    else if (task !== "sensitivity") {
      // Do not label an old input snapshot as current if the user edited during a solve.
      const edited = JSON.stringify(readInputs()) !== JSON.stringify(inputs);
      acceptResult(task, result, inputs);
      if (task === "solve" && edited) {
        state.dirty = true;
        updateDirty();
      }
    }
    if (task !== "solve") {
      lastAnalysis = result;
      renderAnalysis(result);
    }
    refresh();
  }
  async function start(task, inputs) {
    pause();
    stopTask();
    const ticket = ++generation;
    active = { ticket };
    busyUi(task);
    message(
      text("C++ çalıştırması başlatılıyor…", "Starting C++ calculation…"),
    );
    try {
      const job = await api().native_start(task, inputs, options());
      if (!job.ok) throw Error(job.error);
      if (ticket !== generation) {
        await api().native_cancel(job.id);
        return;
      }
      active = { id: job.id, ticket, task };
      sequence = -1;
      while (ticket === generation) {
        const update = await api().native_poll(job.id, sequence);
        if (ticket !== generation) return;
        if (!update.ok) throw Error(update.error);
        sequence = update.sequence;
        const p = update.progress;
        if (p) {
          const fraction = p.total
            ? p.completed / p.total
            : (p.coreTemperature - inputs.initial) /
              Math.max(1e-9, inputs.target - inputs.initial);
          el("progressBar").value = Number.isFinite(fraction)
            ? Math.min(99, Math.max(0, fraction * 100))
            : 0;
          el("progressText").textContent =
            p.stage === "analysis"
              ? `${p.completed} / ${p.total} · ${p.case}`
              : p.stage === "sizing"
                ? `${p.iteration} / ${p.total}`
                : `${number((p.seconds || 0) / 3600)} h · ${number(p.coreTemperature, 1)} °C`;
        }
        if (update.status !== "running") {
          active = null;
          stopTask();
          if (update.status === "error") throw Error(update.error);
          if (update.status === "cancelled") {
            message(text("Çalıştırma durduruldu.", "Calculation stopped."));
            return;
          }
          accept(task, update.result, inputs);
          message(
            text("Raporlar kaydedildi: ", "Reports saved: ") + update.directory,
          );
          await history();
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 160));
      }
    } catch (error) {
      if (ticket !== generation && active) return;
      active = null;
      stopTask();
      showError(error);
      message(error.message, true);
    } finally {
      refresh();
    }
  }
  function renderAnalysis(result) {
    el("nativeAnalysisDetails").hidden = false;
    el("nativeAnalysisDetails").open = true;
    if (!result.cases) {
      el("nativeAnalysis").textContent = JSON.stringify({
        possible: result.possible,
        kw: result.kw,
      });
      return;
    }
    const headings = [
      text("Koşu", "Case"),
      text("Hedef (h)", "Target (h)"),
      text("Ürün (°C)", "Product (°C)"),
      "kWh",
      text("Enerji artığı", "Energy residual"),
      text("Süre (s)", "Wall (s)"),
    ];
    el("nativeAnalysis").innerHTML =
      "<table><thead><tr>" +
      headings.map((h) => "<th>" + escape(h) + "</th>").join("") +
      "</tr></thead><tbody>" +
      result.cases
        .map((row) => {
          const s = row.summary || {};
          return (
            "<tr>" +
            [
              row.name,
              row.ok ? number(s.targetHours) : row.error,
              number(s.productC),
              number(s.energyInKWh),
              s.balanceRelative?.toExponential(2) || "—",
              number(s.wallSeconds),
            ]
              .map((v) => "<td>" + escape(v) + "</td>")
              .join("") +
            "</tr>"
          );
        })
        .join("") +
      '</tbody></table><p class="nativeNote">' +
      escape(
        text(
          "Bağımsız koşular paralel çözülür. Hedefe ulaşılmayan süreler karşılaştırılmaz.",
          "Independent cases run in parallel. Unreached target times are excluded from comparisons.",
        ),
      ) +
      "</p>";
    if (result.sensitivities) {
      const names = {
        rpm: text("Devir", "Rotational speed"),
        flow: text("Su debisi", "Water flow"),
        href: text("Film katsayısı", "Film coefficient"),
        exchangePerRev: text("Yatak yenilenmesi", "Bed renewal"),
      };
      const available = result.sensitivities.filter(
        (item) => item.available && Number.isFinite(item.timeElasticity),
      );
      const scale = Math.max(
        1e-12,
        ...available.map((item) => Math.abs(item.timeElasticity)),
      );
      const rows = result.sensitivities
        .map((item) => {
          const value = item.timeElasticity,
            width = item.available
              ? Math.min(50, (Math.abs(value) / scale) * 50)
              : 0;
          const left = value < 0 ? 50 - width : 50;
          return `<div class="nativeSensitivityRow"><span>${escape(names[item.parameter] || item.parameter)}</span><div class="nativeSensitivityTrack"><i style="left:${left}%;width:${width}%;background:${value < 0 ? "#008a88" : "#c88931"}"></i></div><b>${escape(item.available ? number(value, 3) : "—")}</b></div>`;
        })
        .join("");
      el("nativeAnalysis").insertAdjacentHTML(
        "beforeend",
        `<h3>${escape(text("Hedef süresinin yerel duyarlılığı", "Local sensitivity of target time"))}</h3><div class="nativeSensitivityBars">${rows}</div><p class="nativeNote">${escape(text("Boyutsuz elastisite: −0,8 değeri, parametrede +%1 değişim için hedef süresinde yaklaşık −%0,8 yerel değişim demektir. ±%10 koşuları üzerinden hesaplanır; belirsizlik aralığı değildir.", "Dimensionless elasticity: −0.8 means approximately −0.8% local target-time change for a +1% parameter change. Calculated from ±10% cases; not an uncertainty interval."))}</p>`,
      );
    }
  }
  async function history() {
    if (!api()?.native_history) return;
    const response = await api().native_history();
    if (!response.ok) return;
    el("nativeHistory").replaceChildren();
    for (const run of response.runs) {
      const button = document.createElement("button");
      button.textContent =
        run.type === "analysis"
          ? `${run.runId} · ${run.analysis} · ${run.cases} ${text("koşu", "cases")}`
          : `${run.runId} · ${run.targetReached ? number(run.seconds / 3600) + " h" : text("Hedef yok", "No target")} · ${number(run.energyInKWh)} kWh`;
      button.onclick = async () => {
        try {
          if (active)
            throw Error(
              text(
                "Önce çalışan hesabı durdurun.",
                "Stop the active calculation first.",
              ),
            );
          const response = await api().native_read_run(run.runId);
          if (!response.ok) throw Error(response.error);
          const result = response.result;
          const saved = result.traceability?.requestedConfiguration || result.c;
          const inputs = saved.inputs || saved;
          const settings = result.traceability?.options || {};
          if (settings.integrator)
            el("nativeMethod").value = settings.integrator;
          if (settings.waterModel)
            el("nativeWater").value = settings.waterModel;
          if (
            Number.isInteger(settings.threads) &&
            settings.threads >= 1 &&
            settings.threads <= 32
          ) {
            const select = el("nativeThreads");
            if (
              ![...select.options].some(
                (option) => option.value === String(settings.threads),
              )
            )
              select.add(
                new Option(String(settings.threads), String(settings.threads)),
              );
            select.value = String(settings.threads);
          }
          renderFields(inputs);
          if (result.analysis) {
            state.dirty = true;
            updateDirty();
            lastAnalysis = result;
            renderAnalysis(result);
          } else acceptResult("solve", result, inputs);
          refresh();
          message(text("Kayıt açıldı: ", "Opened run: ") + run.runId);
        } catch (error) {
          message(error.message, true);
        }
      };
      el("nativeHistory").append(button);
    }
    if (!response.runs.length)
      el("nativeHistory").textContent = text(
        "Henüz kayıtlı C++ çalıştırması yok.",
        "No saved C++ runs yet.",
      );
  }
  function markdown() {
    const r = state.result,
      t = r.traceability,
      e = r.engine;
    return `# Rotary Melter — ${t.runId}\n\n| Quantity | Result |\n| --- | ---: |\n| Target reached | ${r.targetReached} |\n| Physical time (s) | ${r.seconds} |\n| Input energy (kWh) | ${r.energyInKWh} |\n| Relative energy residual | ${r.balanceRelative} |\n\n## Calculation stages\n\n1. Geometry and inclined wet-area quadrature establish heat-transfer areas.\n2. Water/metal capacities and radial granule masses define conservative energy storage.\n3. The piecewise enthalpy law includes sensible heat and latent melting energy.\n4. Eigen solves the coupled surface balance; conduction, convection and radiation give heat rates.\n5. Boost.Odeint ${e.integrator} advances the coupled state.\n6. Energy closure and the target criterion are checked before export.\n\nDetailed formulas, source-line references, literature and library roles: docs/CPP_CALCULATION_EQUATIONS.md.\n\n## Traceability\n\n- Input SHA-256: ${t.inputSha256}\n- Native library SHA-256: ${t.nativeLibrarySha256}\n- Native source SHA-256: ${e.sourceFingerprint}\n- Libraries: ${JSON.stringify(e.libraries)}\n\nThese are numerical model predictions. Physical coefficients require experimental calibration.\n`;
  }
  async function bootstrap() {
    if (booted || !api()?.native_info) return;
    booted = true;
    stopTask();
    engine = await api().native_info();
    if (
      engine.available &&
      el("cppSource")?.dataset.fingerprint !== engine.sourceFingerprint
    ) {
      engine.available = false;
      engine.error = text(
        "C++ kaynakları derlenen motorla eşleşmiyor. .venv\\Scripts\\python.exe -m tools.BuildCpp komutuyla yeniden derleyin.",
        "C++ sources differ from the compiled engine. Rebuild with .venv\\Scripts\\python.exe -m tools.BuildCpp.",
      );
    }
    refresh();
    if (!engine.available) {
      message(engine.error, true);
      return;
    }
    document.body.classList.add("cppReady");
    if(api().native_gpu_info)api().native_gpu_info().then(info=>{gpuInfo=info;gpuButton.title=info.available?info.devices.map(device=>device.name).join(', '):info.error;refresh();});
    await history();
    start("solve", readInputs());
  }
  el("nativeSensitivity").onclick = () => start("sensitivity", readInputs());
  el("nativeConvergence").onclick = () => start("verify", readInputs());
  el("nativeRefreshHistory").onclick = () =>
    history().catch((error) => message(error.message, true));
  el("nativeMarkdown").onclick = () =>
    saveData(
      "Rotary_Melter_" + state.result.traceability.runId + ".md",
      markdown(),
      "text/markdown;charset=utf-8",
    );
  for (const id of ["nativeMethod", "nativeThreads", "nativeWater"])
    el(id).onchange = () => {
      state.dirty = true;
      updateDirty();
      refresh();
    };
  window.NativeDashboard = {
    available: () => !!api()?.native_start,
    start,
    cancel,
    refresh,
    history,
    options,
    get activeJob() {
      return active;
    },
    get analysis() {
      return lastAnalysis;
    },
  };
  window.addEventListener("pywebviewready", bootstrap);
  if (api()) bootstrap();
  labels();
  refresh();
  setInterval(refresh, 750);
})();
