# APIs de Cálculo de Custos — AWS, Azure, Google Cloud e OCI

Documentação de referência das APIs oficiais de preços/custos de cada provedor de nuvem, para uso em ferramentas de comparação e estimativa de custos de aplicações.

---

## Resumo comparativo

| Provedor | Endpoint | Autenticação | Escopo dos dados |
|---|---|---|---|
| AWS | Price List Query/Bulk API | IAM | Preço de lista público (SKU) |
| Azure | `prices.azure.com/api/retail/prices` | Nenhuma | Preço de varejo público |
| GCP | `cloudbilling.googleapis.com` | API key | Preço público + Pricing API traz preços de contrato |
| OCI | `apexapps.oracle.com/pls/apex/cetools/api/v1/products/` | Nenhuma | Preço PAYG global |

---

## AWS — Price List API

Duas versões disponíveis:
- **Bulk API**: baixa arquivos JSON/CSV completos por serviço e região.
- **Query API**: consultas filtradas via SDK/CLI, permite buscar por atributos de produto e retorna preços no nível de SKU.

Existe também a **AWS Pricing Calculator API**, que permite criar estimativas programaticamente para uso planejado na nuvem, modelando Savings Plans, Reserved Instances e descontos.

- Documentação: `docs.aws.amazon.com/aws-cost-management/latest/APIReference/`
- Endpoint da Pricing API disponível somente em `us-east-1` e `ap-south-1` (independente da região dos preços consultados).

### Configuração da conta AWS

**1. Permissão IAM** — crie/anexe uma policy com:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:DescribeServices",
        "pricing:GetAttributeValues"
      ],
      "Resource": "*"
    }
  ]
}
```

**2. Credenciais** — duas formas comuns:

- AWS CLI configurado (mais simples):
  ```bash
  aws configure
  ```
- Variáveis de ambiente (bom para CI/CD ou containers):
  ```bash
  export AWS_ACCESS_KEY_ID=sua_access_key
  export AWS_SECRET_ACCESS_KEY=sua_secret_key
  ```

**3. Teste rápido**
```bash
pip install boto3
aws sts get-caller-identity   # confirma que as credenciais estão funcionando
```

---

## Azure — Retail Prices API

Dá acesso não autenticado para obter preços de varejo de todos os serviços Azure, útil para comparar preços entre regiões e SKUs.

- Endpoint: `https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview`
- Suporta filtros OData, ex: `$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'eastus'`
- Se você tem contrato empresarial (Enterprise Agreement), use as APIs de Cost Management/Consumption em vez desta — a Retail Prices API só traz preço público.

---

## Google Cloud — Cloud Billing Catalog / Pricing API

- **Catalog API**: retorna lista de todos os serviços públicos e SKUs, com descrição legível, preço público, regiões disponíveis e dados de categorização.
- **Pricing API** (mais nova): vai além, trazendo preços customizados de contrato específicos da sua conta de billing, além dos preços públicos.
- Endpoint: `cloudbilling.googleapis.com`
- Requer API key com a Cloud Billing API habilitada no console GCP.

---

## OCI — Oracle Cloud Price List API

Oracle disponibiliza uma forma oficial de consultar os preços de lista dos serviços, permitindo buscar todos os serviços ou um SKU específico e especificar a moeda desejada.

- Endpoint: `https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/`
- Não requer autenticação — API pública que retorna todos os preços de produtos OCI em JSON.
- Documentação: `docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup_topic-Estimating_Costs.htm`
- Limitações: só mostra preço Pay-As-You-Go — descontos de uso comprometido (anual/3 anos), regiões governamentais/soberanas e preços negociados de contratos empresariais exigem contato com vendas da Oracle.

---

## Script de referência

O arquivo `cloud_pricing_apis.py` implementa funções para consultar as quatro APIs e normalizar os resultados em um formato comum (`NormalizedPrice`), com campos: `provider`, `service`, `sku_or_meter`, `region`, `unit`, `price_usd`, `raw`.

Isso permite juntar os preços das quatro nuvens numa única lista, DataFrame do pandas, ou exportar para CSV/planilha para comparação lado a lado.
