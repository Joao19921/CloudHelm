const state = {
  token: null,
  userEmail: null,
  catalog: [],
};

const $ = (id) => document.getElementById(id);

const statusEl = $("status");
const authStateEl = $("auth-state");
const architectureEl = $("architecture");
const costsEl = $("costs");
const terraformEl = $("terraform-modules");
const rankingEl = $("ranking");
const catalogGridEl = $("catalog-grid");
const catalogMetaEl = $("catalog-meta");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.className = isError ? "mt-3 text-xs text-rose-300" : "mt-3 text-xs text-emerald-300";
}

function authHeaders() {
  if (!state.token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${state.token}`,
  };
}

function renderArchitecture(analysis) {
  const modules = analysis.architecture.modules || [];
  architectureEl.innerHTML = modules
    .map(
      (m) => `
      <div class="rounded-xl border border-white/10 bg-slate-950/50 p-3">
        <p class="text-sm font-semibold text-brand-200">${m.name}</p>
        <p class="text-xs text-slate-300 mt-1">${m.role}</p>
        <p class="text-[11px] text-slate-400 mt-2"><span class="text-slate-200">Calls:</span> ${m.calls}</p>
        <p class="text-[11px] text-slate-400"><span class="text-slate-200">Returns:</span> ${m.returns}</p>
      </div>
    `
    )
    .join("");
}

function renderCosts(analysis) {
  const rows = analysis.costs.monthly_estimate;
  const selected = analysis.provider;
  costsEl.innerHTML = `
    <div class="rounded-xl border border-white/10 bg-slate-950/50 p-3">
      <p class="text-sm font-semibold mb-2">Comparativo mensal (USD)</p>
      ${Object.entries(rows)
        .map(([provider, values]) => {
          const isSelected = provider === selected;
          const cls = isSelected ? "text-brand-200 font-semibold" : "text-slate-300";
          return `<p class="text-xs ${cls}">${provider.toUpperCase()}: ${values.min} - ${values.max}</p>`;
        })
        .join("")}
    </div>
  `;
}

function renderTerraform(analysis) {
  const modules = analysis.terraform.modules || {};
  terraformEl.innerHTML = Object.entries(modules)
    .map(
      ([name, script]) => `
      <details class="rounded-xl border border-white/10 bg-slate-950/50 p-3">
        <summary class="cursor-pointer text-sm font-semibold text-brand-200">${name}</summary>
        <pre class="mt-3 overflow-x-auto text-[11px] leading-5 text-slate-200">${script}</pre>
      </details>
    `
    )
    .join("");
}

function renderRanking(analysis) {
  const ranking = analysis.ranking || {};
  const items = ranking.items || [];
  if (!items.length) {
    rankingEl.innerHTML = "";
    return;
  }
  rankingEl.innerHTML = `
    <div class="rounded-xl border border-brand-400/30 bg-brand-950/20 p-3">
      <p class="text-sm font-semibold text-brand-200">Ranking Inteligente de Provider</p>
      <p class="mt-1 text-[11px] text-slate-300">Recomendado: <span class="font-semibold text-emerald-300">${ranking.recommended_provider?.toUpperCase() || "-"}</span></p>
      <p class="text-[11px] text-slate-400">${ranking.method || ""}</p>
      <div class="mt-3 space-y-2">
        ${items
          .map(
            (item) => `
            <div class="rounded-lg border border-white/10 bg-slate-950/40 p-2">
              <p class="text-xs font-semibold ${item.provider === ranking.recommended_provider ? "text-emerald-300" : "text-slate-200"}">${item.provider.toUpperCase()} - score ${Number(item.score).toFixed(3)}</p>
              <p class="text-[11px] text-slate-400">Custo medio: USD ${Number(item.cost_mid_usd_month).toFixed(2)} | SLA: ${Number(item.sla_score).toFixed(2)} | Catalogo: ${Number(item.catalog_signal).toFixed(2)}</p>
            </div>
          `
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderCatalog(list) {
  if (!list.length) {
    catalogGridEl.innerHTML =
      '<div class="rounded-xl border border-white/10 bg-slate-950/50 p-4 text-xs text-slate-300">Nenhum item encontrado. Sincronize o catalogo primeiro.</div>';
    return;
  }
  catalogGridEl.innerHTML = list
    .map(
      (item) => `
      <div class="rounded-xl border border-white/10 bg-slate-950/60 p-4">
        <div class="flex items-start justify-between gap-3">
          <img src="${item.icon}" class="h-10 w-10 object-contain" onerror="this.src='/static/icons/generic.svg'" />
          <span class="rounded bg-white/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-brand-100">${item.provider}</span>
        </div>
        <p class="mt-3 text-sm font-semibold text-slate-100">${item.display_name}</p>
        <p class="text-[11px] text-slate-400">${item.service}${item.region ? ` - ${item.region}` : ""}</p>
        <p class="mt-3 text-lg font-bold text-brand-200">${item.currency} ${Number(item.price).toFixed(4)}</p>
        <p class="text-[11px] text-slate-400">por ${item.unit} - fonte: ${item.source}</p>
      </div>
    `
    )
    .join("");
}

function applyCatalogFilter() {
  const provider = $("catalog-provider-filter").value;
  const search = $("catalog-search").value.trim().toLowerCase();
  const filtered = state.catalog.filter((item) => {
    const providerMatch = provider === "all" || item.provider === provider;
    const searchMatch =
      !search ||
      item.display_name.toLowerCase().includes(search) ||
      item.service.toLowerCase().includes(search);
    return providerMatch && searchMatch;
  });
  renderCatalog(filtered);
  catalogMetaEl.textContent = `Itens exibidos: ${filtered.length} / ${state.catalog.length}`;
}

async function register() {
  const payload = {
    name: $("register-name").value.trim(),
    email: $("register-email").value.trim(),
    password: $("register-password").value.trim(),
  };
  if (!payload.name || !payload.email || !payload.password) {
    setStatus("Preencha nome, email e senha para registrar.", true);
    return;
  }
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    setStatus("Falha no registro. Verifique email e senha.", true);
    return;
  }
  setStatus("Usuario registrado com sucesso.");
}

async function login() {
  const payload = {
    email: $("register-email").value.trim(),
    password: $("register-password").value.trim(),
  };
  if (!payload.email || !payload.password) {
    setStatus("Informe email e senha para login.", true);
    return;
  }
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    setStatus("Credenciais invalidas.", true);
    return;
  }
  const data = await res.json();
  state.token = data.access_token;
  state.userEmail = payload.email;
  authStateEl.textContent = `Autenticado: ${state.userEmail}`;
  setStatus("Login concluido.");
}

async function loadCatalog() {
  const provider = $("catalog-provider-filter").value;
  const search = $("catalog-search").value.trim();
  const res = await fetch(`/api/catalog/items?provider=${provider}&search=${encodeURIComponent(search)}&limit=300`);
  if (!res.ok) {
    catalogMetaEl.textContent = "Falha ao carregar catalogo.";
    return;
  }
  state.catalog = await res.json();
  applyCatalogFilter();
}

async function syncCatalog() {
  if (!state.token) {
    setStatus("Faca login para sincronizar o catalogo.", true);
    return;
  }
  setStatus("Sincronizando catalogo cloud...");
  const res = await fetch("/api/catalog/sync", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      providers: ["aws", "gcp", "azure"],
      limit_per_provider: 25,
    }),
  });
  if (!res.ok) {
    setStatus("Falha na sincronizacao do catalogo.", true);
    return;
  }
  const data = await res.json();
  const syncedProviders = Object.entries(data.synced)
    .map(([provider, total]) => `${provider.toUpperCase()}: ${total}`)
    .join(" | ");
  setStatus(`Catalogo sincronizado. ${syncedProviders}`);
  await loadCatalog();
}

async function orchestrate() {
  if (!state.token) {
    setStatus("Faca login antes de orquestrar a demanda.", true);
    return;
  }

  const title = $("demand-title").value.trim();
  let rawInput = $("demand-input").value.trim();
  let inputType = "text";
  const provider = $("provider").value;
  const fileInput = $("demand-file");

  if (fileInput.files.length > 0 && !rawInput) {
    setStatus("Transcrevendo audio...");
    const form = new FormData();
    form.append("audio", fileInput.files[0]);
    const transcribeRes = await fetch("/api/demands/transcribe", {
      method: "POST",
      headers: state.token ? { Authorization: `Bearer ${state.token}` } : {},
      body: form,
    });
    if (!transcribeRes.ok) {
      setStatus("Falha na transcricao automatica. Preencha o texto manualmente.", true);
      return;
    }
    const transcriptData = await transcribeRes.json();
    rawInput = transcriptData.transcript;
    inputType = "audio_transcript";
    $("demand-input").value = rawInput;
  } else if (fileInput.files.length > 0) {
    inputType = "audio_transcript";
  }

  if (!title || rawInput.length < 10) {
    setStatus("Informe titulo e uma descricao valida da demanda.", true);
    return;
  }

  setStatus("Criando demanda...");
  const createRes = await fetch("/api/demands", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      title,
      raw_input: rawInput,
      input_type: inputType,
    }),
  });
  if (!createRes.ok) {
    setStatus("Falha ao criar demanda.", true);
    return;
  }
  const demand = await createRes.json();

  setStatus("Executando orquestracao...");
  const orchestrationRes = await fetch(`/api/demands/${demand.id}/orchestrate`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ provider }),
  });
  if (!orchestrationRes.ok) {
    setStatus("Falha na orquestracao.", true);
    return;
  }
  const analysis = await orchestrationRes.json();

  renderArchitecture(analysis);
  renderCosts(analysis);
  renderTerraform(analysis);
  renderRanking(analysis);
  setStatus("Orquestracao concluida com sucesso.");
}

async function transcribeAudio() {
  if (!state.token) {
    setStatus("Faca login para transcrever audio.", true);
    return;
  }
  const fileInput = $("demand-file");
  if (!fileInput.files.length) {
    setStatus("Selecione um arquivo de audio antes de transcrever.", true);
    return;
  }
  setStatus("Transcrevendo audio...");
  const form = new FormData();
  form.append("audio", fileInput.files[0]);
  const res = await fetch("/api/demands/transcribe", {
    method: "POST",
    headers: { Authorization: `Bearer ${state.token}` },
    body: form,
  });
  if (!res.ok) {
    setStatus("Falha na transcricao automatica.", true);
    return;
  }
  const data = await res.json();
  $("demand-input").value = data.transcript;
  setStatus(`Transcricao concluida via ${data.source} (${data.model}).`);
}

$("register-btn").addEventListener("click", register);
$("login-btn").addEventListener("click", login);
$("orchestrate-btn").addEventListener("click", orchestrate);
$("transcribe-btn").addEventListener("click", transcribeAudio);
$("catalog-sync-btn").addEventListener("click", syncCatalog);
$("catalog-provider-filter").addEventListener("change", loadCatalog);
$("catalog-search").addEventListener("input", applyCatalogFilter);

loadCatalog();
