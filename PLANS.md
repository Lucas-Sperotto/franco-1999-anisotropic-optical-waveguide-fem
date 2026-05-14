# PLANS.md

## Estado atual

- documentação do artigo traduzida e revisada em `docs/`
- casos de teste já resumidos e organizados
- estratégia do repositório definida
- implementação ainda não iniciada de forma estruturada

## Fase 1 — infraestrutura

Critérios de aceite:

- criar estrutura base do repositório
- criar `CMakeLists.txt`
- criar `scripts/build.sh`
- criar `scripts/run_case.sh`
- definir convenção de `cases/` e `out/`

## Fase 2 — geometria básica

Critérios de aceite:

- implementar triângulo linear P1
- calcular área
- calcular gradientes das funções de forma
- adicionar teste simples

## Fase 3 — solver mínimo

Critérios de aceite:

- montar problema generalizado
- resolver autovalores
- exportar $n_eff$
- rodar caso simples

## Fase 4 — validação progressiva

Critérios de aceite:

- caso 1 funcional
- caso 2 funcional
- depois avançar para os demais


Caso 1 resolvido: o eigensolver Jacobi usava `max_iterations=200` (insuficiente para malhas
com ~378 DOFs livres). Corrigido para `max(200, 5*n²)`. Com a malha farfield e V=1.0,
n_eff²=2.140 (entre 2.0449 e 2.25). Discrepância residual em B vs referência é
atribuída à assimetria da geometria (cover≠substrate) — questão separada.
