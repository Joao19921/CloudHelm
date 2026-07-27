# Frontend responsivo e performance

## Contexto

A interface principal do CloudHelm e HTML/CSS/JavaScript estatico, publicada no GitHub Pages e tambem servida pelo FastAPI para acesso direto ao backend.

## Decisoes

- Mantemos a stack estatica por enquanto para evitar novo build pipeline e dependencias de runtime.
- `frontend/styles.css` concentra ajustes responsivos sem reescrever a UI inteira.
- O layout usa largura fluida controlada por `--shell-max`, com breakpoints para mobile, 2.5K, 4K e 8K.
- Resultados pesados usam `content-visibility: auto` para reduzir custo de renderizacao fora da viewport.
- Campo de busca do catalogo usa CSS responsivo e esta preparado para debounce quando o frontend evoluir.

## Breakpoints principais

- Ate 768px: header quebra linha, cards reduzem padding e controles ganham area minima de toque.
- A partir de 1536px: catalogo expande para 4 colunas.
- A partir de 2560px: shell cresce para 2200px e o workspace ganha proporcao otimizada.
- A partir de 3840px: shell cresce para 3000px e catalogo usa 6 colunas.
- A partir de 7000px: shell cresce para 4200px e catalogo usa 8 colunas.

## Observacao sobre React

React ainda nao faz parte da stack atual. Para aplicar padroes equivalentes de performance sem migracao, a UI evita estado global desnecessario, mantem DOM simples e usa CSS nativo para responsividade em vez de adicionar runtime ou bundle novo.
