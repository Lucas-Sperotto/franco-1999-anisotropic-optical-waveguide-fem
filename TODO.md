# Plano Consolidado de Finalização

**Data:** 2026-05-14  
**Consolidador:** Codex  
**Fontes:** `ai_logs/2024-05-21_gemini_auditoria_final.md`, `ai_logs/2026-05-14_claude_auditoria_documental_final.md`, `ai_logs/2026-05-14_codex_auditoria_tecnica_final.md`

## 1. Veredito geral

O projeto está **parcialmente pronto**.

A base técnica compila, a suíte passa via `./scripts/test.sh` e o fluxo `bash scripts/run_all.sh --smoke && python3 scripts/plot_all.py --smoke` valida os artefatos reduzidos dos Casos 1 a 6. O Caso 2 é o único caso atualmente pronto como reprodução quantitativa final: tem CSV, figura e comparação analítica no pipeline. Os Casos 1, 3, 4, 5 e 6 são reprodutíveis, mas permanecem parciais por limitações específicas de validação ou modelagem.

Casos já prontos:

- Caso 2 - Fig. 2: guia planar isotrópico difundido, com CSV, figura e referência analítica.

Casos implementados ou reprodutíveis, mas ainda não prontos:

- Caso 1 - Fig. 1: CSV e figura existem, mas a validação final depende de resolver a geometria `cover_index`/`substrate_index`.
- Caso 3 - Fig. 4: sweep e figura existem, mas a validação final depende de auditar/ativar `delta_x`/`delta_z` no perfil circular.
- Caso 4 - Fig. 5: sweep, consolidação e figura existem; falta referência digitizada/overlay para validação quantitativa.
- Caso 5 - Fig. 6: sweep de 4 modos e figura existem; falta substituir a proxy Gaussian por pré-processador FEM 2D de difusão APE, se necessário para comparação final.
- Caso 6 - Fig. 7: sweep em `W`, `W_x/W_y` e figura existem; falta estudo de convergência de malha/extração FWHM.

## 2. Matriz de reprodução

| Caso | Figura | Status atual | O que falta | Responsável sugerido |
| --- | --- | --- | --- | --- |
| Caso 1 - guia homogêneo isotrópico | Fig. 1 | Parcial: geometria confirmada (T-004), docs/03 atualizado (T-017); discrepância explicada por ref. de Marcatili/EIM | Regenerar artefatos finais em `final_run/` (T-013) | Claude/Gemini |
| Caso 2 - guia planar isotrópico difundido | Fig. 2 | Pronto: executa, gera CSV e SVG, possui comparação analítica | Fixar artefatos finais em `final_run/` (T-014) | Gemini |
| Caso 3 - canal isotrópico circular | Fig. 4 | Parcial: modelo, YAML, sweep, CSV e figura existem; flags delta seguem desligados neste perfil | Auditar ativação de `delta_x/delta_z` no perfil circular | Codex + Claude |
| Caso 4 - canal Gaussian-Gaussian | Fig. 5 | Parcial: fórmula confirmada na ref. [12], sweep/CSV/SVG implementados com delta ativo | Anexar/digitar referência e quantificar erro | Codex |
| Caso 5 - APE LiNbO3 | Fig. 6 | Parcial: sweep/CSV/SVG implementados com 4 modos e proxy Gaussian de concentração | Avaliar necessidade de pré-processador FEM 2D de difusão APE | Codex |
| Caso 6 - Ti:LiNbO3 | Fig. 7 | Parcial: sweep em `W`, `W_x/W_y`, CSV e SVG implementados | Auditar extração FWHM e convergência de malha | Codex |

## 3. TODO por fases

### Fase A - Correções de build e testes

- [x] T-001 — Criar comando reprodutível de testes
  - Responsável: Codex
  - Arquivos: `scripts/test.sh`, `README.md`, `tests/README.md`
  - Critério de aceite: `./scripts/test.sh` executa `/usr/bin/ctest --test-dir build --output-on-failure` e evita o wrapper Python quebrado em `/home/sperotto/.local/bin/ctest`.
  - Comando de teste: `./scripts/test.sh`

- [x] T-002 — Adicionar CTest smoke dedicado ao Caso 3
  - Responsável: Codex
  - Arquivos: `CMakeLists.txt`, `tests/check_smoke_outputs.cmake`
  - Critério de aceite: a suíte CTest executa `cases/channel_diffused_isotropic_case.yaml` e verifica `neff.csv`, `dispersion_curve_points.csv` e `nodal_material_fields.csv`.
  - Comando de teste: `./scripts/test.sh -R case3`

- [x] T-003 — Atualizar documentação curta da suíte de testes
  - Responsável: Codex
  - Arquivos: `tests/README.md`, `README.md`
  - Critério de aceite: a documentação informa a suíte CTest atual, os testes smoke dos casos implementados e o uso de `/usr/bin/ctest` ou `./scripts/test.sh`.
  - Comando de teste: `./scripts/test.sh`

### Fase B - Fechamento dos casos numéricos

- [x] T-004 — Resolver a geometria do Caso 1
  - Responsável: Claude
  - Arquivos: `cases/homogeneous_channel_isotropic_case.yaml`, `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`, `scripts/run_case1_homogeneous_channel_sweep.py`
  - Critério de aceite: fica documentado se a Fig. 1 usa guia buried simétrico ou superfície assimétrica; o YAML é ajustado apenas se a hipótese for confirmada; a nova curva reduz a discrepância sem mascarar o método.
  - Comando de teste: `python3 scripts/run_case1_homogeneous_channel_sweep.py --smoke --output-root build/test_output/case1_geometry_check`
  - **Resultado (2026-06-15):** A Fig. 1 usa **guia de superfície assimétrico** (n₁=1.00 ar acima, n₂=1.43 substrato abaixo/laterais). Hipótese buried (`cover_index=1.43`) testada e REJEITADA (piorou erro em V=1.2 de 43% para 63%). YAML `cover_index=1.00` mantido sem alteração. Smoke sweep confirmado: B=0.502/0.735/0.910 em V=1.2/2.0/4.0 (todos guiados). Discrepância residual explicada: pontos de referência extraídos da curva Marcatili/EIM (curvas inferiores), não da curva FEM "This work".

- [x] T-005 — Auditar o termo F4 no Caso 3
  - Responsável: Claude
  - Arquivos: `docs/02_formulacao_por_elementos_finitos.md`, `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`, `src/material_profile.cpp`, `src/local_assembly.cpp`
  - Critério de aceite: a decisão sobre `delta_x` e `delta_z` no perfil circular fica registrada com justificativa; se a documentação não sustentar mudança, manter o caso conservador e registrar TODO explícito.
  - Comando de teste: verificação documental e `build/waveguide_global_tests`
  - **Resultado (2026-06-15):** `docs/02` §3 confirma explicitamente que F2, F3 e F4 são não-simétricas quando delta_x/delta_z são ativos. Os flags permanecem `false` nos perfis 2D até a rota não simétrica ser auditada.
  - **Atualização (2026-06-16) — rota não-simétrica operacional:** `src/eigensolver.cpp` usa a rota `general_nonsym_refined`: transformação por Cholesky de `M`, estimativa inicial por simetrização/Jacobi, iteração inversa no operador não simétrico e refinamento por quociente de Rayleigh. Também há eliminação Gaussiana com pivoteamento parcial para os sistemas lineares e correção em `app.cpp` para não calcular confinamento quando um eigenpair não trouxer autovetor. `delta_x/delta_z` foram ativados nos perfis dos Casos 4, 5 e 6. O Caso 3 circular permanece conservador (`false`) até auditoria própria da geometria.

- [x] T-006 — Criar pipeline completo da Fig. 4
  - Responsável: Codex
  - Arquivos: `scripts/run_case3_channel_diffused_sweep.py`, `scripts/consolidate_case3_channel_diffused_sweep.py`, `scripts/plot_case3_channel_diffused_sweep.py`, `tests/check_case3_sweep_outputs.py`
  - Critério de aceite: o Caso 3 gera CSV consolidado e SVG tipo Fig. 4; o status da figura indica explicitamente se F4 foi auditado.
  - Comando de teste: `python3 scripts/run_case3_channel_diffused_sweep.py --smoke --output-root build/test_output/case3_sweep`
  - **Resultado (2026-06-15):** scripts criados e testados. Smoke em V=2.0 e V=4.0: neff=1.4734/1.4830, B=1.116/1.441 (B > 1 esperado com delta_x/delta_z desativados — neff > n3av). SVG gerado com eixo B estendido até 1.5 e linha de referência B=1.0 tracejada com nota T-005 visível. A curva completa (15 pontos) está em `out/case3_channel_diffused_isotropic/final_run/`. Verificador `tests/check_case3_sweep_outputs.py` conectado ao CTest em 2026-06-15.

- [x] T-007 — Recuperar a fórmula do Caso 4
  - Responsável: Gemini
  - Arquivos: `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`
  - Critério de aceite: A forma analítica de `f(x,y)` foi registrada em `docs/05` com justificativa, desbloqueando a implementação.
  - Status: Concluído.

- [x] T-008 — Implementar o Caso 4 após recuperar `f(x,y)`
  - Responsável: Codex
  - Arquivos: `include/waveguide_solver/material_profile.hpp`, `src/material_profile.cpp`, `src/config.cpp`, `src/global_assembly.cpp`, `src/app.cpp`, `cases/case4_gaussian_gaussian_channel.yaml`, `tests/global_tests.cpp`
  - Critério de aceite: perfil implementado sem fórmula inventada, YAML executa, teste de sanidade passa e gera CSV pontual.
  - Comando de teste: `cmake --build build -j && build/waveguide_global_tests`
  - **Resultado Codex (2026-06-15):** referência [12] organizada; fórmula `f(x,y)` verificada; perfil C++ e YAML implementados; CTest pontual passa. neff=1.493103 (delta=false).
  - **Atualização (2026-06-16):** delta_x/delta_z ATIVADOS após auditoria da rota `general_nonsym_refined`. Scripts criados: `run_case4_gaussian_gaussian_sweep.py`, `consolidate_case4_gaussian_gaussian_sweep.py`, `plot_case4_gaussian_gaussian_sweep.py`. Sweep completo (17 pontos, V=1.0..5.0) concluído em `out/case4_gaussian_gaussian/final_run/`. Artefatos: `consolidated/dispersion_curve.csv` (51 pares modo/V após filtragem de modos não-guiados), `plots/fig5_like_reference.svg`. Curva modo 1: B cresce monotonicamente de 0.021 (V=1.0) a 0.597 (V=5.0).

- [x] T-009 — Criar contrato de material anisotrópico exercitado
  - Responsável: Codex
  - Arquivos: `include/waveguide_solver/material_profile.hpp`, `src/material_profile.cpp`, `tests/global_tests.cpp`
  - Critério de aceite: há teste mínimo mostrando que material com `nx2 != nz2` produz montagem diferente do equivalente isotrópico, sem misturar ainda os perfis APE/Ti.
  - Comando de teste: `cmake --build build -j && build/waveguide_global_tests`
  - **Resultado Codex (2026-06-15):** `tests/global_tests.cpp` agora monta um caso anisotrópico constante com `nx2 != nz2`, verifica que `M_full` e `F_full` diferem do caso isotrópico equivalente, preserva simetria no caso constante e resolve um autovalor válido. Validação: `./scripts/test.sh -R waveguide_global_tests`.

- [x] T-010 — Consolidar tabela de parâmetros dos Casos 5 e 6
  - Responsável: Gemini
  - Arquivos: `docs/06_guia_de_onda_de_canal_difuso_anisotropico.md`, `docs/09_resumo_dos_casos_de_teste.md`, `ai_logs/`
  - Critério de aceite: todos os parâmetros necessários para APE e Ti:LiNbO3 estão listados, com unidade, símbolo, fonte e lacunas explícitas.
  - Comando de teste: verificação manual das tabelas
  - **Resultado (2026-06-15):** Tabelas de parâmetros detalhadas para os Casos 5 e 6 foram adicionadas a `docs/09_resumo_dos_casos_de_teste.md`, consolidando as informações de `docs/06` e explicitando as lacunas (e.g., $n_{es}$ no Caso 5).

- [x] T-011 — Implementar o Caso 5, APE LiNbO3
  - Responsável: Codex
  - Arquivos: `src/material_profile.cpp`, `src/config.cpp`, `src/global_assembly.cpp`, `src/app.cpp`, `cases/case5_ape_linbo3.yaml`, `tests/global_tests.cpp`
  - Critério de aceite: o solver executa pelo menos um ponto da Fig. 6, gera CSV e deixa limitações da difusão anisotrópica documentadas.
  - Comando de teste: `bash scripts/run_case.sh cases/case5_ape_linbo3.yaml audit_case5`
  - **Resultado Codex (2026-06-16):** `ape_linbo3_anisotropic_sanity` implementado; YAML executa 4 modos; neff=2.207327 (sanidade). Limitação: C(x,y) proxy e delta=false.
  - **Atualização (2026-06-16):** pré-processador APE para aproximação Gaussian implementado em `scripts/ape_diffusion_preprocessor.py` (`Da_x=0.92`, `Da_z=0.77 µm²/h`; para t=4h: dx=3.836665, dy=3.509986). `case5_ape_linbo3.yaml` atualizado para `peak_concentration=1.00`. delta_x/delta_z ATIVADOS. Scripts: `run_case5_ape_linbo3_sweep.py`, `consolidate_case5_ape_linbo3_sweep.py`, `plot_case5_ape_linbo3_sweep.py`. Sweep (15 pontos, t=0.3h..10h, V=2.24..12.92) concluído em `out/case5_ape_linbo3/final_run/`. Artefatos: `consolidated/dispersion_curve.csv` (60 linhas, 4 modos × 15 pontos de tempo), `plots/fig6_like_reference.svg`. Modo 1 monotônico: B=0.872→0.990.

- [x] T-012 — Implementar o Caso 6, Ti:LiNbO3
  - Responsável: Codex
  - Arquivos: `src/material_profile.cpp`, `src/config.cpp`, `src/global_assembly.cpp`, `src/app.cpp`, `cases/case6_ti_linbo3.yaml`, `tests/global_tests.cpp`
  - Critério de aceite: o solver executa pelo menos um ponto da Fig. 7, gera CSV e separa corretamente parâmetros ordinário/extraordinário.
  - Comando de teste: `bash scripts/run_case.sh cases/case6_ti_linbo3.yaml audit_case6`
  - **Resultado Codex (2026-06-16):** `ti_diffused_linbo3_anisotropic` implementado; YAML executa em W=7µm; neff=2.210077. Exporta nx/nz separados. Delta=false (sanidade).
  - **Atualização (2026-06-16):** delta_x/delta_z ATIVADOS. Scripts: `run_case6_ti_linbo3_sweep.py` (W=3..12 µm, 18 pontos), `consolidate_case6_ti_linbo3_sweep.py` (extrai W_x/W_y via FWHM de |E|² com max-binning), `plot_case6_ti_linbo3_sweep.py` (neff + W_x + W_y vs W, dois eixos Y). Sweep concluído (18 pontos, W=3..12 µm) em `out/case6_ti_linbo3/final_run/`. Artefatos: `consolidated/neff_mode_sizes.csv` (18 linhas), `plots/fig7_like_reference.svg`. neff cresce monotonicamente de 2.20908 (W=3µm) a 2.21054 (W=12µm). W_x mínimo ≈4.70 µm em W=7µm (spot de menor largura); W_y decresce de 4.29 para 4.14 µm conforme o campo se confina.

### Fase C - Geração de CSVs e figuras

- [x] T-013 — Regenerar CSV e figura finais do Caso 1
  - Responsável: Gemini
  - Arquivos: `out/case1_homogeneous_channel/final_run/`
  - Critério de aceite: `reference_dispersion.csv`, `consolidated_curve.csv` e `fig1_like_reference.svg` são gerados após a decisão de geometria.
  - Comando de teste: `python3 scripts/plot_case1_homogeneous_channel_sweep.py --sweep-root out/case1_homogeneous_channel/final_run`
  - **Resultado (2026-06-15):** sweep executado com 34 pontos no CSV consolidado. SVG `fig1_like_reference.svg` gerado em `out/case1_homogeneous_channel/final_run/plots/`. Comparação com referência visual mostra desvios esperados (pontos de referência são da curva Marcatili/EIM, confirmado em T-004).

- [x] T-014 — Fixar artefatos finais do Caso 2
  - Responsável: Gemini
  - Arquivos: `out/planar_diffuse_sweep/final_run/`
  - Critério de aceite: CSVs consolidados, comparação analítica e `fig2_like_reference.svg` existem em pasta final reproduzível.
  - Comando de teste: `python3 scripts/plot_planar_diffuse_sweep.py --sweep-root out/planar_diffuse_sweep/final_run`
  - **Resultado (2026-06-15):** sweep executado em `final_run/`; consolidação bloqueada por incompatibilidade scipy 1.11.4 vs numpy 2.4.6 (erro `cannot import name 'Inf'`). Artefatos copiados de `case2_exact_refined/` (run equivalente, mesmos parâmetros). `fem_vs_exact_comparison.csv` e `fig2_like_reference.svg` disponíveis em `final_run/consolidated/` e `final_run/plots/`. Erro máximo: 0.0017% (Caso 2 mantido como PASS).
  - **Atualização Codex (2026-06-15):** `scripts/planar_exact_reference.py` deixou de depender de SciPy e passou a usar `mpmath` + bisseção local. O teste `./scripts/test.sh -R waveguide_planar_sweep` voltou a passar no ambiente com numpy 2.4.6.

- [x] T-015 — Gerar CSV e figura finais do Caso 3
  - Responsável: Gemini
  - Arquivos: `out/case3_channel_diffused_isotropic/final_run/`
  - Critério de aceite: CSV consolidado e `fig4_like_reference.svg` existem; o relatório marca claramente qualquer ressalva de F4.
  - Comando de teste: `python3 scripts/plot_case3_channel_diffused_sweep.py --sweep-root out/case3_channel_diffused_isotropic/final_run`
  - **Resultado (2026-06-15):** sweep completo executado (15 pontos, V=1.5..5.0). CSV `dispersion_curve.csv` e SVG `fig4_like_reference.svg` em `final_run/consolidated/` e `final_run/plots/`. Todos os pontos com B > 1 (1.0..1.5) por causa dos flags delta_x/delta_z desativados (T-005 BLOCKER visível no SVG). Ressalva explícita no plot e na nota de limitação.

- [x] T-016 — Criar orquestradores finais de reprodução
  - Responsável: Codex
  - Arquivos: `scripts/run_all.sh`, `scripts/plot_all.py`
  - Critério de aceite: um comando roda os casos implementados e outro gera/consolida as figuras disponíveis, sem fingir que Casos 4-6 estão prontos.
  - Comando de teste: `bash scripts/run_all.sh && python3 scripts/plot_all.py`
  - **Resultado Codex (2026-06-16):** `scripts/run_all.sh` e `scripts/plot_all.py` agora incluem os sweeps dos Casos 1 a 6. Validação executada: `bash scripts/run_all.sh --smoke --skip-build && python3 scripts/plot_all.py --smoke`. O `plot_all.py` verifica os artefatos reduzidos e grava `out/reproduction_artifacts.csv`.

### Fase D - Documentação científica

- [x] T-017 — Atualizar `docs/03` com o estado real do Caso 1
  - Responsável: Claude
  - Arquivos: `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`
  - Critério de aceite: a tabela antiga com resultados pré-correção não aparece como resultado atual; a seção explica geometria, desvios e limites da comparação.
  - Comando de teste: verificação manual
  - **Resultado (2026-06-15):** seção "Investigação de geometria (T-004)" adicionada com geometria de superfície assimétrica confirmada, hipótese buried rejeitada empiricamente, tabela comparativa surface vs. buried, e discrepância residual explicada pela extração dos pontos de referência da curva Marcatili/EIM (não da curva FEM). Não há tabela de resultados pré-correção; o texto atual é o estado real.

- [x] T-018 — Atualizar `docs/09` com a matriz real dos casos
  - Responsável: Claude
  - Arquivos: `docs/09_resumo_dos_casos_de_teste.md`
  - Critério de aceite: Caso 2 aparece como pronto; Casos 1, 3, 4, 5 e 6 aparecem como parciais, distinguindo figuras finais de pontos de sanidade.
  - Comando de teste: verificação manual
  - **Resultado (2026-06-16):** seção "Estado atual de reprodução" atualizada com: Caso 1 com resultado T-004; Caso 2 PASS; Caso 3 com sweep/figura e bloqueio de gradientes; Casos 4-6 com sweeps, CSVs, SVGs e limitações explícitas.

- [x] T-019 — Documentar o Caso 3 depois do sweep
  - Responsável: Claude
  - Arquivos: `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`, `RESULTADOS_REPRODUCAO.md`
  - Critério de aceite: parâmetros, fórmula usada, artefatos e ressalva de F4 aparecem de forma auditável.
  - Comando de teste: verificação manual
  - **Resultado (2026-06-15):** seção "Reprodução computacional do Caso 3" adicionada em `docs/05` com auditoria T-005, sweep de 15 pontos (B > 1 por delta_x/delta_z desativados), e caminhos dos artefatos finais. Tabela consolidada em RESULTADOS_REPRODUCAO.md atualizada com 15 pontos CSV e SVG gerado.

### Fase E - Relatório final

- [x] T-020 — Escrever `RESULTADOS_REPRODUCAO.md`
  - Responsável: Claude
  - Arquivos: `RESULTADOS_REPRODUCAO.md`
  - Critério de aceite: o relatório lista metodologia, comandos, tabelas, CSVs e figuras dos casos prontos; casos pendentes são declarados como pendentes, não como validados.
  - Comando de teste: `/usr/bin/ctest --test-dir build --output-on-failure`
  - **Resultado (2026-06-16):** relatório atualizado com Casos 4, 5 e 6 como sweeps implementados. Estado atual: 1 caso PASS (Fig. 2) e 5 casos PARTIAL com artefatos reproduzíveis (Figs. 1, 4, 5, 6 e 7).

### Fase F - Limpeza final do repositório

- [x] T-021 — Atualizar `README.md`
  - Responsável: Gemini
  - Arquivos: `README.md`
  - Critério de aceite: README inclui estado por caso, comandos reais, dependências e caminho dos artefatos finais.
  - Comando de teste: verificação manual
  - **Resultado Codex (2026-06-16):** README atualizado com tabela de estado por figura, suíte de 41 testes, fluxo `run_all/plot_all` cobrindo Casos 1-6 e caminhos dos artefatos finais.

- [x] T-022 — Limpar e organizar saídas finais
  - Responsável: Codex
  - Arquivos: `out/README.md`, `out/case1_homogeneous_channel/final_run/`, `out/planar_diffuse_sweep/final_run/`, `out/case3_channel_diffused_isotropic/final_run/`, `out/case4_gaussian_gaussian/final_run/`, `out/case5_ape_linbo3/final_run/`, `out/case6_ti_linbo3/final_run/`
  - Critério de aceite: saídas exploratórias ficam separadas das saídas finais; nenhum resultado solto na raiz é necessário para reproduzir o relatório.
  - Comando de teste: `find out -maxdepth 3 -type f | sort`
  - **Resultado Codex (2026-06-16):** `out/README.md` declara as seis pastas finais canônicas e classifica as demais saídas como exploratórias/históricas. Nenhum artefato antigo foi apagado ou movido, para preservar referências existentes em relatórios. `plot_all.py --smoke` verificou os artefatos finais esperados no fluxo reduzido.

## 4. Divisão por IA

### Gemini

- Conferir parâmetros e tabelas do artigo, especialmente Casos 4-6.
- Manter a matriz de reprodução sincronizada com CSVs e figuras reais.
- Executar e conferir os sweeps finais dos casos que já tiverem pipeline.
- Atualizar README/TODO em nível de coordenação.

### Claude

- Resolver as pendências científicas e documentais: geometria do Caso 1, F4 do Caso 3, status em `docs/09`.
- Atualizar documentos técnicos sem apagar ambiguidades relevantes.
- Escrever `RESULTADOS_REPRODUCAO.md` com linguagem científica e limites explícitos.

### Codex

- Implementar patches pequenos e verificáveis.
- Manter build, CTest, scripts e artefatos reproduzíveis.
- Manter os CTests dos sweeps dos Casos 1-6, orquestradores finais e perfis materiais futuros quando a fórmula estiver documentada.

## 5. Comandos finais esperados

Comandos reais disponíveis hoje:

```bash
cmake -S . -B build
cmake --build build -j
/usr/bin/ctest --test-dir build --output-on-failure

./scripts/test.sh
bash scripts/run_all.sh
python3 scripts/plot_all.py

python3 scripts/run_case1_homogeneous_channel_sweep.py --output-root out/case1_homogeneous_channel/final_run
python3 scripts/consolidate_case1_homogeneous_channel_sweep.py --sweep-root out/case1_homogeneous_channel/final_run
python3 scripts/plot_case1_homogeneous_channel_sweep.py --sweep-root out/case1_homogeneous_channel/final_run

python3 scripts/run_planar_diffuse_sweep.py --output-root out/planar_diffuse_sweep/final_run
python3 scripts/consolidate_planar_diffuse_sweep.py --sweep-root out/planar_diffuse_sweep/final_run
python3 scripts/plot_planar_diffuse_sweep.py --sweep-root out/planar_diffuse_sweep/final_run

python3 scripts/run_case3_channel_diffused_sweep.py --output-root out/case3_channel_diffused_isotropic/final_run
python3 scripts/consolidate_case3_channel_diffused_sweep.py --sweep-root out/case3_channel_diffused_isotropic/final_run
python3 scripts/plot_case3_channel_diffused_sweep.py --sweep-root out/case3_channel_diffused_isotropic/final_run

python3 scripts/run_case4_gaussian_gaussian_sweep.py --output-root out/case4_gaussian_gaussian/final_run
python3 scripts/consolidate_case4_gaussian_gaussian_sweep.py --sweep-root out/case4_gaussian_gaussian/final_run
python3 scripts/plot_case4_gaussian_gaussian_sweep.py --sweep-root out/case4_gaussian_gaussian/final_run

python3 scripts/run_case5_ape_linbo3_sweep.py --output-root out/case5_ape_linbo3/final_run
python3 scripts/consolidate_case5_ape_linbo3_sweep.py --sweep-root out/case5_ape_linbo3/final_run
python3 scripts/plot_case5_ape_linbo3_sweep.py --sweep-root out/case5_ape_linbo3/final_run

python3 scripts/run_case6_ti_linbo3_sweep.py --output-root out/case6_ti_linbo3/final_run
python3 scripts/consolidate_case6_ti_linbo3_sweep.py --sweep-root out/case6_ti_linbo3/final_run
python3 scripts/plot_case6_ti_linbo3_sweep.py --sweep-root out/case6_ti_linbo3/final_run
```

## 6. Arquivos finais obrigatórios

- `README.md` - visão geral, comandos e status por caso.
- `TODO.md` - plano vivo e priorizado.
- `RESULTADOS_REPRODUCAO.md` - relatório final de reprodução.
- `docs/02_formulacao_por_elementos_finitos.md` - formulação FEM.
- `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md` - Caso 1 atualizado.
- `docs/04_guia_de_onda_planar_difuso_isotropico.md` - Caso 2.
- `docs/05_guia_de_onda_de_canal_difuso_isotropico.md` - Casos 3 e 4, com fórmula/ambiguidade registrada.
- `docs/06_guia_de_onda_de_canal_difuso_anisotropico.md` - Casos 5 e 6.
- `docs/09_resumo_dos_casos_de_teste.md` - matriz final de casos.
- `cases/homogeneous_channel_isotropic_case.yaml`
- `cases/planar_diffuse_isotropic_case.yaml`
- `cases/channel_diffused_isotropic_case.yaml`
- `cases/case4_gaussian_gaussian_channel.yaml`
- `cases/case5_ape_linbo3.yaml`
- `cases/case6_ti_linbo3.yaml`
- `scripts/build.sh`
- `scripts/test.sh`
- `scripts/run_case.sh`
- `scripts/run_all.sh`
- `scripts/plot_all.py`
- `scripts/run_case1_homogeneous_channel_sweep.py`
- `scripts/consolidate_case1_homogeneous_channel_sweep.py`
- `scripts/plot_case1_homogeneous_channel_sweep.py`
- `scripts/run_planar_diffuse_sweep.py`
- `scripts/consolidate_planar_diffuse_sweep.py`
- `scripts/plot_planar_diffuse_sweep.py`
- `scripts/run_case3_channel_diffused_sweep.py`
- `scripts/consolidate_case3_channel_diffused_sweep.py`
- `scripts/plot_case3_channel_diffused_sweep.py`
- `scripts/run_case4_gaussian_gaussian_sweep.py`
- `scripts/consolidate_case4_gaussian_gaussian_sweep.py`
- `scripts/plot_case4_gaussian_gaussian_sweep.py`
- `scripts/ape_diffusion_preprocessor.py`
- `scripts/run_case5_ape_linbo3_sweep.py`
- `scripts/consolidate_case5_ape_linbo3_sweep.py`
- `scripts/plot_case5_ape_linbo3_sweep.py`
- `scripts/run_case6_ti_linbo3_sweep.py`
- `scripts/consolidate_case6_ti_linbo3_sweep.py`
- `scripts/plot_case6_ti_linbo3_sweep.py`
- `tests/check_smoke_outputs.cmake`
- `tests/check_case3_sweep_outputs.py`
- `tests/check_case4_sweep_outputs.py`
- `tests/check_case5_sweep_outputs.py`
- `tests/check_case6_sweep_outputs.py`
- `out/case1_homogeneous_channel/final_run/consolidated/*.csv`
- `out/case1_homogeneous_channel/final_run/plots/*.svg`
- `out/planar_diffuse_sweep/final_run/consolidated/*.csv`
- `out/planar_diffuse_sweep/final_run/plots/*.svg`
- `out/case3_channel_diffused_isotropic/final_run/consolidated/*.csv`
- `out/case3_channel_diffused_isotropic/final_run/plots/*.svg`
- `out/case4_gaussian_gaussian/final_run/consolidated/*.csv`
- `out/case4_gaussian_gaussian/final_run/plots/*.svg`
- `out/case5_ape_linbo3/final_run/consolidated/*.csv`
- `out/case5_ape_linbo3/final_run/plots/*.svg`
- `out/case6_ti_linbo3/final_run/consolidated/*.csv`
- `out/case6_ti_linbo3/final_run/plots/*.svg`
- `ai_logs/2024-05-21_gemini_auditoria_final.md`
- `ai_logs/2026-05-14_claude_auditoria_documental_final.md`
- `ai_logs/2026-05-14_codex_auditoria_tecnica_final.md`
- `ai_logs/2026-05-14_conselho_ias_plano_finalizacao.md`

## 7. Próxima ação recomendada

Próxima frente sugerida: validação quantitativa dos Casos 4-6.

Tarefa: anexar ou digitalizar curvas de referência para Figs. 5, 6 e 7, gerar overlays nos scripts de plot e registrar métricas de erro. Em paralelo, auditar a ativação de `delta_x/delta_z` no perfil circular do Caso 3 e estudar a convergência de malha da extração `W_x/W_y` no Caso 6.
