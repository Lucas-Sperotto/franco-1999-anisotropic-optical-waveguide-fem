
# TODO.md — Plano Consolidado de Finalização

**Data da Consolidação:** 2026-05-14
**Fonte:** `ai_logs/2026-05-14_conselho_ias_plano_finalizacao.md`
**Revisão:** `ai_logs/2026-05-14_claude_auditoria_documental_final.md` (correções de 4 erros do plano Gemini)

Este arquivo contém as tarefas pendentes para a conclusão do projeto, consolidadas a partir das auditorias de Gemini, Claude e Codex.

## Fase A — Correções de build e documentação

- [ ] **T-001 — Corrigir comando de teste `ctest`**
  - **Responsável:** Codex
  - **Arquivos:** `README.md`, `scripts/test.sh` (a ser criado)
  - **Critério de aceite:** Um comando único e documentado (`./scripts/test.sh`) invoca `/usr/bin/ctest --test-dir build --output-on-failure` sem cair no wrapper Python quebrado em `/home/sperotto/.local/bin/ctest`.
  - **Comando de teste:** `./scripts/test.sh`

- [x] **T-002 — Adicionar nota de obsolescência à auditoria Gemini de 2024** *(concluído)*
  - **Responsável:** Claude
  - **Arquivos:** `ai_logs/2024-05-21_gemini_auditoria_final.md`
  - **Status:** feito nesta sessão — o cabeçalho já contém aviso identificando os quatro diagnósticos incorretos (bug do π, ausência de anisotropia, Caso 1, Caso 3).

## Fase B — Fechamento dos casos numéricos

- [ ] **T-003 — Investigar e corrigir geometria do Caso 1**
  - **Responsável:** Claude
  - **Arquivos:** `cases/homogeneous_channel_isotropic_case.yaml`, `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`
  - **Contexto:** YAML atual usa `cover_index: 1.0` (ar acima), gerando guia assimétrico. A Fig. 1 do artigo provavelmente usa guia buried com n_cover = n_substrate = 1.43. Hipótese a verificar contra referência [7].
  - **Critério de aceite:** A configuração é ajustada para a geometria correta e o desvio de B em relação à Fig. 1 é reduzido de ~63% para < 10%.
  - **Comando de teste:** `python3 scripts/run_case1_homogeneous_channel_sweep.py`

- [ ] **T-004 — Adicionar CTest smoke dedicado ao Caso 3**
  - **Responsável:** Codex
  - **Arquivos:** `CMakeLists.txt`, `tests/check_case3_sweep_outputs.py` (a ser criado)
  - **Contexto:** O Caso 3 executa pontualmente via `scripts/run_case.sh`, mas não tem CTest de artefatos próprio. O test `waveguide_global_tests` cobre sanidade de matriz, não reprodutibilidade de pipeline.
  - **Critério de aceite:** CTest roda `cases/channel_diffused_isotropic_case.yaml` e verifica existência de `neff.csv` e `dispersion_curve_points.csv`.
  - **Comando de teste:** `/usr/bin/ctest --test-dir build --output-on-failure -R case3`

- [ ] **T-005 — Implementar pipeline de automação para o Caso 3 (Fig. 4)**
  - **Responsável:** Codex
  - **Arquivos:** `scripts/run_case3_channel_diffused_sweep.py`, `scripts/consolidate_case3_channel_diffused_sweep.py`, `scripts/plot_case3_channel_diffused_sweep.py`
  - **Atenção:** O perfil circular tem `delta_x = false` e `delta_z = false` hardcoded em `src/material_profile.cpp:313-314` (TODO pendente sobre convenção do termo F4 de `docs/02`). O sweep vai gerar uma curva, mas ela não deve ser tratada como validação final do artigo até o F4 ser auditado.
  - **Critério de aceite:** Pipeline gera `consolidated/reference_dispersion.csv` e `plots/fig4_like_reference.svg` no estilo dos Casos 1 e 2.
  - **Comando de teste:** `python3 scripts/run_case3_channel_diffused_sweep.py --smoke --output-root build/test_output/case3_sweep`

- [ ] **T-006 — Auditar convenção do termo F4 para o Caso 3 (delta_x/delta_z)**
  - **Responsável:** Claude
  - **Arquivos:** `docs/02_formulacao_por_elementos_finitos.md`, `src/material_profile.cpp`, `src/local_assembly.cpp`
  - **Contexto:** `make_channel_diffused_isotropic_global_material` seta `delta_x = false; delta_z = false` com um TODO explícito. A questão é se o perfil circular n(x,y) tem gradiente material não nulo que deva ativar esses termos, ou se eles se cancelam pela simetria do perfil.
  - **Critério de aceite:** Decisão documentada em `docs/02` ou em comentário no código — com ou sem justificativa de por que `delta_z` deve ou não ser `true` para este perfil.
  - **Comando de teste:** N/A (tarefa de análise)

- [ ] **T-007 — Pesquisar e implementar perfil do Caso 4 (Fig. 5)**
  - **Responsável:** Codex
  - **Arquivos:** `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`, `src/material_profile.cpp`
  - **Pré-requisito:** Recuperar a forma analítica de `f(x,y)` da referência [12] antes de qualquer implementação.
  - **Critério de aceite:** A fórmula de `f(x,y)` está documentada com fonte rastreável e o perfil implementado passa em teste unitário.
  - **Comando de teste:** `cmake --build build -j && build/waveguide_global_tests`

- [ ] **T-008 — Criar contrato de material anisotrópico para Casos 5 e 6**
  - **Responsável:** Codex
  - **Arquivos:** `include/waveguide_solver/material_profile.hpp`, `src/material_profile.cpp`, `tests/global_tests.cpp`
  - **Contexto:** Antes de implementar APE e Ti:LiNbO3, criar um teste unitário que verfique que um elemento com nx2 ≠ nz2 produz matrizes F e M distintas do caso isotrópico equivalente. Isso garante que a infraestrutura anisotrópica já existente em `local_assembly.cpp` funciona corretamente antes de adicionar os perfis complexos.
  - **Critério de aceite:** Teste unitário passa e documenta a expectativa de comportamento.
  - **Comando de teste:** `cmake --build build -j && build/waveguide_global_tests`

- [ ] **T-009 — Implementar perfil do Caso 5 (APE LiNbO3, Fig. 6)**
  - **Responsável:** Gemini
  - **Arquivos:** `src/material_profile.cpp`, `cases/case5_ape_linbo3.yaml` (a ser criado)
  - **Pré-requisito:** T-008 concluído.
  - **Contexto:** Equação (10) de `docs/06`: n_e(C) = n_es + Δn_e·[1 − exp(−11C)]. O perfil de concentração C(x,y) requer resolver equação de difusão anisotrópica em 2D — ou usar um mapa pré-computado.
  - **Critério de aceite:** O solver executa o Caso 5 e gera n_eff para pelo menos um ponto da curva da Fig. 6.
  - **Comando de teste:** `scripts/run_case.sh cases/case5_ape_linbo3.yaml audit_case5`

- [ ] **T-010 — Implementar perfil do Caso 6 (Ti:LiNbO3, Fig. 7)**
  - **Responsável:** Gemini
  - **Arquivos:** `src/material_profile.cpp`, `cases/case6_ti_linbo3.yaml` (a ser criado)
  - **Pré-requisito:** T-008 concluído.
  - **Contexto:** Equações (11)–(13) de `docs/06` — perfil Gaussian-Gaussian anisotrópico com parâmetros distintos para ramos extraordinário e ordinário. Todos os parâmetros numéricos estão em `docs/06`.
  - **Critério de aceite:** O solver executa o Caso 6 e gera n_eff para pelo menos um ponto da curva da Fig. 7.
  - **Comando de teste:** `scripts/run_case.sh cases/case6_ti_linbo3.yaml audit_case6`

## Fase C — Geração de CSVs e figuras

- [ ] **T-011 — Re-gerar resultados e figura do Caso 1**
  - **Responsável:** Gemini
  - **Arquivos:** `out/case1_homogeneous_channel/`
  - **Pré-requisito:** T-003 concluído.
  - **Critério de aceite:** CSV e SVG da curva de dispersão gerados com geometria corrigida.
  - **Comando de teste:** `python3 scripts/run_case1_homogeneous_channel_sweep.py`

- [ ] **T-012 — Gerar resultados e figura do Caso 3 (Fig. 4)**
  - **Responsável:** Gemini
  - **Arquivos:** `out/case3_circular_channel/` (a ser criado)
  - **Pré-requisitos:** T-005 e T-006 concluídos.
  - **Critério de aceite:** CSV e SVG gerados; nota na figura indica se F4 foi ou não ativado.
  - **Comando de teste:** `python3 scripts/run_case3_channel_diffused_sweep.py`

## Fase D — Documentação científica

- [ ] **T-013 — Atualizar documento do Caso 1 (docs/03)**
  - **Responsável:** Claude
  - **Arquivos:** `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`
  - **Pré-requisito:** T-011 concluído.
  - **Critério de aceite:** A tabela de comparação com B_calc negativos é substituída pelos resultados corretos, e a seção de conclusão é atualizada.
  - **Comando de teste:** Verificação manual

- [ ] **T-014 — Atualizar docs/09 com status atual dos casos**
  - **Responsável:** Claude
  - **Arquivos:** `docs/09_resumo_dos_casos_de_teste.md`
  - **Critério de aceite:** O status do Caso 3 é atualizado de "MISSING" para refletir a implementação atual com a ressalva do F4.

## Fase E — Relatório final

- [ ] **T-015 — Escrever o relatório final de reprodução**
  - **Responsável:** Claude
  - **Arquivos:** `RESULTADOS_REPRODUCAO.md` (a ser criado)
  - **Pré-requisito:** T-011 e T-012 concluídos.
  - **Critério de aceite:** O relatório consolida resultados dos Casos 1, 2 e 3, com tabelas, figuras e discussão de desvios. Casos 4–6 marcados como pendentes com contexto.

## Fase F — Limpeza final do repositório

- [ ] **T-016 — Atualizar README.md**
  - **Responsável:** Gemini
  - **Arquivos:** `README.md`
  - **Critério de aceite:** O README contém os comandos reais de execução (`./scripts/build.sh`, `/usr/bin/ctest ...`, etc.) e lista o estado de cada caso.
