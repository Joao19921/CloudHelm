# Testing Guide

O CloudHelm utiliza o **pytest** para automação de testes no backend, cobrindo saúde da API, validação de regras de negócios (unidade) e integração.

## Estrutura de Testes

A base de testes está localizada no diretório `api/tests/`:

- `conftest.py`: Contém as **fixtures** globais, como o Banco de Dados em memória (SQLite) e o Client de disparo (TestClient), isolando o ambiente.
- `api/test_health.py`: Teste de fumaça (Smoke Test - P0) que assegura a integridade das rotas bases.
- `api/test_auth.py`: Regressão dos fluxos de registro e de autenticação, validando permissões, status codes e dados armazenados.

## Executando os Testes Localmente

Para rodar a suite de testes localmente na sua máquina:

1. Certifique-se de que seu ambiente virtual do Python está ativado (ex: `.venv/Scripts/Activate.ps1`).
2. Navegue para o diretório `api`:
   ```bash
   cd api
   ```
3. Execute o `pytest`. Pode adicionar a flag `-v` para visualização mais detalhada:
   ```bash
   python -m pytest -v
   ```

## Integração Contínua (CI/CD)

A integração contínua está implementada nativamente via **GitHub Actions**. O arquivo de configuração se encontra em `.github/workflows/backend-tests.yml`.

Sempre que alterações forem enviadas (via **Push** ou **Pull Request**) para o branch `main`, a esteira do GitHub irá:
1. Instalar o Python 3.12 em uma máquina recém-criada no Ubuntu.
2. Instalar todas as dependências do `api/requirements.txt`.
3. Disparar o `pytest`.
4. Em caso de falha nos testes, o Action é apontado como "Failed", prevenindo a introdução de regressões no ambiente principal.

## Como Escrever os Próximos Testes (AAA Pattern)

*   **Arrange**: Configure os dados necessários (utilizando o banco de dados em memória `db_session` onde aplicável).
*   **Act**: Chame o endpoint utilizando o `client`.
*   **Assert**: Valide as saídas que o usuário experenciaria ou os registros no banco, não confie no código interno da função testada.
