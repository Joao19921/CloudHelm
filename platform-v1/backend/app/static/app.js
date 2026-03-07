const state = {
  token: null,
  userEmail: null,
  catalog: [],
  llmSettings: {
    llmProvider: "none",
    llmModel: "",
    openaiApiKey: "",
    geminiApiKey: "",
  },
};

const $ = (id) => document.getElementById(id);
const SETTINGS_STORAGE_KEY = "cloudhelm.llm.settings.v1";

const statusEl = $("status");
const authStateEl = $("auth-state");
const llmStateEl = $("llm-state");
const architectureEl = $("architecture");
const costsEl = $("costs");
const terraformEl = $("terraform-modules");
const rankingEl = $("ranking");
const aiBriefEl = $("ai-brief");
const catalogGridEl = $("catalog-grid");
const catalogMetaEl = $("catalog-meta");
const settingsModalEl = $("settings-modal");
const settingsProviderEl = $("settings-llm-provider");
const settingsModelEl = $("settings-llm-model");
const settingsOpenAiKeyEl = $("settings-openai-key");
const settingsGeminiKeyEl = $("settings-gemini-key");
const settingsOpenAiWrapEl = $("settings-openai-wrap");
const settingsGeminiWrapEl = $("settings-gemini-wrap");
const settingsValidationEl = $("settings-validation");

function maskSecret(secret) {
  if (!secret) return "nao configurada";
  if (secret.length <= 8) return `${secret.slice(0, 2)}****`;
  return `${secret.slice(0, 4)}****${secret.slice(-4)}`;
}

function setInputValidationState(inputEl, isValid, enabled = true) {
  inputEl.classList.remove("border-emerald-400/70", "border-rose-400/70", "border-white/10");
  if (!enabled) {
    inputEl.classList.add("border-white/10");
    return;
  }
  inputEl.classList.add(isValid ? "border-emerald-400/70" : "border-rose-400/70");
}

function loadSettingsFromStorage() {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    state.llmSettings = {
      llmProvider: parsed.llmProvider || "none",
      llmModel: parsed.llmModel || "",
      openaiApiKey: parsed.openaiApiKey || "",
      geminiApiKey: parsed.geminiApiKey || "",
    };
  } catch (_e) {
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
  }
}

function persistSettings() {
  localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(state.llmSettings));
}

function evaluateLlmSettings(settings) {
  if (settings.llmProvider === "none") {
    return { valid: true, message: "Modo deterministico ativo.", level: "info" };
  }
  if (!settings.llmModel || settings.llmModel.length < 3) {
    return { valid: false, message: "Modelo invalido. Minimo de 3 caracteres.", level: "error" };
  }
  if (settings.llmProvider === "openai") {
    const key = settings.openaiApiKey.trim();
    const valid = /^sk-[A-Za-z0-9_-]{20,}$/.test(key);
    return valid
      ? { valid: true, message: `OpenAI key valida (${maskSecret(key)}).`, level: "success" }
      : { valid: false, message: "OpenAI key invalida. Esperado prefixo sk-.", level: "error" };
  }
  if (settings.llmProvider === "gemini") {
    const key = settings.geminiApiKey.trim();
    const valid = /^AIza[A-Za-z0-9_-]{20,}$/.test(key);
    return valid
      ? { valid: true, message: `Gemini key valida (${maskSecret(key)}).`, level: "success" }
      : { valid: false, message: "Gemini key invalida. Esperado prefixo AIza.", level: "error" };
  }
  return { valid: false, message: "Provedor IA invalido.", level: "error" };
}

function updateLlmStateBadge() {
  const evaluation = evaluateLlmSettings(state.llmSettings);
  if (state.llmSettings.llmProvider === "none") {
    llmStateEl.textContent = "IA: Deterministico";
    llmStateEl.className =
      "rounded-lg border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300";
    return;
  }
  const providerLabel = state.llmSettings.llmProvider === "openai" ? "GPT" : "Gemini";
  llmStateEl.textContent = evaluation.valid ? `IA: ${providerLabel} configurado` : `IA: ${providerLabel} invalido`;
  llmStateEl.className = evaluation.valid
    ? "rounded-lg border border-emerald-400/40 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300"
    : "rounded-lg border border-rose-400/40 bg-rose-500/10 px-3 py-1 text-xs text-rose-300";
}

function syncSettingsInputsFromState() {
  settingsProviderEl.value = state.llmSettings.llmProvider;
  settingsModelEl.value = state.llmSettings.llmModel;
  settingsOpenAiKeyEl.value = state.llmSettings.openaiApiKey;
  settingsGeminiKeyEl.value = state.llmSettings.geminiApiKey;
}

function readSettingsInputs() {
  return {
    llmProvider: settingsProviderEl.value,
    llmModel: settingsModelEl.value.trim(),
    openaiApiKey: settingsOpenAiKeyEl.value.trim(),
    geminiApiKey: settingsGeminiKeyEl.value.trim(),
  };
}

function updateSettingsFieldVisibility(provider) {
  const openAiEnabled = provider === "openai";
  const geminiEnabled = provider === "gemini";
  settingsOpenAiKeyEl.disabled = !openAiEnabled;
  settingsGeminiKeyEl.disabled = !geminiEnabled;
  settingsOpenAiWrapEl.classList.toggle("opacity-40", !openAiEnabled);
  settingsGeminiWrapEl.classList.toggle("opacity-40", !geminiEnabled);
}

function renderSettingsValidation(evaluation, draft) {
  const validationClass =
    evaluation.level === "success"
      ? "rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-200"
      : evaluation.level === "error"
        ? "rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-200"
        : "rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-xs text-slate-300";
  settingsValidationEl.className = validationClass;
  settingsValidationEl.textContent = evaluation.message;

  const keyToValidate = draft.llmProvider === "gemini" ? settingsGeminiKeyEl : settingsOpenAiKeyEl;
  const otherKey = draft.llmProvider === "gemini" ? settingsOpenAiKeyEl : settingsGeminiKeyEl;

  setInputValidationState(settingsModelEl, draft.llmProvider === "none" || draft.llmModel.length >= 3);
  setInputValidationState(keyToValidate, draft.llmProvider === "none" || evaluation.valid, draft.llmProvider !== "none");
  setInputValidationState(otherKey, true, false);
}

function validateSettingsUi() {
  const draft = readSettingsInputs();
  updateSettingsFieldVisibility(draft.llmProvider);
  const evaluation = evaluateLlmSettings(draft);
  renderSettingsValidation(evaluation, draft);
  return { draft, evaluation };
}

function openSettingsModal() {
  syncSettingsInputsFromState();
  validateSettingsUi();
  settingsModalEl.classList.remove("hidden");
  settingsModalEl.classList.add("flex");
}

function closeSettingsModal() {
  settingsModalEl.classList.add("hidden");
  settingsModalEl.classList.remove("flex");
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

function renderAIBrief(analysis) {
  const ai = analysis.ai || analysis.architecture?.ai || {};
  if (!ai || !ai.brief) {
    aiBriefEl.innerHTML = "";
    return;
  }
  const providerLabel =
    ai.provider === "openai"
      ? "GPT"
      : ai.provider === "gemini"
        ? "Gemini"
        : "Deterministico";
  const badgeClass = ai.used_fallback ? "text-amber-300" : "text-emerald-300";

  aiBriefEl.innerHTML = `
    <div class="rounded-xl border border-white/10 bg-slate-950/55 p-3">
      <p class="text-sm font-semibold text-brand-200">Brief IA da Arquitetura</p>
      <p class="mt-1 text-[11px] text-slate-300">
        Engine: <span class="${badgeClass} font-semibold">${providerLabel}</span> | Modelo: <span class="text-slate-200">${ai.model || "-"}</span>
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
  const llmProvider = state.llmSettings.llmProvider;
  const llmModel = state.llmSettings.llmModel || null;
  const llmApiKey =
    llmProvider === "openai"
      ? state.llmSettings.openaiApiKey || null
      : llmProvider === "gemini"
        ? state.llmSettings.geminiApiKey || null
        : null;
  const fileInput = $("demand-file");

  const llmEvaluation = evaluateLlmSettings(state.llmSettings);
  if (llmProvider !== "none" && !llmEvaluation.valid) {
    setStatus("Settings IA invalido. Clique em 'Settings IA' e valide sua chave.", true);
    openSettingsModal();
    return;
  }

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
    body: JSON.stringify({
      provider,
      llm_provider: llmProvider,
      llm_model: llmModel,
      llm_api_key: llmApiKey,
    }),
  });
  if (!orchestrationRes.ok) {
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

function initSettingsUi() {
  loadSettingsFromStorage();
  updateLlmStateBadge();
  syncSettingsInputsFromState();
  validateSettingsUi();
}

$("register-btn").addEventListener("click", register);
$("login-btn").addEventListener("click", login);
$("orchestrate-btn").addEventListener("click", orchestrate);
$("transcribe-btn").addEventListener("click", transcribeAudio);
$("catalog-sync-btn").addEventListener("click", syncCatalog);
$("catalog-provider-filter").addEventListener("change", loadCatalog);
$("catalog-search").addEventListener("input", applyCatalogFilter);
$("open-settings-btn").addEventListener("click", openSettingsModal);
$("close-settings-btn").addEventListener("click", closeSettingsModal);
$("test-settings-btn").addEventListener("click", () => {
  const { evaluation } = validateSettingsUi();
  setStatus(evaluation.message, !evaluation.valid);
});
$("save-settings-btn").addEventListener("click", () => {
  const { draft, evaluation } = validateSettingsUi();
  if (!evaluation.valid) {
    setStatus("Nao foi possivel salvar. Corrija os campos de Settings IA.", true);
    return;
  }
  state.llmSettings = draft;
  persistSettings();
  updateLlmStateBadge();
  setStatus("Settings IA salvos localmente.");
  closeSettingsModal();
});
$("clear-settings-btn").addEventListener("click", () => {
  state.llmSettings = {
    llmProvider: "none",
    llmModel: "",
    openaiApiKey: "",
    geminiApiKey: "",
  };
  persistSettings();
  syncSettingsInputsFromState();
  validateSettingsUi();
  updateLlmStateBadge();
  setStatus("Settings IA limpos.");
});
settingsProviderEl.addEventListener("change", validateSettingsUi);
settingsModelEl.addEventListener("input", validateSettingsUi);
settingsOpenAiKeyEl.addEventListener("input", validateSettingsUi);
settingsGeminiKeyEl.addEventListener("input", validateSettingsUi);
settingsModalEl.addEventListener("click", (event) => {
  if (event.target === settingsModalEl) closeSettingsModal();
});

initSettingsUi();
loadCatalog();
