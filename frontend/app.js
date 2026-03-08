const AUTH_TOKEN_KEY = "cloudhelm.auth.token";
const config = window.CLOUDHELM_CONFIG || {};
const API_BASE_URL = (config.API_BASE_URL || "").replace(/\/$/, "");

const state = {
  token: null,
  session: null,
  catalog: [],
};

const $ = (id) => document.getElementById(id);

const statusEl = $("status");
const authStateEl = $("auth-state");
const architectureEl = $("architecture");
const costsEl = $("costs");
const terraformEl = $("terraform-modules");
const rankingEl = $("ranking");
const aiBriefEl = $("ai-brief");
const catalogGridEl = $("catalog-grid");
const catalogMetaEl = $("catalog-meta");
const backofficeLinkEl = $("backoffice-link");
const logoutBtnEl = $("logout-btn");

function apiUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

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

function saveToken(token) {
  state.token = token;
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

function loadTokenFromUrlOrStorage() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  const pending = url.searchParams.get("pending");

  if (token) {
    saveToken(token);
    url.searchParams.delete("token");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  } else {
    saveToken(localStorage.getItem(AUTH_TOKEN_KEY));
  }

  if (pending) {
    setStatus("Acesso pendente. Aguarde aprovacao do administrador CloudHelm.", true);
    url.searchParams.delete("pending");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }
}

async function refreshSession() {
  if (!state.token) {
    state.session = null;
    authStateEl.textContent = "Nao autenticado";
    backofficeLinkEl.classList.add("hidden");
    logoutBtnEl.classList.add("hidden");
    return;
  }

  const res = await fetch(apiUrl("/api/auth/session"), { headers: authHeaders() });
  if (!res.ok) {
    saveToken(null);
    state.session = null;
    authStateEl.textContent = "Sessao expirada";
    backofficeLinkEl.classList.add("hidden");
    logoutBtnEl.classList.add("hidden");
    return;
  }
  state.session = await res.json();
  authStateEl.textContent = `Autenticado: ${state.session.email}`;
  logoutBtnEl.classList.remove("hidden");
  if (state.session.is_admin) {
    backofficeLinkEl.classList.remove("hidden");
  } else {
    backofficeLinkEl.classList.add("hidden");
  }
}

function renderArchitecture(analysis) {
  const modules = analysis.architecture.modules || [];
  architectureEl.innerHTML = modules
    .map(
      (m) => `
      <div class="rounded-xl border border-white/10 bg-slate-950/50 p-3">
        <p class="text-sm font-semibold text-brand-200">${m.name}</p>
        <p class="mt-1 text-xs text-slate-300">${m.role}</p>
        <p class="mt-2 text-[11px] text-slate-400"><span class="text-slate-200">Calls:</span> ${m.calls}</p>
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
      <p class="mb-2 text-sm font-semibold">Comparativo mensal (USD)</p>
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

function renderAIBrief(analysis) {
  const ai = analysis.ai || analysis.architecture?.ai || {};
  if (!ai || !ai.brief) {
    aiBriefEl.innerHTML = "";
    return;
  }
  const providerLabel = ai.provider === "none" ? "Padrao" : "Avancado";
  const badgeClass = ai.used_fallback ? "text-amber-300" : "text-emerald-300";
  aiBriefEl.innerHTML = `
    <div class="rounded-xl border border-white/10 bg-slate-950/55 p-3">
      <p class="text-sm font-semibold text-brand-200">Resumo de Arquitetura</p>
      <p class="mt-1 text-[11px] text-slate-300">
        Processamento: <span class="${badgeClass} font-semibold">${providerLabel}</span>
      </p>
      <p class="mt-2 whitespace-pre-wrap text-xs leading-5 text-slate-200">${ai.brief}</p>
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
          <img src="${item.icon}" class="h-10 w-10 object-contain" onerror="this.src='./assets/icons/generic.svg'" />
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

async function loadCatalog() {
  const provider = $("catalog-provider-filter").value;
  const search = $("catalog-search").value.trim();
  const res = await fetch(apiUrl(`/api/catalog/items?provider=${provider}&search=${encodeURIComponent(search)}&limit=300`));
  if (!res.ok) {
    catalogMetaEl.textContent = "Falha ao carregar catalogo.";
    return;
  }
  state.catalog = await res.json();
  applyCatalogFilter();
}

async function syncCatalog() {
  if (!state.token) {
    setStatus("Faca login com GitHub para sincronizar o catalogo.", true);
    return;
  }
  setStatus("Sincronizando catalogo cloud...");
  const res = await fetch(apiUrl("/api/catalog/sync"), {
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

async function loginWithGithub() {
  const res = await fetch(apiUrl("/api/auth/github/url"));
  if (!res.ok) {
    setStatus("GitHub OAuth nao configurado no servidor.", true);
    return;
  }
  const data = await res.json();
  window.location.href = data.auth_url;
}

function logout() {
  saveToken(null);
  state.session = null;
  backofficeLinkEl.classList.add("hidden");
  logoutBtnEl.classList.add("hidden");
  authStateEl.textContent = "Nao autenticado";
  setStatus("Sessao encerrada.");
}

async function orchestrate() {
  if (!state.token) {
    setStatus("Faca login com GitHub antes de orquestrar.", true);
    return;
  }

  const title = $("demand-title").value.trim();
  let rawInput = $("demand-input").value.trim();
  let inputType = "text";
  const provider = $("provider").value;
  const fileInput = $("demand-file");

  // Handle file upload if provided
  if (fileInput.files.length > 0) {
    setStatus("Processando arquivo e transcrevendo audio se necessario...");
    const file = fileInput.files[0];
    const isAudio = file.type.startsWith("audio/") || file.type === "video/mp4";
    
    if (isAudio) {
      // Transcribe audio
      const form = new FormData();
      form.append("audio", file);
      const transcribeRes = await fetch(apiUrl("/api/demands/transcribe"), {
        method: "POST",
        headers: state.token ? { Authorization: `Bearer ${state.token}` } : {},
        body: form,
      });
      if (!transcribeRes.ok) {
        console.warn("Falha na transcricao. Continuando com texto fornecido.");
      } else {
        const transcriptData = await transcribeRes.json();
        // Append transcribed text to existing input
        if (rawInput) {
          rawInput += "\n\n[Transcricao do audio]\n" + transcriptData.transcript;
        } else {
          rawInput = transcriptData.transcript;
        }
        inputType = "mixed_text_audio";
      }
    }
  }

  // Validate that we have at least a title and some input
  if (!title || rawInput.length < 10) {
    setStatus("Informe titulo e uma descricao valida da demanda (minimo 10 caracteres).", true);
    return;
  }

  setStatus("Criando demanda...");
  const createRes = await fetch(apiUrl("/api/demands"), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      title,
      raw_input: rawInput,
      input_type: inputType,
    }),
  });
  if (!createRes.ok) {
    if (createRes.status === 403) {
      setStatus("Usuario aguardando aprovacao do administrador.", true);
      return;
    }
    setStatus("Falha ao criar demanda.", true);
    return;
  }
  const demand = await createRes.json();

  setStatus("Executando orquestracao...");
  const orchestrationRes = await fetch(apiUrl(`/api/demands/${demand.id}/orchestrate`), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ provider }),
  });
  if (!orchestrationRes.ok) {
    if (orchestrationRes.status === 403) {
      setStatus("Usuario aguardando aprovacao do administrador.", true);
      return;
    }
    setStatus("Falha na orquestracao.", true);
    return;
  }
  const analysis = await orchestrationRes.json();

  renderArchitecture(analysis);
  renderAIBrief(analysis);
  renderCosts(analysis);
  renderTerraform(analysis);
  renderRanking(analysis);
  setStatus("Orquestracao concluida com sucesso.");
}

async function transcribeAudio() {
  if (!state.token) {
    setStatus("Faca login com GitHub para transcrever audio.", true);
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
  const res = await fetch(apiUrl("/api/demands/transcribe"), {
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

$("login-github-btn").addEventListener("click", loginWithGithub);
$("logout-btn").addEventListener("click", logout);
$("orchestrate-btn").addEventListener("click", orchestrate);
$("transcribe-btn").addEventListener("click", transcribeAudio);
$("catalog-sync-btn").addEventListener("click", syncCatalog);
$("catalog-provider-filter").addEventListener("change", loadCatalog);
$("catalog-search").addEventListener("input", applyCatalogFilter);

loadTokenFromUrlOrStorage();
refreshSession();
loadCatalog();
