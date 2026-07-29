import { useCallback, useEffect, useMemo, useState } from "react";

const AUTH_TOKEN_KEY = "cloudhelm.auth.token";
const config = window.CLOUDHELM_CONFIG || {};
const API_BASE_URL = (config.API_BASE_URL || "").replace(/\/$/, "");

const providers = ["aws", "gcp", "azure", "oci"];
const serviceTypeLabels = {
  compute: "Compute",
  database: "Database",
  cache: "Cache",
  storage: "Storage",
  network: "Network",
  observability: "Observabilidade",
  security: "Segurança",
  ai_ml: "AI / ML",
  integration: "Integração",
  other: "Outros",
};
const providerMeta = {
  aws: { label: "AWS", subtitle: "Amazon Web Services", tone: "orange" },
  gcp: { label: "GCP", subtitle: "Google Cloud Platform", tone: "blue" },
  azure: { label: "Azure", subtitle: "Microsoft Azure", tone: "cyan" },
  oci: { label: "OCI", subtitle: "Oracle Cloud Infrastructure", tone: "rose" },
};
const stepStyles = {
  cyan: { border: "border-cyan-300/20", text: "text-cyan-300" },
  violet: { border: "border-violet-300/20", text: "text-violet-300" },
  emerald: { border: "border-emerald-300/20", text: "text-emerald-300" },
};
const promptExamples = [
  "Quero desenvolver um marketplace para 100 mil usuários",
  "Preciso de um sistema hospitalar com alta disponibilidade",
  "Desejo criar um aplicativo financeiro para um milhão de usuários",
];
const card = "rounded-3xl border border-white/10 bg-slate-900/70 p-6 shadow-[0_30px_80px_-50px_rgba(15,23,42,0.8)]";
const input = "w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/70 focus:ring-2 focus:ring-cyan-300/20";

function apiUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

function iconUrl(path) {
  if (!path) return "./assets/icons/generic.svg";
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/static/icons/cloud/")) return `./assets/icons/cloud/${path.split("/").pop()}`;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function authHeaders(token) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function trackEvent(token, eventName, metadata = {}) {
  if (!token) return;
  void fetch(apiUrl("/api/telemetry/events"), {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ event_name: eventName, event_category: "interaction", event_status: "success", metadata }),
  }).catch(() => {});
}

function formatMoney(value) {
  return Number(value || 0).toFixed(2);
}

function downloadArtifact(content, filename, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportAnalysis(analysis, format) {
  if (!analysis) return;
  if (format === "json") {
    downloadArtifact(JSON.stringify(analysis, null, 2), "cloudhelm-base-arquitetural.json", "application/json");
    return;
  }

  const summary = analysis.executive_summary || {};
  const lines = [
    "# Base arquitetural CloudHelm",
    "",
    "## Resumo executivo",
    summary.interpretation || "",
    "",
    `Escala: ${summary.scale || "a definir"}`,
    `Provider de referência: ${summary.provider_reference || analysis.provider}`,
    "",
    "## Objetivos",
    ...(summary.objectives || []).map((item) => `- ${item}`),
    "",
    "## Riscos",
    ...(analysis.risks || []).map((item) => `- [${item.severity}] ${item.title}: ${item.mitigation}`),
    "",
    "## Plano inicial",
    ...(analysis.implementation_plan || []).map((item, index) => `${index + 1}. ${item.step} — ${item.description}`),
  ];
  downloadArtifact(lines.join("\n"), "cloudhelm-base-arquitetural.md");
}

function BusyOverlay({ busy }) {
  if (!busy) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/85 backdrop-blur-sm px-4">
      <div className="inline-flex items-center gap-3 rounded-3xl bg-slate-900/95 px-6 py-4 text-sm font-semibold text-slate-100 shadow-xl shadow-cyan-500/10">
        <span className="h-3 w-3 animate-pulse rounded-full bg-cyan-300" />
        Processando solicitação...
      </div>
    </div>
  );
}

function Header({ session, onLogout }) {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/95 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <img src="./assets/brand/cloudhelm-logo.png" alt="CloudHelm" className="h-12 w-auto object-contain" />
          <div>
            <p className="text-sm font-semibold text-slate-100">CloudHelm</p>
            <p className="text-xs text-slate-400">Blueprint arquitetural multi-cloud</p>
          </div>
        </div>
        <div className="flex flex-1 flex-col items-end gap-3 sm:flex-row sm:items-center sm:justify-end">
          {session?.is_admin && (
            <a href="./backoffice.html" className="rounded-xl border border-cyan-300/40 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-200">
              Backoffice
            </a>
          )}
          {session ? (
            <button onClick={onLogout} className="rounded-xl border border-white/15 px-3 py-2 text-xs text-slate-200 hover:bg-white/10">
              Sair
            </button>
          ) : null}
          <p className="max-w-[16rem] truncate text-sm text-slate-300">
            {session ? `Autenticado: ${session.email}` : "Não autenticado"}
          </p>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="grid items-center gap-12 lg:grid-cols-2">
      <div>
        <p className="inline-flex rounded-full border border-cyan-300/30 bg-cyan-400/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
          Arquitetura & Infraestrutura
        </p>
        <h1 className="mt-6 text-4xl font-extrabold leading-tight text-white sm:text-5xl">
          Transforme requisitos em arquitetura executável.
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
          O CloudHelm organiza contexto, recomenda serviços multi-cloud e gera documentação de arquitetura e infraestrutura inicial.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a href="#workspace" className="rounded-2xl bg-gradient-to-r from-blue-500 via-cyan-400 to-violet-500 px-6 py-3 text-sm font-bold text-slate-950 shadow-glow">
            Criar base arquitetural
          </a>
          <a href="./demo.html" className="rounded-2xl border border-white/15 bg-white/5 px-6 py-3 text-sm font-semibold text-slate-100 hover:border-cyan-300/60">
            Explorar exemplo
          </a>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 text-center text-slate-300 text-xs">
        {[
          { value: "4", label: "Camadas de referência" },
          { value: "C4", label: "Modelos de arquitetura" },
          { value: "IaC", label: "Infraestrutura inicial" },
          { value: "API", label: "Decisões rastreáveis" },
        ].map((item) => (
          <article key={item.label} className="rounded-3xl border border-white/10 bg-slate-900/60 p-6">
            <p className="text-3xl font-bold text-cyan-300">{item.value}</p>
            <p className="mt-2">{item.label}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ProductSteps() {
  return (
    <section className="mt-14 grid gap-4 md:grid-cols-3">
      {[
        {
          accent: "cyan",
          title: "Entender",
          description: "Requisitos, jornadas e restrições viram uma base comum para produto e engenharia.",
          label: "01 · Entender",
        },
        {
          accent: "violet",
          title: "Desenhar",
          description: "Arquitetura, dados e infraestrutura são entregues com clareza e rastreabilidade.",
          label: "02 · Desenhar",
        },
        {
          accent: "emerald",
          title: "Evoluir",
          description: "Uma base de decisões e riscos para guiar o próximo ciclo.",
          label: "03 · Evoluir",
        },
      ].map((step) => (
        <article key={step.title} className={`${card} ${stepStyles[step.accent].border}`}>
          <p className={`text-xs font-bold uppercase tracking-[0.16em] ${stepStyles[step.accent].text}`}>
            {step.label}
          </p>
          <h3 className="mt-3 text-lg font-bold">{step.title}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">{step.description}</p>
        </article>
      ))}
    </section>
  );
}

function QuickStatus({ status, isError }) {
  if (!status) return null;
  return (
    <div className={`rounded-3xl border p-4 text-sm ${isError ? "border-rose-300/20 bg-rose-950/10 text-rose-200" : "border-emerald-300/20 bg-emerald-950/10 text-emerald-200"}`} role="status" aria-live="polite">
      {status}
    </div>
  );
}

function SavedBases({ bases, onOpen, onDelete, busy }) {
  return (
    <section className={card}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between md:gap-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-300">Memória de trabalho</p>
          <h2 className="mt-2 text-lg font-semibold">Bases arquiteturais salvas</h2>
          <p className="mt-1 text-sm text-slate-300">Reabra uma base para revisar, refinar ou exportar. Limite de 3 bases por conta.</p>
        </div>
        <span className="rounded-full border border-white/10 bg-slate-950/40 px-3 py-2 text-xs text-slate-300">
          {bases.length}/3 usadas
        </span>
      </div>
      {!bases.length ? (
        <div className="mt-5 rounded-3xl border border-dashed border-white/15 bg-slate-950/30 p-6 text-center text-sm text-slate-400">
          Nenhuma base salva ainda. A primeira análise aparecerá aqui.
        </div>
      ) : (
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {bases.map((base) => (
            <article key={base.id} className="min-w-0 rounded-3xl border border-white/10 bg-slate-950/60 p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-100">{base.title}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {new Date(base.created_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" })}
                  </p>
                </div>
                <span className="rounded-full bg-white/5 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300">
                  {base.provider_selected?.toUpperCase() || "RASCUNHO"}
                </span>
              </div>
              <p
                className="mt-4 text-sm leading-6 text-slate-300"
                style={{
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                  whiteSpace: "pre-wrap",
                }}
              >
                {base.raw_input}
              </p>
              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onOpen(base)}
                  className="min-w-0 flex-1 rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-wait disabled:opacity-50"
                >
                  Abrir base
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDelete(base)}
                  className="min-w-0 rounded-2xl border border-rose-300/30 px-4 py-3 text-sm text-rose-200 transition hover:bg-rose-300/10 disabled:opacity-50"
                >
                  Apagar
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function DemandForm({ provider, setProvider, onSubmit, onLogin, busy, session, draft }) {
  const [title, setTitle] = useState("");
  const [rawInput, setRawInput] = useState("");

  useEffect(() => {
    if (draft) {
      setTitle(draft.title || "");
      setRawInput(draft.rawInput || "");
    }
  }, [draft]);

  const submit = (event) => {
    event.preventDefault();
    onSubmit({ title, rawInput });
  };

  return (
    <section className="grid gap-6 lg:grid-cols-3">
      <form id="demand-form" onSubmit={submit} className={`${card} lg:col-span-2`}>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-300">Agente de arquitetura</p>
        <h2 className="mt-2 text-xl font-bold">Conte o desafio de negócio</h2>
        <p className="mt-1 text-sm text-slate-300">O agente interpreta a intenção e entrega uma base arquitetural clara.</p>
        <div className="mt-5 flex flex-wrap gap-2">
          {promptExamples.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setRawInput(example)}
              className="rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-left text-xs text-slate-300 transition hover:border-cyan-300/60 hover:text-cyan-200"
            >
              {example}
            </button>
          ))}
        </div>
        <div className="mt-6 space-y-4">
          <label className="block text-xs font-semibold text-slate-300">
            Referência da demanda
            <input
              required
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Ex: Demanda de marketplace"
              className={`${input} mt-2`}
            />
          </label>
          <label className="block text-xs font-semibold text-slate-300">
            Contexto e requisitos
            <textarea
              required
              minLength={10}
              value={rawInput}
              onChange={(event) => setRawInput(event.target.value)}
              rows="8"
              placeholder="Descreva usuários, jornadas, integrações, dados, escala, segurança e restrições."
              className={`${input} mt-2 resize-none`}
            />
          </label>
        </div>
      </form>
      <aside className={card}>
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet-300">Configuração inicial</p>
        <h2 className="mt-2 text-lg font-semibold">Escolha o cloud de referência</h2>
        <p className="mt-1 text-sm text-slate-300">A base é gerada com um provedor de referência. Pode ser refinada depois.</p>
        {!session && (
          <button
            type="button"
            onClick={onLogin}
            className="mt-5 w-full rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Entrar com GitHub
          </button>
        )}
        <label className="mt-6 block text-xs font-semibold text-slate-300">
          Cloud de referência
          <select
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
            className={`${input} mt-2`}
          >
            {providers.concat("auto").map((item) => (
              <option key={item} value={item}>
                {item.toUpperCase()}
              </option>
            ))}
          </select>
        </label>
        <button
          form="demand-form"
          disabled={busy}
          type="submit"
          className="mt-6 w-full rounded-2xl bg-gradient-to-r from-blue-500 via-cyan-400 to-violet-500 px-5 py-3 text-sm font-semibold text-slate-950 transition disabled:cursor-wait disabled:opacity-60"
        >
          {busy ? "Analisando desafio..." : "Construir base arquitetural"}
        </button>
      </aside>
    </section>
  );
}

function Catalog({ catalog, onSync, token }) {
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [type, setType] = useState("all");
  const [search, setSearch] = useState("");
  const [usage, setUsage] = useState({});

  const defaultUsage = (unit) => (/hrs|hour/i.test(unit || "") ? 730 : 1);

  const counts = useMemo(
    () =>
      catalog.reduce((acc, item) => {
        const cloud = item.provider?.toLowerCase();
        if (cloud) acc[cloud] = (acc[cloud] || 0) + 1;
        return acc;
      }, {}),
    [catalog]
  );

  const filtered = useMemo(
    () =>
      catalog.filter(
        (item) =>
          item.provider === selectedProvider &&
          (type === "all" || (item.service_type || "other") === type) &&
          (!search || `${item.display_name} ${item.service}`.toLowerCase().includes(search.toLowerCase()))
      ),
    [catalog, selectedProvider, type, search]
  );

  const grouped = useMemo(() => {
    const groups = filtered.reduce((acc, item) => {
      const kind = item.service_type || "other";
      acc[kind] ||= [];
      acc[kind].push(item);
      return acc;
    }, {});
    return Object.fromEntries(
      Object.entries(groups).map(([kind, items]) => [
        kind,
        items.sort((a, b) => Number(a.price) - Number(b.price) || a.display_name.localeCompare(b.display_name)),
      ])
    );
  }, [filtered]);

  const chooseProvider = (provider) => {
    setSelectedProvider((current) => (current === provider ? null : provider));
    setType("all");
    setSearch("");
  };

  return (
    <section className={card}>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Catálogo de custos cloud</h2>
          <p className="mt-1 text-sm text-slate-300">Preços de referência por serviço. Ajuste o consumo para comparar custos.</p>
        </div>
        {token && (
          <button
            onClick={onSync}
            className="rounded-2xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Atualizar biblioteca
          </button>
        )}
      </div>
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {providers.map((provider) => {
          const meta = providerMeta[provider];
          const active = selectedProvider === provider;
          return (
            <button
              key={provider}
              type="button"
              aria-pressed={active}
              onClick={() => chooseProvider(provider)}
              className={`rounded-3xl border p-4 text-left transition ${
                active ? "border-cyan-300/70 bg-cyan-300/10 shadow-glow" : "border-white/10 bg-slate-950/55 hover:border-white/30"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-bold text-slate-100">{meta.label}</span>
                <span className="text-[11px] text-slate-400">{counts[provider] || 0} serviços</span>
              </div>
              <p className="mt-2 text-[11px] text-slate-400">{meta.subtitle}</p>
              <span className="mt-3 inline-flex text-[11px] font-semibold text-cyan-200">{active ? "Recolher serviços ↑" : "Abrir serviços →"}</span>
            </button>
          );
        })}
      </div>
      {!selectedProvider ? (
        <div className="mt-5 rounded-3xl border border-dashed border-white/15 bg-slate-950/30 p-6 text-center text-sm text-slate-400">
          Selecione um cloud para explorar os blocos de infraestrutura do catálogo.
        </div>
      ) : (
        <div className="mt-5 rounded-3xl border border-cyan-300/20 bg-slate-950/35 p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="font-bold uppercase tracking-wide text-cyan-200">{providerMeta[selectedProvider].label}</h3>
              <p className="text-xs text-slate-400">{providerMeta[selectedProvider].subtitle} · {filtered.length} serviços exibidos</p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <select
                aria-label="Filtrar por tipo"
                value={type}
                onChange={(event) => setType(event.target.value)}
                className="rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-2 text-sm outline-none focus:border-cyan-300/60"
              >
                <option value="all">Todas as categorias</option>
                {Object.entries(serviceTypeLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              <input
                aria-label="Pesquisar serviço"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Pesquisar serviço..."
                className="rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-2 text-sm outline-none focus:border-cyan-300/60"
              />
            </div>
          </div>
          {!filtered.length ? (
            <div className="mt-5 rounded-3xl border border-white/10 bg-slate-950/50 p-5 text-xs text-slate-300">
              Nenhum serviço encontrado para este filtro.
            </div>
          ) : (
            <div className="mt-5 space-y-4">
              {Object.entries(grouped).map(([kind, items], index) => (
                <details key={kind} open={index === 0 || type === kind} className="rounded-3xl border border-white/10 bg-slate-950/50">
                  <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-slate-200">
                    {serviceTypeLabels[kind] || kind}
                    <span className="ml-2 text-xs font-normal text-slate-500">({items.length})</span>
                  </summary>
                  <div className="grid gap-3 border-t border-white/10 p-4 md:grid-cols-2 xl:grid-cols-3">
                    {items.map((item) => (
                      <article key={item.id} className="rounded-3xl border border-white/10 bg-slate-950/70 p-4 transition hover:border-cyan-300/40">
                        <div className="flex items-start justify-between gap-3">
                          <img
                            src={iconUrl(item.icon)}
                            alt={`${item.provider} ${item.service}`}
                            className="h-10 w-10 object-contain"
                            onError={(event) => {
                              event.currentTarget.onerror = null;
                              event.currentTarget.src = "./assets/icons/generic.svg";
                            }}
                          />
                          <span className="rounded-full bg-white/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-cyan-100">
                            {item.provider}
                          </span>
                        </div>
                        <p className="mt-4 text-sm font-semibold text-slate-100">{item.display_name}</p>
                        <p className="text-[11px] text-slate-400">{item.service}{item.region ? ` — ${item.region}` : ""}</p>
                        <p className="mt-3 text-lg font-bold text-cyan-200">{item.currency} {Number(item.price).toFixed(4)}</p>
                        <p className="text-[11px] text-slate-400">por {item.unit} · fonte: {item.source}</p>
                        <div className="mt-4 flex items-center gap-2">
                          <label className="text-[10px] text-slate-400">
                            {/hrs|hour/i.test(item.unit || "") ? "Horas mensais" : "Uso mensal"}
                            <input
                              type="number"
                              min="0"
                              step="0.1"
                              value={usage[item.id] ?? defaultUsage(item.unit)}
                              onChange={(event) => setUsage((current) => ({ ...current, [item.id]: Number(event.target.value) }))}
                              className="ml-2 w-20 rounded-xl border border-white/10 bg-slate-900 px-2 py-1 text-xs text-slate-100"
                            />
                          </label>
                          <span className="ml-auto text-xs font-semibold text-emerald-300">
                            ≈ USD {(Number(item.price) * Number(usage[item.id] ?? defaultUsage(item.unit))).toFixed(2)}/mês
                          </span>
                        </div>
                      </article>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function ExecutiveSummary({ summary }) {
  if (!summary) return null;
  return (
    <section className="rounded-3xl border border-cyan-300/25 bg-cyan-950/15 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-300">Resumo executivo</p>
          <h3 className="mt-2 text-xl font-bold text-white">O que o agente entendeu</h3>
        </div>
        <span className="rounded-full border border-white/10 bg-slate-950/40 px-3 py-2 text-[11px] text-slate-300">
          Escala: {summary.scale || "a definir"}
        </span>
      </div>
      <p className="mt-5 whitespace-pre-wrap text-sm leading-7 text-slate-200">{summary.interpretation}</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Objetivos identificados</p>
          <ul className="mt-3 space-y-2 text-sm text-slate-300">
            {(summary.objectives || []).map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-cyan-300">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Requisitos de qualidade</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(summary.non_functional_requirements || []).map((item) => (
              <span key={item} className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-200">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
      <p className="mt-5 border-t border-white/10 pt-3 text-xs text-slate-400">{summary.confidence_note}</p>
    </section>
  );
}

function ServiceDecisions({ decisions }) {
  if (!decisions?.length) return null;
  return (
    <section>
      <div className="mb-4">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet-300">Decisões por serviço</p>
        <h3 className="mt-1 text-xl font-bold">Por que cada bloco existe</h3>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {decisions.map((item) => (
          <article key={item.service} className="rounded-3xl border border-white/10 bg-slate-950/50 p-5">
            <p className="font-semibold text-violet-200">{item.service}</p>
            <p className="mt-2 text-sm text-slate-200">{item.purpose}</p>
            <p className="mt-3 text-xs leading-6 text-slate-400">
              <strong className="text-slate-200">Motivo:</strong> {item.why}
            </p>
            <p className="mt-2 text-xs leading-6 text-slate-400">
              <strong className="text-slate-300">Alternativa:</strong> {item.alternative}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

function InsightPanels({ tradeoffs, risks, plan }) {
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-3xl border border-amber-300/20 bg-amber-950/10 p-5">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-amber-300">Trade-offs</p>
        <div className="mt-4 space-y-3">
          {(tradeoffs || []).map((item) => (
            <details key={item.decision} className="rounded-2xl border border-white/10 bg-slate-950/40 p-3">
              <summary className="cursor-pointer text-sm font-semibold text-slate-200">{item.decision}</summary>
              <p className="mt-2 text-xs leading-5 text-emerald-200">Benefício: {item.benefit}</p>
              <p className="mt-1 text-xs leading-5 text-amber-200">Custo: {item.cost}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">Quando: {item.when}</p>
            </details>
          ))}
        </div>
      </div>
      <div className="rounded-3xl border border-rose-300/20 bg-rose-950/10 p-5">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-rose-300">Riscos para validar</p>
        <div className="mt-4 space-y-3">
          {(risks || []).map((item) => (
            <article key={item.title} className="rounded-2xl border border-white/10 bg-slate-950/40 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-slate-200">{item.title}</p>
                <span className="text-[10px] uppercase text-rose-300">{item.severity}</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-400">{item.detail}</p>
              <p className="mt-2 text-xs leading-5 text-emerald-200">Mitigação: {item.mitigation}</p>
            </article>
          ))}
        </div>
      </div>
      <div className="rounded-3xl border border-emerald-300/20 bg-emerald-950/10 p-5">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-300">Plano inicial</p>
        <div className="mt-4 space-y-3">
          {(plan || []).map((item, index) => (
            <article key={item.step} className="flex gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-300/15 text-xs font-bold text-emerald-200">{index + 1}</span>
              <div>
                <p className="text-sm font-semibold text-slate-200">{item.step}</p>
                <p className="mt-1 text-xs leading-5 text-slate-400">{item.description}</p>
                {item.owner ? <p className="mt-1 text-[10px] uppercase text-emerald-300/70">{item.owner}</p> : null}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function BlueprintSections({ analysis }) {
  const discovery = analysis.discovery || {};
  const platform = analysis.platform_blueprint || {};
  const delivery = analysis.delivery_estimate || {};

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <details open className="rounded-3xl border border-cyan-300/20 bg-cyan-950/15 p-5">
        <summary className="cursor-pointer text-lg font-bold text-cyan-200">Descoberta e lacunas</summary>
        <p className="mt-3 text-xs text-slate-400">O que precisa ser confirmado antes de transformar a base em compromisso de execução.</p>
        <div className="mt-4 space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Perguntas de negócio</p>
            <ul className="mt-2 space-y-1 text-xs text-slate-300">
              {(discovery.business_questions || []).map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Lacunas</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {(discovery.gaps || []).map((item) => (
                <span key={item} className="rounded-full bg-amber-300/10 px-3 py-1 text-[11px] text-amber-200">
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </details>
      <details className="rounded-3xl border border-violet-300/20 bg-violet-950/15 p-5">
        <summary className="cursor-pointer text-lg font-bold text-violet-200">Alternativas arquiteturais</summary>
        <div className="mt-4 space-y-3">
          {(analysis.architecture_options || []).map((item) => (
            <article key={item.name} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-slate-100">{item.name}</p>
                <span className="text-[10px] uppercase text-violet-300">{item.fit}</span>
              </div>
              <p className="mt-2 text-xs text-emerald-200">Vantagem: {item.benefit}</p>
              <p className="mt-1 text-xs text-amber-200">Trade-off: {item.tradeoff}</p>
            </article>
          ))}
        </div>
      </details>
      <details className="rounded-3xl border border-rose-300/20 bg-rose-950/15 p-5">
        <summary className="cursor-pointer text-lg font-bold text-rose-200">Segurança por padrão</summary>
        <div className="mt-4 grid gap-3">
          {(analysis.security_baseline || []).map((item) => (
            <article key={item.area} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <p className="text-sm font-semibold text-rose-200">{item.area}</p>
              <p className="mt-1 text-xs leading-5 text-slate-300">{item.baseline}</p>
            </article>
          ))}
        </div>
      </details>
      <details className="rounded-3xl border border-blue-300/20 bg-blue-950/15 p-5">
        <summary className="cursor-pointer text-lg font-bold text-blue-200">Plataforma, dados e APIs</summary>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {Object.entries(platform).map(([name, items]) => (
            <div key={name}>
              <p className="text-xs font-semibold uppercase tracking-wider text-blue-300">{name}</p>
              <ul className="mt-2 space-y-1 text-xs text-slate-300">
                {(items || []).map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </details>
      <details className="rounded-3xl border border-emerald-300/20 bg-emerald-950/15 p-5">
        <summary className="cursor-pointer text-lg font-bold text-emerald-200">Entrega, equipe e sustentação</summary>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-300">Equipe de referência</p>
            <div className="mt-2 space-y-2 text-xs text-slate-300">
              {(delivery.team || []).map((item) => (
                <p key={item.role}>
                  <strong>{item.role}</strong> · {item.count} · {item.phase}
                </p>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-300">Fases</p>
            <ol className="mt-2 space-y-1 text-xs text-slate-300">
              {(delivery.timeline || []).map((item, index) => (
                <li key={item}>{index + 1}. {item}</li>
              ))}
            </ol>
          </div>
        </div>
        <p className="mt-4 border-t border-white/10 pt-3 text-xs text-slate-400">{delivery.cost_note}</p>
        <ul className="mt-3 space-y-1 text-xs text-slate-300">
          {(analysis.support_model || []).map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </details>
      <details className="rounded-3xl border border-amber-300/20 bg-amber-950/15 p-5">
        <summary className="cursor-pointer text-lg font-bold text-amber-200">Próximos passos e princípios</summary>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-300">Próximos passos</p>
            <ol className="mt-2 space-y-1 text-xs text-slate-300">
              {(analysis.next_steps || []).map((item, index) => (
                <li key={item}>{index + 1}. {item}</li>
              ))}
            </ol>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-300">Princípios</p>
            <ul className="mt-2 space-y-1 text-xs text-slate-300">
              {(analysis.engineering_principles || []).map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </div>
        </div>
      </details>
    </section>
  );
}

function RefinementActions({ onRefine, busy }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-300">Próxima pergunta do agente</p>
          <p className="mt-1 text-sm text-slate-300">Refine a base sem começar de novo.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {["Reduzir custos", "Aumentar disponibilidade", "Priorizar segurança", "Escalar para mais usuários"].map((action) => (
            <button
              key={action}
              disabled={busy}
              onClick={() => onRefine(action)}
              className="rounded-2xl border border-white/15 px-4 py-3 text-xs text-slate-200 transition hover:border-cyan-300/60 hover:bg-cyan-300/10 disabled:opacity-50"
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function ArchitectureResults({ analysis, onRefine, busy }) {
  const modules = analysis?.architecture?.modules || [];
  const costs = analysis?.costs?.monthly_estimate || {};
  const details = analysis?.costs?.providers || {};
  const ranking = analysis?.ranking || {};
  const referenceProvider = analysis?.provider || ranking.recommended_provider || "-";
  const ai = analysis?.ai || analysis?.architecture?.ai || {};
  const terraform = analysis?.terraform?.modules || {};

  return (
    <section className="space-y-8">
      <ExecutiveSummary summary={analysis.executive_summary} />
      <BlueprintSections analysis={analysis} />
      <div className="flex flex-wrap gap-3">
        <button onClick={() => exportAnalysis(analysis, "md")} className="rounded-2xl border border-cyan-300/40 bg-cyan-300/10 px-4 py-2 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-300/15">
          Exportar documentação .md
        </button>
        <button onClick={() => exportAnalysis(analysis, "json")} className="rounded-2xl border border-white/15 bg-slate-950/60 px-4 py-2 text-xs text-slate-200 transition hover:border-cyan-300/40">
          Exportar dados .json
        </button>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className={card}>
          <h2 className="text-lg font-semibold">Infraestrutura de referência</h2>
          <p className="mt-1 text-sm text-slate-300">Blocos iniciais para orientar implementação e evolução.</p>
          <div className="mt-5 space-y-4">
            {Object.entries(terraform).map(([name, script]) => (
              <details key={name} className="rounded-3xl border border-white/10 bg-slate-950/50 p-4">
                <summary className="cursor-pointer text-sm font-semibold text-cyan-200">{name}</summary>
                <pre className="mt-3 overflow-x-auto rounded-2xl bg-slate-950/70 p-4 text-[11px] leading-6 text-slate-200">{script}</pre>
              </details>
            ))}
          </div>
        </div>
        <div className={card}>
          <h2 className="text-lg font-semibold">Componentes e custos</h2>
          {ai?.brief && (
            <div className="mt-4 rounded-3xl border border-white/10 bg-slate-950/55 p-4">
              <p className="text-sm font-semibold text-cyan-200">Análise arquitetural da IA</p>
              <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-slate-400">
                {ai.provider || "deterministic"} · {ai.model || "fallback"} · {ai.used_fallback ? "fundação determinística" : "análise gerada"}
              </p>
              <p className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-200">{ai.brief}</p>
            </div>
          )}
          {ranking.items?.length > 0 && (
            <div className="mt-4 rounded-3xl border border-cyan-400/30 bg-cyan-950/20 p-4">
              <p className="text-sm font-semibold text-cyan-200">Comparativo de referência</p>
              <p className="mt-1 text-[11px] text-slate-300">
                Cloud de referência: <span className="font-semibold text-emerald-300">{referenceProvider.toUpperCase()}</span>
              </p>
              <div className="mt-3 space-y-2">
                {ranking.items.map((item) => (
                  <p key={item.provider} className="text-[11px] text-slate-300">
                    {item.provider.toUpperCase()} · score {Number(item.score).toFixed(3)} · USD {formatMoney(item.cost_mid_usd_month)}
                  </p>
                ))}
              </div>
            </div>
          )}
          <div className="mt-4 space-y-4">
            {modules.map((module) => (
              <article key={module.name} className="rounded-3xl border border-white/10 bg-slate-950/50 p-4">
                <p className="text-sm font-semibold text-cyan-200">{module.name}</p>
                <p className="mt-1 text-xs text-slate-300">{module.role}</p>
                <p className="mt-2 text-[11px] text-slate-400"><span className="text-slate-200">Calls:</span> {module.calls}</p>
                <p className="text-[11px] text-slate-400"><span className="text-slate-200">Returns:</span> {module.returns}</p>
              </article>
            ))}
            {Object.entries(costs).map(([provider, values]) => {
              const detail = details[provider] || {};
              const total = Number(values.total ?? ((Number(values.min) + Number(values.max)) / 2));
              return (
                <article key={provider} className="rounded-3xl border border-white/10 bg-slate-950/40 p-4">
                  <p className="text-xs font-semibold text-cyan-200">
                    {provider.toUpperCase()}: USD {formatMoney(total)} <span className="text-slate-400">({formatMoney(values.min)} - {formatMoney(values.max)})</span>
                  </p>
                  <p className="mt-2 text-[11px] text-slate-400">Fonte: {(detail.sources || []).join(", ") || "catálogo"}</p>
                  {(detail.components || []).slice(0, 4).map((component) => (
                    <p key={component.component} className="mt-2 text-[11px] text-slate-300">
                      {component.component}: USD {formatMoney(component.monthly_cost)}
                    </p>
                  ))}
                </article>
              );
            })}
          </div>
        </div>
      </div>
      <ServiceDecisions decisions={analysis.service_decisions} />
      <InsightPanels tradeoffs={analysis.tradeoffs} risks={analysis.risks} plan={analysis.implementation_plan} />
      <RefinementActions onRefine={onRefine} busy={busy} />
    </section>
  );
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [session, setSession] = useState(null);
  const [draft, setDraft] = useState(null);
  const [bases, setBases] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [provider, setProvider] = useState("aws");
  const [status, setStatus] = useState("");
  const [isError, setIsError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [lastRequest, setLastRequest] = useState(null);

  const notify = useCallback((message, error = false) => {
    setStatus(message);
    setIsError(error);
  }, []);

  useEffect(() => {
    const url = new URL(window.location.href);
    const urlToken = url.searchParams.get("token");
    if (urlToken) {
      localStorage.setItem(AUTH_TOKEN_KEY, urlToken);
      setToken(urlToken);
      url.searchParams.delete("token");
      window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    }
    const pending = url.searchParams.get("pending");
    const authError = url.searchParams.get("auth_error");
    if (pending) notify("Acesso pendente. Aguarde aprovação do administrador.", true);
    if (authError) notify(`Falha no login GitHub: ${authError}`, true);
  }, [notify]);

  useEffect(() => {
    if (!token) {
      setBases([]);
      return;
    }

    const loadBases = async () => {
      try {
        const response = await fetch(apiUrl("/api/demands"), { headers: authHeaders(token) });
        if (!response.ok) {
          setBases([]);
          return;
        }
        setBases(await response.json());
      } catch {
        setBases([]);
      }
    };

    loadBases();
  }, [token]);

  useEffect(() => {
    const load = async () => {
      try {
        const catalogRequest = fetch(apiUrl("/api/catalog/items?provider=all&limit=500"));
        const sessionRequest = token ? fetch(apiUrl("/api/auth/session"), { headers: authHeaders(token) }) : Promise.resolve(null);
        const [catalogResponse, sessionResponse] = await Promise.all([catalogRequest, sessionRequest]);

        if (catalogResponse.ok) setCatalog(await catalogResponse.json());
        if (sessionResponse?.ok) {
          setSession(await sessionResponse.json());
        } else if (token) {
          localStorage.removeItem(AUTH_TOKEN_KEY);
          setToken(null);
          setSession(null);
          setBases([]);
          setAnalysis(null);
          setDraft(null);
          setLastRequest(null);
        }
      } catch {
        notify("Falha ao carregar dados da plataforma.", true);
      }
    };

    load();
  }, [token, notify]);

  const login = async () => {
    const response = await fetch(apiUrl("/api/auth/github/url"));
    if (response.ok) {
      const data = await response.json();
      window.location.href = data.auth_url;
      return;
    }
    notify("GitHub OAuth não configurado no servidor.", true);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
    setSession(null);
    setBases([]);
    setAnalysis(null);
    setDraft(null);
    setLastRequest(null);
    notify("Sessão encerrada.");
  };

  const syncCatalog = async () => {
    if (!token) return notify("Faça login com GitHub para sincronizar o catálogo.", true);
    notify("Sincronizando catálogo cloud...");
    setBusy(true);

    try {
      const response = await fetch(apiUrl("/api/catalog/sync"), {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ providers, limit_per_provider: 100 }),
      });
      if (!response.ok) throw new Error();
      notify("Catálogo sincronizado.");
      const items = await fetch(apiUrl("/api/catalog/items?provider=all&limit=500"));
      if (items.ok) setCatalog(await items.json());
    } catch {
      notify("Falha na sincronização do catálogo.", true);
    } finally {
      setBusy(false);
    }
  };

  const openBase = async (base) => {
    trackEvent(token, "base_open_clicked", { demand_id: base.id });
    setBusy(true);
    try {
      const response = await fetch(apiUrl(`/api/demands/${base.id}/analysis`), { headers: authHeaders(token) });
      if (!response.ok) {
        if (response.status === 404 && !base.has_analysis) {
          setDraft({ title: base.title, rawInput: base.raw_input });
          document.getElementById("demand-form")?.scrollIntoView({ behavior: "smooth", block: "center" });
          notify("Rascunho carregado no formulário. Construa a base para gerar a arquitetura.");
          return;
        }
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `Não foi possível abrir esta base (HTTP ${response.status}).`);
      }
      const saved = await response.json();
      setAnalysis(saved);
      setDraft({ title: base.title, rawInput: base.raw_input });
      setProvider(saved.provider || base.provider_selected || "aws");
      setLastRequest({ title: base.title, rawInput: base.raw_input });
      notify("Base arquitetural carregada.");
    } catch (error) {
      notify(error.message, true);
    } finally {
      setBusy(false);
    }
  };

  const deleteBase = async (base) => {
    if (!window.confirm(`Apagar a base "${base.title}"?`)) return;
    setBusy(true);
    try {
      const response = await fetch(apiUrl(`/api/demands/${base.id}`), {
        method: "DELETE",
        headers: authHeaders(token),
      });
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || `Não foi possível apagar esta base (HTTP ${response.status}).`);
      }
      setBases((current) => current.filter((item) => item.id !== base.id));
      if (analysis?.demand_id === base.id) setAnalysis(null);
      notify("Base apagada. Você pode criar outra.");
    } catch (error) {
      notify(error.message, true);
    } finally {
      setBusy(false);
    }
  };

  const orchestrate = async ({ title, rawInput }) => {
    trackEvent(token, "architecture_build_clicked", { provider, input_type: "text" });
    if (!token) return notify("Faça login com GitHub antes de orquestrar.", true);
    setLastRequest({ title, rawInput });
    setBusy(true);
    notify("Criando demanda...");

    try {
      const demandResponse = await fetch(apiUrl("/api/demands"), {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ title, raw_input: rawInput, input_type: "text" }),
      });
      if (!demandResponse.ok) {
        const errorBody = await demandResponse.json().catch(() => ({}));
        throw new Error(errorBody.detail || "Falha ao criar demanda.");
      }
      const demand = await demandResponse.json();
      notify("Executando orquestração...");
      const response = await fetch(apiUrl(`/api/demands/${demand.id}/orchestrate`), {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ provider }),
      });
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || "Falha na orquestração.");
      }
      const generated = await response.json();
      setAnalysis(generated);
      setBases((current) => [{ ...demand, provider_selected: generated.provider, has_analysis: true }, ...current.filter((item) => item.id !== demand.id)]);
      notify("Base arquitetural pronta para validação.");
    } catch (error) {
      notify(error.message, true);
    } finally {
      setBusy(false);
    }
  };

  const refine = (instruction) => {
    if (!lastRequest) return notify("Execute uma análise antes de refinar a base.", true);
    orchestrate({ title: lastRequest.title, rawInput: `${lastRequest.rawInput}\n\nRefinamento solicitado: ${instruction}` });
  };

  return (
    <>
      <BusyOverlay busy={busy} />
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_12%_18%,rgba(59,130,246,0.22),transparent_35%),radial-gradient(circle_at_88%_8%,rgba(139,92,246,0.18),transparent_30%),linear-gradient(180deg,#020617,#0b1020_52%,#04070f)]" />
      <Header session={session} onLogout={logout} />
      <main className="mx-auto max-w-7xl px-4 pb-24 pt-8 sm:px-6 sm:pt-10">
        <Hero />
        <ProductSteps />
        <section id="workspace" className="mt-16 space-y-8">
          <SavedBases bases={bases} onOpen={openBase} onDelete={deleteBase} busy={busy} />
          <div className={card}>
            <h3 className="text-xl font-semibold">Workspace CloudHelm</h3>
            <p className="mt-2 text-sm text-slate-300">Descreva o contexto da sua solução e receba uma base arquitetural inicial com custos e recomendações.</p>
          </div>
          <DemandForm provider={provider} setProvider={setProvider} onSubmit={orchestrate} onLogin={login} busy={busy} session={session} draft={draft} />
          <QuickStatus status={status} isError={isError} />
          {analysis && <ArchitectureResults analysis={analysis} onRefine={refine} busy={busy} />}
          <Catalog catalog={catalog} onSync={syncCatalog} token={token} />
        </section>
      </main>
    </>
  );
}
