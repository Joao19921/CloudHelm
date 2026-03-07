#!/usr/bin/env bash
set -euo pipefail

echo "CloudHelm - Verificacao de pre-requisitos"
echo "-----------------------------------------"

check_cmd() {
  local name="$1"
  local version_cmd="$2"

  if ! command -v "$name" >/dev/null 2>&1; then
    echo "[FAIL] $name nao encontrado no PATH."
    return 1
  fi

  local version
  version="$(eval "$version_cmd" 2>/dev/null || true)"
  echo "[ OK ] $name encontrado -> ${version:-versao indisponivel}"
  return 0
}

git_ok=0
docker_ok=0
compose_ok=0
python_ok=0

check_cmd "git" "git --version" || git_ok=1
check_cmd "docker" "docker --version" || docker_ok=1

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    echo "[ OK ] docker compose encontrado -> $(docker compose version)"
  else
    echo "[FAIL] docker compose nao disponivel."
    compose_ok=1
  fi
else
  compose_ok=1
fi

check_cmd "python3" "python3 --version" || python_ok=1

echo
echo "Portas recomendadas:"
echo "- 8000 (CloudHelm App)"
echo "- 3307 (MySQL local)"
echo

if [[ "$git_ok" -eq 0 && "$docker_ok" -eq 0 && "$compose_ok" -eq 0 ]]; then
  echo "Ambiente pronto para execucao com Docker."
  echo "Proximo passo: docker compose up --build"
else
  echo "Ambiente incompleto para Docker. Instale os itens em [FAIL]."
fi

if [[ "$python_ok" -eq 0 ]]; then
  echo "Python disponivel para modo sem Docker e jobs."
else
  echo "Python ausente: necessario para modo sem Docker e scripts de job."
fi
