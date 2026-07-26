# Arquitetura CloudHelm

Este diretório contém os artefatos arquiteturais da plataforma no formato C4, UML e BPMN.

## Visão dos artefatos

| Artefato | Finalidade | Fonte |
| --- | --- | --- |
| C4 | Contexto, contêineres e componentes principais | [C4.md](C4.md) |
| Sequência | Login, estimativa e orquestração de demanda | [SEQUENCE.md](SEQUENCE.md) |
| Infraestrutura | Topologia atualmente publicada e blueprint provisionável | [INFRASTRUCTURE.md](INFRASTRUCTURE.md) |
| BPMN | Processo de análise e recomendação de infraestrutura | [BPMN.md](BPMN.md) |
| BPMN 2.0 | Arquivo importável em ferramentas BPMN | [cloudhelm-demand.bpmn](cloudhelm-demand.bpmn) |

## Convenções

- Produção atual é identificada como **Current State**: GitHub Pages, Render e Supabase.
- AWS, Azure e GCP em Kubernetes são **Target State**: representam os módulos Terraform/Ansible disponíveis para evolução, não o deployment atual.
- O backend é um monólito modular FastAPI; os módulos internos não são microsserviços independentes.
- Integrações de IA são opcionais. Na ausência de credenciais ou em caso de erro, a orquestração usa fallback determinístico.

## Renderização

- PlantUML: renderize blocos `plantuml` com PlantUML/C4-PlantUML.
- Mermaid: renderização nativa no GitHub e em editores compatíveis.
- BPMN: importe `cloudhelm-demand.bpmn` em uma ferramenta compatível com BPMN 2.0.
