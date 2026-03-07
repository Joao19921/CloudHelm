const AUTH_TOKEN_KEY = "cloudhelm.auth.token";
const state = {
  token: localStorage.getItem(AUTH_TOKEN_KEY),
  users: [],
};

const $ = (id) => document.getElementById(id);

function setStatus(message, isError = false) {
  const el = $("status");
  el.textContent = message;
  el.className = isError ? "text-xs text-rose-300" : "text-xs text-emerald-300";
}

function authHeaders() {
  if (!state.token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${state.token}`,
  };
}

function logout() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  window.location.href = "/";
}

async function ensureAdminSession() {
  if (!state.token) {
    window.location.href = "/";
    return false;
  }
  const res = await fetch("/api/auth/session", { headers: authHeaders() });
  if (!res.ok) {
    window.location.href = "/";
    return false;
  }
  const session = await res.json();
  if (!session.is_admin) {
    setStatus("Acesso negado: apenas administrador.", true);
    return false;
  }
  return true;
}

function renderUsers() {
  const container = $("users-grid");
  if (!state.users.length) {
    container.innerHTML = '<div class="rounded-xl border border-white/10 bg-slate-950/60 p-4 text-xs text-slate-300">Sem usuarios cadastrados.</div>';
    return;
  }
  container.innerHTML = state.users
    .map(
      (user) => `
      <div class="rounded-xl border border-white/10 bg-slate-950/60 p-4">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p class="text-sm font-semibold">${user.name}</p>
            <p class="text-xs text-slate-300">${user.email}</p>
            <p class="text-[11px] text-slate-400">GitHub: ${user.github_login || "-"} | Provider: ${user.auth_provider}</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="rounded px-2 py-1 text-[10px] font-semibold ${user.is_approved ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"}">
              ${user.is_approved ? "Aprovado" : "Pendente"}
            </span>
            <span class="rounded px-2 py-1 text-[10px] font-semibold ${user.is_admin ? "bg-sky-500/20 text-sky-300" : "bg-slate-500/20 text-slate-300"}">
              ${user.is_admin ? "Admin" : "User"}
            </span>
            ${
              user.is_admin
                ? ""
                : user.is_approved
                  ? `<button data-action="revoke" data-id="${user.id}" class="rounded-lg border border-rose-300/40 px-3 py-1 text-xs text-rose-200 hover:bg-rose-500/20">Revogar</button>`
                  : `<button data-action="approve" data-id="${user.id}" class="rounded-lg border border-emerald-300/40 px-3 py-1 text-xs text-emerald-200 hover:bg-emerald-500/20">Aprovar</button>`
            }
          </div>
        </div>
      </div>
    `
    )
    .join("");
}

async function loadUsers() {
  const res = await fetch("/api/backoffice/users", { headers: authHeaders() });
  if (!res.ok) {
    setStatus("Falha ao carregar usuarios.", true);
    return;
  }
  state.users = await res.json();
  renderUsers();
}

async function handleUserAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const userId = button.getAttribute("data-id");
  const action = button.getAttribute("data-action");
  const endpoint = action === "approve" ? "approve" : "revoke";
  const res = await fetch(`/api/backoffice/users/${userId}/${endpoint}`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    setStatus("Falha ao atualizar permissao do usuario.", true);
    return;
  }
  setStatus(action === "approve" ? "Usuario aprovado." : "Acesso revogado.");
  await loadUsers();
}

async function loadLlmConfig() {
  const res = await fetch("/api/backoffice/llm-config", { headers: authHeaders() });
  if (!res.ok) {
    setStatus("Falha ao carregar configuracao de IA.", true);
    return;
  }
  const data = await res.json();
  $("llm-provider").value = data.provider || "none";
  $("llm-model").value = data.model || "";
  $("llm-meta").textContent = `OpenAI: ${data.openai_api_key_masked || "nao configurada"} | Gemini: ${data.gemini_api_key_masked || "nao configurada"}`;
}

async function saveLlmConfig() {
  const payload = {
    provider: $("llm-provider").value,
    model: $("llm-model").value.trim(),
    openai_api_key: $("openai-key").value.trim(),
    gemini_api_key: $("gemini-key").value.trim(),
  };
  const res = await fetch("/api/backoffice/llm-config", {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    setStatus(err.detail || "Falha ao salvar configuracao IA.", true);
    return;
  }
  const data = await res.json();
  $("openai-key").value = "";
  $("gemini-key").value = "";
  $("llm-meta").textContent = `OpenAI: ${data.openai_api_key_masked || "nao configurada"} | Gemini: ${data.gemini_api_key_masked || "nao configurada"}`;
  setStatus("Configuracao IA salva no backoffice.");
}

async function init() {
  const ok = await ensureAdminSession();
  if (!ok) return;
  $("logout-btn").addEventListener("click", logout);
  $("save-llm-btn").addEventListener("click", saveLlmConfig);
  $("reload-llm-btn").addEventListener("click", loadLlmConfig);
  $("users-grid").addEventListener("click", handleUserAction);
  await loadLlmConfig();
  await loadUsers();
}

init();
