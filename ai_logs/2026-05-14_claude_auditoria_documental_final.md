# Auditoria Claude — Organização Científica e Documental

**Data:** 2026-05-14
**Auditor:** Claude (Sonnet 4.6)
**Objetivo:** Avaliar a coerência entre a documentação, a implementação e os resultados do projeto de reprodução do artigo Franco et al. (1999), "Finite Element Analysis of Anisotropic Optical Waveguide with Arbitrary Index Profile".

---

## 1. Diagnóstico Geral

O projeto está em um estado **substancialmente mais avançado** do que o descrito na auditoria anterior (`2024-05-21_gemini_auditoria_final.md`). As oito tarefas da lista `prompts.md` foram todas concluídas e comitadas. A infraestrutura é robusta, o solver está correto para os casos isotrópicos já exercitados, e a documentação em `docs/` é de alta qualidade e tem servido como especificação executável para a implementação.

Os problemas remanescentes são de dois tipos:

1. **Documentação desatualizada** (`docs/03`): a tabela de comparação do Caso 1 reflete resultados pré-correção do Jacobi (todos B negativos). Esses valores são enganosos para qualquer leitor ou revisor que não conheça o histórico da sessão.

2. **Lacunas de execução** (Casos 3–6): o solver e os perfis materiais para Casos 3 e 4 foram implementados (Caso 3 completamente, Caso 4 parcialmente); Casos 5 e 6 (anisotrópicos) aguardam implementação. Nenhum desses casos tem script de sweep nem curva de dispersão gerada.

---

## 2. Mapa Artigo → Implementação

| Componente do artigo | Localização no código | Status |
|---|---|---|
| Formulação escalar FEM (Ex-modes) | `src/local_assembly.cpp` | **IMPLEMENTADO** |
| Matriz F (equações 3a, 3b) | `src/local_assembly.cpp`, funções `F1`–`F4` | **IMPLEMENTADO** |
| Matriz M (massa) | `src/local_assembly.cpp` | **IMPLEMENTADO** |
| Anisotropia: tensores `[p]`, `[q]` via `nx2`, `nz2`, `gz2` | `src/local_assembly.cpp` (campos `delta_x`, `delta_z`, gradientes) | **IMPLEMENTADO** — nunca exercitado com material anisotrópico real |
| Eigenproblem generalizado `[F]{E} = n_eff² [M]{E}` | `src/eigensolver.cpp` (Jacobi + Cholesky) | **IMPLEMENTADO** e verificado |
| Caso 1 — canal homogêneo (Fig. 1) | `cases/homogeneous_channel_isotropic_case.yaml`, `scripts/run_case1_*` | **PARCIAL** — curva gerada, B desvia da referência (ver §3) |
| Caso 2 — planar difuso (Fig. 2) | `cases/planar_diffuse_isotropic_case.yaml`, `scripts/run_planar_diffuse_sweep.py` | **COMPLETO** — validado contra solução analítica |
| Caso 3 — canal circular difuso isotrópico (Fig. 4) | `cases/channel_diffused_isotropic_case.yaml`, `src/material_profile.cpp` | **PARCIAL** — solver + testes ok, sweep e curva de dispersão ausentes |
| Caso 4 — canal Gaussian-Gaussian (Fig. 5) | ausente | **FALTANDO** — perfil f(x,y) não definido no artigo (ver `docs/05`) |
| Caso 5 — APE LiNbO3 (Fig. 6) | ausente | **FALTANDO** |
| Caso 6 — Ti:LiNbO3 (Fig. 7) | ausente | **FALTANDO** |
| Condições de contorno Dirichlet/natural | `src/global_assembly.cpp`, `detect_dirichlet_node_ids` | **IMPLEMENTADO** — 3 opções: boundary, y\_extrema, natural |
| DOF reduction planar x-invariant | `src/global_assembly.cpp`, `build_dof_mapping` | **IMPLEMENTADO** — unitariamente auditado |

---

## 3. Problemas Conceituais ou de Nomenclatura

### 3.1 Caso 1 — desvio em B (não resolvido)

**Situação após a correção do Jacobi:** o eigensolver agora converge para malhas com ≥300 DOFs livres. Com a malha `farfield` (304 nós, 238 livres) e V=1.2, o solver retorna n_eff²=2.162, que corresponde a B≈0.571. O valor de referência visual para V=1.2 é B≈0.350. O desvio é de ~63%.

**Hipótese mais provável:** inversão semântica no material `rectangular_channel_step_index`. A função `evaluate_rectangular_channel_step_index_squared` atribui `cover_index` à região y < `surface_y` (abaixo da superfície — fisicamente o substrato) e `substrate_index` à região acima e fora do núcleo. Para o guia **enterrado** (buried) da Fig. 1 do artigo, a geometria correta tem n_cover = n_substrate = 1.43 (ar/substrato simétricamente), mas o YAML usa `cover_index: 1.0` e `substrate_index: 1.43` — resultando em geometria assimétrica.

**O que deve ser verificado:** se a Fig. 1 do artigo é para guia enterrado simétrico (n_cover = n_substrate = 1.43, núcleo suspenso em substrato) ou para guia de superfície com cobertura de ar. A referência [7] citada usa `a = 2b`, geometria buried.

**Pendência documentada:** este ponto está registrado em `PLANS.md` e deve ser resolvido antes de atualizar `docs/03`.

### 3.2 Tabela de comparação em `docs/03` — **desatualizada**

A tabela na seção "Comparação preliminar com pontos aproximados da Fig. 1" mostra B_calc negativos para todos os pontos (resultados anteriores à correção do Jacobi). Esses valores não refletem o estado atual do solver e são enganosos. Não devem ser removidos imediatamente, mas devem ser claramente marcados como "pré-correção do Jacobi" ou substituídos pelos resultados atualizados assim que a geometria do Caso 1 for resolvida.

### 3.3 Auditoria anterior `2024-05-21_gemini_auditoria_final.md` — **obsoleta**

A auditoria Gemini contém afirmações incorretas ou desatualizadas:
- Identifica como bug crítico "o ausência do fator π no script k0" — esse fator já estava presente no código à época da auditoria.
- Diz que Caso 1 é "PARTIAL" por normalização; a causa real era insuficiência do Jacobi (max_iterations=200).
- Afirma que Caso 3 está "MISSING"; o perfil circular está agora completamente implementado e testado.
- Afirma que anisotropia não está implementada no solver; ela está implementada em `src/local_assembly.cpp` (campos `nx2`, `nz2`, `gz2`, `delta_x`, `delta_z`).

O arquivo deve ser mantido como registro histórico, mas o cabeçalho precisa de uma nota de obsolescência.

### 3.4 Função `f(x,y)` do Caso 4 — não definida

O texto em `docs/05` documenta corretamente que a forma analítica de `f(x,y)` para o perfil Gaussian-Gaussian não está explicitada no artigo e deve ser recuperada da referência [12]. Esta é uma lacuna de pesquisa, não de implementação. Está registrada em `docs/05` com observação editorial adequada.

### 3.5 Rótulo de modo TE — corrigido nesta sessão

A função `mode_index_to_label` agora restringe os rótulos TE0/TE1/TE2 aos modelos `planar_diffuse_isotropic_exponential` e `planar_diffuse_isotropic_surface_exponential`, usando `mode_N` nos demais. O comportamento anterior (rotular todos os primeiros modos como TE, inclusive em casos de canal) foi corrigido no commit `b8587d4`.

### 3.6 Condição de contorno natural — unificada

Dois nomes distintos (`natural_zero_flux_on_boundary` e `open_boundary_natural`) foram unificados para o primeiro no commit `7750957`. O comportamento é o mesmo: manter todos os nós externos como DOFs livres. A documentação em `docs/03` e os YAMLs já usam o nome correto.

---

## 4. Documentos que Precisam ser Ajustados

| Documento | Problema | Ação recomendada | Prioridade |
|---|---|---|---|
| `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md` | Tabela de comparação mostra B_calc negativos (pré-Jacobi) | Marcar seção como "pré-correção" e, após resolver geometria, substituir por tabela atualizada | **ALTA** |
| `ia_logs/2024-05-21_gemini_auditoria_final.md` | Contém diagnósticos incorretos (bug π, ausência de anisotropia, Caso 3 missing) | Adicionar nota de obsolescência no cabeçalho do arquivo | **MÉDIA** |
| `docs/09_resumo_dos_casos_de_teste.md` | Deve refletir que Caso 3 está agora implementado a nível de solver | Atualizar status do Caso 3 de "MISSING" para "PARTIAL — solver implementado, sweep pendente" | **MÉDIA** |
| `PLANS.md` | Menciona o bug do Jacobi como resolvido, mas não registra a hipótese de geometria assimétrica do Caso 1 | Adicionar nota sobre a hipótese cover/substrate para orientar próxima investigação | **BAIXA** |

---

## 5. Estrutura Recomendada para o Relatório Final

O relatório final (`RESULTADOS_REPRODUCAO.md`, ainda não criado) deve ter a seguinte estrutura:

```markdown
# Resultados de Reprodução — Franco et al. (1999)

## Sumário Executivo
## Metodologia
  - Formulação FEM (referência a docs/02)
  - Decisões de implementação (malhas, condições de contorno, eigensolver)
  - Limitações conhecidas
## Caso 1 — Canal Homogêneo Isotrópico (Fig. 1)
  - Parâmetros
  - Curva de dispersão gerada
  - Comparação com referência (tabela + figura)
  - Discussão de desvios
## Caso 2 — Guia Planar Difuso Isotrópico (Fig. 2)
  - Parâmetros
  - Curva de dispersão vs. solução analítica
  - Erros relativos
## Caso 3 — Canal Difuso Circular Isotrópico (Fig. 4) [a gerar]
## Caso 4 — Canal Gaussian-Gaussian (Fig. 5) [pendente f(x,y)]
## Casos 5 e 6 — APE LiNbO3 e Ti:LiNbO3 (Figs. 6 e 7) [pendentes]
## Conclusões
  - Fidelidade geral da reprodução
  - Limitações da formulação escalar vs. vetorial
  - Sugestões de trabalho futuro
```

O Caso 2 já tem dados suficientes para ser escrito em definitivo. O Caso 1 requer resolução da geometria antes da redação final.

---

## 6. Tarefas por Agente

### Claude (este agente)

| ID | Tarefa | Prioridade | Pré-requisito |
|---|---|---|---|
| C-001 | Resolver geometria do Caso 1: verificar se Fig. 1 usa guia buried simétrico; ajustar YAML e re-executar sweep | **CRÍTICA** | — |
| C-002 | Atualizar tabela em `docs/03` com resultados pós-Jacobi e pós-geometria | **ALTA** | C-001 |
| C-003 | Implementar script de sweep para Caso 3 (`scripts/run_case3_sweep.py`) e gerar curva de dispersão | **ALTA** | — |
| C-004 | Escrever `RESULTADOS_REPRODUCAO.md` com Casos 1 e 2 (e 3 após C-003) | **MÉDIA** | C-001, C-002 |

### Codex

| ID | Tarefa | Prioridade | Pré-requisito |
|---|---|---|---|
| X-001 | Pesquisar referência [12] e documentar a fórmula `f(x,y)` do perfil Gaussian-Gaussian do Caso 4 | **MÉDIA** | — |
| X-002 | Após X-001: implementar perfil material e case YAML para Caso 4 | **MÉDIA** | X-001 |
| X-003 | Implementar perfil APE LiNbO3 do Caso 5 (equações 10–13 de `docs/06`) | **BAIXA** | — |

### Gemini Code

| ID | Tarefa | Prioridade | Pré-requisito |
|---|---|---|---|
| G-001 | Implementar perfil Ti:LiNbO3 do Caso 6 (equações 11–13 de `docs/06`, parâmetros completos disponíveis) | **BAIXA** | — |
| G-002 | Adicionar nota de obsolescência em `ia_logs/2024-05-21_gemini_auditoria_final.md` | **MÉDIA** | — |
| G-003 | Escrever testes unitários para a anisotropia em `local_assembly.cpp`: verificar que um elemento com nx2≠nz2 produz matrizes F e M distintas do caso isotrópico equivalente | **MÉDIA** | — |

---

## 7. Veredito Editorial

**Estado atual:** o projeto está em estágio de **reprodução incompleta, porém auditável e rastreável**.

**O que funciona bem:**
- A formulação FEM está correta e implementada fielmente ao artigo, incluindo a anisotropia tensorial, embora esta última ainda não tenha sido exercitada com casos físicos reais.
- O Caso 2 (planar difuso) está completamente validado com erros relativos baixos — isso dá credibilidade sólida ao núcleo do solver.
- Todos os 8 itens de `prompts.md` foram completados: o solver está limpo, bem estruturado e com infraestrutura de testes madura.
- O Caso 3 tem implementação completa a nível de solver e testes unitários; o que falta é o script de sweep e os dados de dispersão.

**O que precisa de atenção imediata:**
1. A geometria do Caso 1 (hipótese buried vs. surface) deve ser esclarecida antes de qualquer publicação de resultados. Os dados em `docs/03` são ativamente enganosos no estado atual.
2. O relatório final `RESULTADOS_REPRODUCAO.md` ainda não existe.

**O que pode aguardar:**
- Os Casos 4, 5 e 6 dependem de pesquisa bibliográfica adicional (Caso 4) ou de implementação de perfis materiais mais complexos (Casos 5 e 6), e podem ser abordados progressivamente sem bloquear os casos já implementados.

---

*Esta auditoria reflete o estado do repositório no commit `164dc7c` (2026-05-14).*
