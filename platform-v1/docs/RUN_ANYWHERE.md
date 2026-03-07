# CloudHelm V1.1 - Requisitos e Execucao

Este guia descreve tudo que qualquer pessoa precisa para rodar o projeto localmente.

## 1) Requisitos obrigatorios

- Git 2.40+
- Docker Desktop 4.29+ (com Docker Compose v2 habilitado)
- 4 GB RAM livres para containers
- 2 vCPUs livres
- 5 GB de disco
- Portas livres:
  - `8000` (app)
  - `3307` (MySQL local mapeado)

## 2) Requisitos opcionais (modo sem Docker)

- Python 3.12+
- `pip` atualizado

## 3) Clonar e preparar

```bash
git clone https://github.com/Joao19921/CloudHelm.git
cd CloudHelm/platform-v1
cp .env.example .env
```

No Windows PowerShell:

```powershell
git clone https://github.com/Joao19921/CloudHelm.git
cd CloudHelm/platform-v1
Copy-Item .env.example .env
```

## 3.1) Checagem automatica de pre-requisitos

Windows:

```powershell
.\scripts\check-prereqs.ps1
```

Linux/macOS:

```bash
chmod +x ./scripts/check-prereqs.sh
./scripts/check-prereqs.sh
```

## 4) Variaveis de ambiente

Arquivo: `.env`

Obrigatorias:

- `APP_NAME=CloudHelm`
- `SECRET_KEY=<defina-um-segredo-forte>`
- `ACCESS_TOKEN_EXPIRE_MINUTES=120`
- `DATABASE_URL=mysql+pymysql://antigravity:antigravity@db:3306/antigravity`

Opcionais:

- `OPENAI_API_KEY=` para transcricao real de audio
- `TRANSCRIBE_MODEL=whisper-1`

## 5) Subir com Docker (recomendado)

```bash
docker compose up --build
```

Acessar:

- UI: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## 6) Fluxo funcional minimo apos subir

1. Registrar usuario.
2. Fazer login.
3. (Opcional) Sincronizar catalogo cloud em `Catalogo Cloud Providers`.
4. Enviar demanda em texto ou audio.
5. Se audio, usar `Transcrever Audio Automaticamente`.
6. Orquestrar com provider especifico ou `Auto (Ranking)`.

## 7) Rodar sem Docker (fallback)

Dentro de `platform-v1/backend`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

No Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Se for usar SQLite no fallback, configure no `.env`:

`DATABASE_URL=sqlite:///./antigravity.db`

## 8) Job de catalogo cloud

Script:

`backend/jobs/alimentador.py`

Execucao manual:

```bash
python jobs/alimentador.py
```

Agendamento Linux (diario, meia-noite):

```bash
0 0 * * * /usr/bin/python3 /caminho/CloudHelm/platform-v1/backend/jobs/alimentador.py
```

## 9) APIs principais

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/demands`
- `POST /api/demands/transcribe`
- `POST /api/demands/{id}/orchestrate`
- `GET /api/catalog/items`
- `POST /api/catalog/sync`
- `GET /api/catalog/summary`

## 10) Troubleshooting rapido

- Erro `python not found`:
  - Instalar Python 3.12 e adicionar ao PATH.
- Erro `docker not found`:
  - Instalar Docker Desktop e reiniciar terminal.
- Porta 8000 ocupada:
  - Trocar mapeamento no `docker-compose.yml` para `8001:8000`.
- Falha na transcricao:
  - Sem `OPENAI_API_KEY`, a plataforma usa fallback local (esperado).
- Falha no sync de catalogo:
  - Verificar conectividade externa para APIs publicas.

## 11) Checklist de pronto para rodar

- [ ] Docker Desktop instalado
- [ ] `.env` criado
- [ ] `docker compose up --build` executado sem erro
- [ ] `GET /health` retorna `{"status":"ok"}`
- [ ] Login funcionando
- [ ] Orquestracao funcionando

## 12) Publicar no GitHub (CloudHelm)

Remoto do projeto:

`https://github.com/Joao19921/CloudHelm.git`

Comandos sugeridos:

```bash
git remote add cloudhelm https://github.com/Joao19921/CloudHelm.git
git add platform-v1
git commit -m "feat: CloudHelm v1.1 web platform"
git push cloudhelm HEAD:main
```
