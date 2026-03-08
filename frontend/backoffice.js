const AUTH_TOKEN_KEY = "cloudhelm.auth.token";
const config = window.CLOUDHELM_CONFIG || {};
const API_BASE_URL = (config.API_BASE_URL || "").replace(/\/$/, "");
const FRONTEND_HOME_URL = config.FRONTEND_HOME_URL || "./index.html";

const state = {
  token: localStorage.getItem(AUTH_TOKEN_KEY),
  users: [],
  selectedUserIds: new Set(),
  auditLogs: [],
  activeTab: "users",
};

const $ = (id) => document.getElementById(id);

function apiUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

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
  window.location.href = FRONTEND_HOME_URL;
}

async function ensureAdminSession() {
  if (!state.token) {
    window.location.href = FRONTEND_HOME_URL;
    return false;
  }
  const res = await fetch(apiUrl("/api/auth/session"), { headers: authHeaders() });
  if (!res.ok) {
    window.location.href = FRONTEND_HOME_URL;
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
    container.innerHTML =
      '<div class="rounded-xl border border-white/10 bg-slate-950/60 p-4 text-xs text-slate-300">Sem usuarios cadastrados.</div>';
    return;
  }
  container.innerHTML = state.users
    .map(
      (user) => `
      <div class="rounded-xl border border-white/10 bg-slate-950/60 p-4">
        <div class="flex gap-3">
          <input type="checkbox" data-user-id="${user.id}" class="user-checkbox h-4 w-4" ${state.selectedUserIds.has(user.id) ? "checked" : ""}>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-semibold">${user.name}</p>
                <p class="text-xs text-slate-300">${user.email}</p>
                <p class="text-[11px] text-slate-400">GitHub: ${user.github_login || "-"}</p>
              </div>
              <div class="flex gap-2">
                <span class="rounded px-2 py-1 text-[10px] font-semibold ${user.is_approved ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"}">
                  ${user.is_approved ? "Aprovado" : "Pendente"}
                </span>
                <select data-role-select="${user.id}" class="rounded bg-slate-800 px-2 py-1 text-[10px] font-semibold text-cyan-300 border border-cyan-500/40 hover:bg-slate-700">
                  <option value="admin" ${user.role === "admin" ? "selected" : ""}>Admin</option>
                  <option value="reviewer" ${user.role === "reviewer" ? "selected" : ""}>Reviewer</option>
                  <option value="user" ${user.role === "user" ? "selected" : ""}>User</option>
                </select>
              </div>
            </div>
            ${user.access_expires_at ? `<p class="mt-2 text-[10px] text-amber-300">Acesso expira em: ${new Date(user.access_expires_at).toLocaleDateString('pt-BR')}</p>` : ""}
            ${user.approved_at ? `<p class="text-[11px] text-slate-400 mt-1">Aprovado em: ${new Date(user.approved_at).toLocaleDateString('pt-BR')}</p>` : ""}
            <div class="mt-3 flex gap-2 flex-wrap">
              ${user.is_admin ? "" : 
                user.is_approved 
                  ? `<button data-action="revoke" data-id="${user.id}" class="rounded-lg border border-rose-300/40 px-3 py-1 text-xs text-rose-200 hover:bg-rose-500/20">Revogar</button>`
                  : `<button data-action="approve" data-id="${user.id}" class="rounded-lg border border-emerald-300/40 px-3 py-1 text-xs text-emerald-200 hover:bg-emerald-500/20">Aprovar</button>`
              }
            </div>
          </div>
        </div>
      </div>
    `
    )
    .join("");
  
  // Attach event listeners
  container.querySelectorAll(".user-checkbox").forEach(checkbox => {
    checkbox.addEventListener("change", (e) => {
      const userId = parseInt(e.target.getAttribute("data-user-id"));
      if (e.target.checked) {
        state.selectedUserIds.add(userId);
      } else {
        state.selectedUserIds.delete(userId);
      }
      updateBulkActionButtons();
    });
  });
  
  container.querySelectorAll("[data-role-select]").forEach(select => {
    select.addEventListener("change", (e) => {
      const userId = parseInt(e.target.getAttribute("data-role-select"));
      handleRoleChange(userId, e.target.value);
    });
  });
}

async function loadUsers() {
  const res = await fetch(apiUrl("/api/backoffice/users"), { headers: authHeaders() });
  if (!res.ok) {
    setStatus("Falha ao carregar usuarios.", true);
    return;
  }
  state.users = await res.json();
  renderUsers();
}

async function handleRoleChange(userId, newRole) {
  if (!confirm(`Tem certeza que deseja mudar a funcao para "${newRole}"?`)) {
    renderUsers();
    return;
  }
  const res = await fetch(apiUrl(`/api/backoffice/users/${userId}/role`), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ role: newRole }),
  });
  if (!res.ok) {
    setStatus("Falha ao mudar funcao do usuario.", true);
    return;
  }
  setStatus(`Funcao alterada para "${newRole}".`);
  await loadUsers();
}

function updateBulkActionButtons() {
  const count = state.selectedUserIds.size;
  $("bulk-action-buttons").style.display = count > 0 ? "flex" : "none";
  $("selected-users-count").textContent = count;
}

async function bulkApproveUsers() {
  if (state.selectedUserIds.size === 0) {
    setStatus("Nenhum usuario selecionado.", true);
    return;
  }
  if (!confirm(`Aprovar ${state.selectedUserIds.size} usuario(s)?`)) return;
  
  const res = await fetch(apiUrl("/api/backoffice/users/bulk-approve"), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ user_ids: Array.from(state.selectedUserIds) }),
  });
  if (!res.ok) {
    setStatus("Falha ao aprovar usuarios.", true);
    return;
  }
  const data = await res.json();
  setStatus(data.message);
  state.selectedUserIds.clear();
  await loadUsers();
}

async function grantTemporaryAccess() {
  if (state.selectedUserIds.size === 0) {
    setStatus("Nenhum usuario selecionado.", true);
    return;
  }
  const days = prompt("Quantos dias de acesso temporario? (1-90)", "7");
  if (!days || isNaN(days) || days < 1 || days > 90) {
    setStatus("Dias invalidos. Digite um numero entre 1 e 90.", true);
    return;
  }
  
  const res = await fetch(apiUrl("/api/backoffice/users/temporary-access"), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ user_ids: Array.from(state.selectedUserIds), days: parseInt(days) }),
  });
  if (!res.ok) {
    setStatus("Falha ao conceder acesso temporario.", true);
    return;
  }
  const data = await res.json();
  setStatus(data.message);
  state.selectedUserIds.clear();
  await loadUsers();
}

async function loadAuditLogs() {
  const res = await fetch(apiUrl("/api/backoffice/audit-logs?limit=50"), { headers: authHeaders() });
  if (!res.ok) {
    setStatus("Falha ao carregar logs de auditoria.", true);
    return;
  }
  state.auditLogs = await res.json();
  renderAuditLogs();
}

function renderAuditLogs() {
  const container = $("audit-logs-container");
  if (!state.auditLogs.length) {
    container.innerHTML =
      '<div class="rounded-xl border border-white/10 bg-slate-950/60 p-4 text-xs text-slate-300">Nenhum log de auditoria encontrado.</div>';
    return;
  }
  const rows = state.auditLogs
    .map(log => `
      <tr class="border-b border-slate-700 hover:bg-slate-800/50">
        <td class="px-4 py-3 text-sm">${log.action}</td>
        <td class="px-4 py-3 text-sm text-slate-300">${log.description}</td>
        <td class="px-4 py-3 text-xs text-slate-400">${log.target_user_id || "-"}</td>
        <td class="px-4 py-3 text-xs text-slate-400">${new Date(log.created_at).toLocaleDateString('pt-BR')} ${new Date(log.created_at).toLocaleTimeString('pt-BR')}</td>
      </tr>
    `)
    .join("");
  
  container.innerHTML = `
    <table class="w-full text-left text-sm">
      <thead class="border-b border-slate-600 bg-slate-800/50">
        <tr>
          <th class="px-4 py-3 font-semibold text-slate-200">Acao</th>
          <th class="px-4 py-3 font-semibold text-slate-200">Descricao</th>
          <th class="px-4 py-3 font-semibold text-slate-200">Usuario Afetado</th>
          <th class="px-4 py-3 font-semibold text-slate-200">Data/Hora</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  `;
}

async function handleUserAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const userId = button.getAttribute("data-id");
  const action = button.getAttribute("data-action");
  const endpoint = action === "approve" ? "approve" : "revoke";
  const res = await fetch(apiUrl(`/api/backoffice/users/${userId}/${endpoint}`), {
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
  const res = await fetch(apiUrl("/api/backoffice/llm-config"), { headers: authHeaders() });
  if (!res.ok) {
    setStatus("Falha ao carregar configuracao de IA.", true);
    return;
  }
  const data = await res.json();
  $("llm-provider").value = data.provider || "none";
  $("llm-model").value = data.model || "";
  
  // Update status displays
  const openaiStatus = data.openai_api_key_masked ? `✅ Configurada (${data.openai_api_key_masked})` : "❌ Nao configurada";
  const geminiStatus = data.gemini_api_key_masked ? `✅ Configurada (${data.gemini_api_key_masked})` : "❌ Nao configurada";
  $("openai-status").textContent = openaiStatus;
  $("gemini-status").textContent = geminiStatus;
  
  $("llm-meta").innerHTML = `
    <p class="font-semibold text-cyan-300">Status das conexoes:</p>
    <p class="mt-2">OpenAI: ${openaiStatus}</p>
    <p class="mt-1">Gemini: ${geminiStatus}</p>
    <p class="mt-3 text-slate-300">As chaves sao armazenadas de forma segura. Voce so vera os ultimos 4 caracteres por motivos de seguranca.</p>
  `;
}

async function saveLlmConfig() {
  const payload = {
    provider: $("llm-provider").value,
    model: $("llm-model").value.trim(),
    openai_api_key: $("openai-key").value.trim(),
    gemini_api_key: $("gemini-key").value.trim(),
  };
  const res = await fetch(apiUrl("/api/backoffice/llm-config"), {
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
  
  // Update status displays
  const openaiStatus = data.openai_api_key_masked ? `✅ Configurada (${data.openai_api_key_masked})` : "❌ Nao configurada";
  const geminiStatus = data.gemini_api_key_masked ? `✅ Configurada (${data.gemini_api_key_masked})` : "❌ Nao configurada";
  $("openai-status").textContent = openaiStatus;
  $("gemini-status").textContent = geminiStatus;
  
  $("llm-meta").innerHTML = `
    <p class="font-semibold text-emerald-300">✨ Configuracao salva com sucesso!</p>
    <p class="mt-2">OpenAI: ${openaiStatus}</p>
    <p class="mt-1">Gemini: ${geminiStatus}</p>
    <p class="mt-3 text-slate-300">A IA agora processara as demandas com o modelo selecionado.</p>
  `;
  setStatus("Configuracao IA salva no backoffice.");
}

async function init() {
  const ok = await ensureAdminSession();
  if (!ok) return;
  
  $("logout-btn").addEventListener("click", logout);
  $("save-llm-btn").addEventListener("click", saveLlmConfig);
  $("reload-llm-btn").addEventListener("click", loadLlmConfig);
  $("users-grid").addEventListener("click", handleUserAction);
  
  // Bulk actions
  $("bulk-approve-btn").addEventListener("click", bulkApproveUsers);
  $("bulk-temporary-btn").addEventListener("click", grantTemporaryAccess);
  
  // Tabs
  document.querySelectorAll("[data-tab]").forEach(tab => {
    tab.addEventListener("click", (e) => {
      state.activeTab = e.target.getAttribute("data-tab");
      document.querySelectorAll("[data-tab-content]").forEach(el => {
        el.style.display = el.getAttribute("data-tab-content") === state.activeTab ? "block" : "none";
      });
      document.querySelectorAll("[data-tab]").forEach(t => {
        t.classList.toggle("border-b-2 border-cyan-500 text-cyan-300", t.getAttribute("data-tab") === state.activeTab);
      });
      
      if (state.activeTab === "audit") {
        loadAuditLogs();
      }
    });
  });
  
  await loadLlmConfig();
  await loadUsers();
}

init();
