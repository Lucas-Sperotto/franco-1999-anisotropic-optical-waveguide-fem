# Auditoria Codex — Build, Testes e Implementação

Data da auditoria: 2026-05-14

Escopo: auditoria técnica do estado de build, testes, scripts de reprodução, artefatos CSV/figuras e lacunas de implementação para a reprodução do artigo de Franco, Passaro, Cardoso e Machado (1999).

## 1. Estado do Git

Comando executado:

```bash
git status --short
```

Saída resumida antes da criação deste relatório:

```text
?? ia_logs/
```

Após esta auditoria, também existe o novo arquivo de relatório em `ai_logs/`.

Observação: não havia modificação rastreada pendente no código-fonte no início da auditoria.

## 2. Build

Comandos executados:

```bash
cmake -S . -B build
cmake --build build -j
```

Resultado:

- configuração CMake: passou;
- compilação: passou;
- alvos construídos: `waveguide_core`, `waveguide_solver`, `waveguide_geometry_tests`, `waveguide_global_tests`.

Saída essencial:

```text
-- Configuring done
-- Generating done
-- Build files have been written to: .../build
[100%] Built target waveguide_solver
```

## 3. Testes

Comando solicitado executado literalmente:

```bash
ctest --test-dir build --output-on-failure
```

Resultado do comando literal: falhou por ambiente/PATH, antes de executar a suíte.

```text
Traceback (most recent call last):
  File "/home/sperotto/.local/bin/ctest", line 5, in <module>
    from cmake import ctest
ModuleNotFoundError: No module named 'cmake'
```

Diagnóstico: `ctest` no PATH aponta para `/home/sperotto/.local/bin/ctest`, um wrapper Python quebrado. O binário do sistema existe em `/usr/bin/ctest`.

Comando de auditoria efetivamente usado para testar a suíte:

```bash
/usr/bin/ctest --test-dir build --output-on-failure
```

Resultado:

```text
100% tests passed, 0 tests failed out of 17
```

Resumo:

- total de testes CTest: 17;
- aprovados: 17;
- falhas da suíte: 0;
- falha externa bloqueante do comando literal: wrapper `ctest` do PATH.

Testes CTest registrados:

```text
waveguide_solver_help
waveguide_solver_smoke
waveguide_solver_planar_smoke
waveguide_solver_case1_smoke
waveguide_geometry_tests
waveguide_global_tests
waveguide_solver_smoke_artifacts
waveguide_solver_planar_smoke_artifacts
waveguide_solver_case1_smoke_artifacts
waveguide_planar_sweep_smoke
waveguide_planar_sweep_consolidate
waveguide_planar_sweep_plot
waveguide_planar_sweep_artifacts
waveguide_case1_sweep_smoke
waveguide_case1_sweep_consolidate
waveguide_case1_sweep_plot
waveguide_case1_sweep_artifacts
```

## 4. Scripts de reprodução

Inventário resumido:

- `scripts/build.sh`
- `scripts/run_case.sh`
- `scripts/run_case1_homogeneous_channel_sweep.py`
- `scripts/consolidate_case1_homogeneous_channel_sweep.py`
- `scripts/plot_case1_homogeneous_channel_sweep.py`
- `scripts/run_planar_diffuse_sweep.py`
- `scripts/consolidate_planar_diffuse_sweep.py`
- `scripts/plot_planar_diffuse_sweep.py`
- `scripts/generate_case1_marcatili_reference.py`
- `scripts/check_case1_pi_hypothesis.py`
- `scripts/investigate_case1_convergence.py`
- `scripts/generate_planar_strip_mesh.py`
- `scripts/planar_exact_reference.py`

Diretórios consultados:

- `apps/`: não existe;
- `data/`: não existe;
- `tests/`: existe;
- `out/`: existe e contém muitos artefatos gerados.

Artefatos gerados encontrados:

- SVGs gerados: 7 arquivos;
- PNGs gerados: 1 arquivo auxiliar;
- CSVs em `out/` e `build/test_output/`: 3672 arquivos, incluindo muitos intermediários de sweeps.

O script genérico também foi testado para o Caso 3:

```bash
scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml audit_case3
```

Resultado: passou, gerando saída em:

```text
out/channel_diffused_isotropic_case/audit_case3/
```

Tabela por figura/caso:

| Caso | Figura | Executável | Script run | CSV | Figura | Teste | Status |
| ---- | ------ | ---------- | ---------- | --- | ------ | ----- | ------ |
| Caso 1: canal isotrópico homogêneo | Fig. 1 | `build/waveguide_solver` | `scripts/run_case1_homogeneous_channel_sweep.py` | `build/test_output/case1_sweep/consolidated/reference_dispersion.csv`, `build/test_output/case1_sweep/consolidated/consolidated_curve.csv` | `build/test_output/case1_sweep/plots/fig1_like_reference.svg` | `waveguide_case1_sweep_smoke`, `waveguide_case1_sweep_consolidate`, `waveguide_case1_sweep_plot`, `waveguide_case1_sweep_artifacts` | Reprodutível com CSV e SVG; validação numérica ainda preliminar conforme documentação do Caso 1. |
| Caso 2: planar difuso isotrópico | Fig. 2 | `build/waveguide_solver` | `scripts/run_planar_diffuse_sweep.py` | `build/test_output/planar_sweep/consolidated/reference_dispersion.csv`, `build/test_output/planar_sweep/consolidated/consolidated_modes.csv`, `build/test_output/planar_sweep/consolidated/analytic_reference.csv`, `build/test_output/planar_sweep/consolidated/fem_vs_exact_comparison.csv` | `build/test_output/planar_sweep/plots/fig2_like_reference.svg`, `build/test_output/planar_sweep/plots/mode1_sensitivity.svg` | `waveguide_planar_sweep_smoke`, `waveguide_planar_sweep_consolidate`, `waveguide_planar_sweep_plot`, `waveguide_planar_sweep_artifacts` | Reprodutível com CSV e SVG; possui referência analítica TE no pipeline. |
| Caso 3: canal difuso isotrópico circular | Fig. 4 | `build/waveguide_solver` | `scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml audit_case3` | `out/channel_diffused_isotropic_case/audit_case3/results/dispersion_curve_points.csv`, `out/channel_diffused_isotropic_case/audit_case3/results/neff.csv` | Não há figura gerada para Fig. 4 | `waveguide_global_tests` cobre sanidade de matriz e faixa de `n_eff`; não há CTest dedicado de artefatos Fig. 4 | Parcial. O modelo executa e gera CSV de ponto/caso, mas não há sweep, consolidação nem plot da Fig. 4. Não considerar validado. |
| Caso 4: canal difuso isotrópico Gaussian-Gaussian | Fig. 5 | Não implementado | Não existe | Não existe | Não existe | Não existe | Não implementado. A documentação registra que a função `f(x,y)` não está explicitada no texto consolidado. |
| Caso 5: guia anisotrópico APE em LiNbO3 | Fig. 6 | Não implementado | Não existe | Não existe | Não existe | Não existe | Não implementado. |
| Caso 6: guia anisotrópico Ti:LiNbO3 | Fig. 7 | Não implementado | Não existe | Não existe | Não existe | Não existe | Não implementado. |

Observações importantes:

- `docs/img/fig_1.png` a `docs/img/fig_7.png` são figuras documentais de referência, não figuras geradas pelo pipeline.
- `tests/marcatili_ref/SG-006i.*` é referência auxiliar ligada a Marcatili/figura externa, não reprodução das Figs. 6 ou 7 do artigo de Franco et al.
- Não há script dedicado para Fig. 4, Fig. 5, Fig. 6 ou Fig. 7.

## 5. Lacunas técnicas

1. O comando literal `ctest` está quebrado por PATH.
   - `/home/sperotto/.local/bin/ctest` falha com `ModuleNotFoundError: No module named 'cmake'`.
   - `/usr/bin/ctest` funciona e a suíte passa.

2. Caso 3 ainda não tem pipeline completo de figura.
   - Existe modelo `channel_diffused_isotropic_circular`.
   - Existe YAML `cases/channel_diffused_isotropic_case.yaml`.
   - Existe CSV de execução pontual.
   - Falta sweep em frequência normalizada, consolidação e plot tipo Fig. 4.
   - Falta CTest dedicado para artefatos do Caso 3.

3. Caso 3 contém TODO técnico no modelo material.
   - A implementação atual registra ambiguidade sobre origem/orientação geométrica do perfil circular.
   - Os termos derivativos `delta_x/delta_z` foram diferidos até auditoria da convenção do termo `F4`.
   - Portanto, o Caso 3 não deve ser marcado como validado contra o artigo.

4. Caso 1 tem pipeline completo, mas validação numérica ainda é preliminar.
   - A documentação do Caso 1 registra discrepâncias com pontos visuais aproximados perto do corte.
   - Há CSV e SVG, mas isso não equivale a validação final.

5. Caso 4 não pode ser implementado fielmente sem recuperar a forma analítica completa de `f(x,y)`.
   - A própria documentação em `docs/05...` registra essa lacuna.

6. Casos 5 e 6 não têm infraestrutura material anisotrópica específica.
   - Faltam modelos APE e Ti-difundido, casos YAML, sweeps, CSVs, figuras e testes.

7. Não existem diretórios `apps/` ou `data/`.
   - Isso não quebra o build, mas qualquer instrução externa que espere esses diretórios falhará.

## 6. Correções mínimas recomendadas

1. Corrigir o problema de PATH do `ctest`.
   - Opção local: chamar `/usr/bin/ctest` nos comandos documentados.
   - Opção de ambiente: remover/corrigir `/home/sperotto/.local/bin/ctest` ou instalar o módulo Python `cmake` compatível.

2. Adicionar CTest dedicado para o Caso 3.
   - Rodar `waveguide_solver` com `cases/channel_diffused_isotropic_case.yaml`.
   - Checar artefatos mínimos: `neff.csv`, `dispersion_curve_points.csv`, `nodal_material_fields.csv`.

3. Criar scripts mínimos para Fig. 4.
   - `run_case3_channel_diffused_sweep.py`
   - `consolidate_case3_channel_diffused_sweep.py`
   - `plot_case3_channel_diffused_sweep.py`

4. Registrar explicitamente no README/cases README o status do Caso 3.
   - “Executa e gera CSV pontual; sem figura consolidada; não validado.”

5. Antes do Caso 4, recuperar a definição de `f(x,y)`.
   - Não implementar Gaussian-Gaussian por aproximação não documentada.

6. Antes dos Casos 5 e 6, criar uma etapa pequena para o contrato de material anisotrópico.
   - Não misturar APE/Ti com refatoração ampla do solver.

## 7. Plano de implementação incremental

* T-001 — Corrigir comando de testes reprodutível

  * Objetivo: garantir que o comando documentado de testes use o CTest funcional.
  * Arquivos: `README.md`, possivelmente `scripts/build.sh` ou novo script pequeno `scripts/test.sh`.
  * Critério de aceite: o usuário consegue rodar a suíte sem cair no wrapper Python quebrado.
  * Comando de teste: `/usr/bin/ctest --test-dir build --output-on-failure`.

* T-002 — Adicionar CTest smoke do Caso 3

  * Objetivo: colocar o Caso 3 no mesmo nível mínimo de execução dos Casos 1 e 2 base.
  * Arquivos: `CMakeLists.txt`, `tests/check_smoke_outputs.cmake` ou novo `tests/check_case3_outputs.py`.
  * Critério de aceite: CTest roda `cases/channel_diffused_isotropic_case.yaml` e verifica CSVs mínimos.
  * Comando de teste: `/usr/bin/ctest --test-dir build --output-on-failure -R case3`.

* T-003 — Criar sweep reprodutível da Fig. 4

  * Objetivo: amostrar a frequência normalizada do Caso 3 e consolidar os pontos do modo fundamental.
  * Arquivos: `scripts/run_case3_channel_diffused_sweep.py`, `cases/channel_diffused_isotropic_case.yaml`.
  * Critério de aceite: gera `point_manifest.csv` e pontos com `dispersion_curve_points.csv` por frequência.
  * Comando de teste: `python3 scripts/run_case3_channel_diffused_sweep.py --smoke --output-root build/test_output/case3_sweep`.

* T-004 — Consolidar CSV da Fig. 4

  * Objetivo: transformar os pontos do sweep do Caso 3 em CSV único nas grandezas da Fig. 4.
  * Arquivos: `scripts/consolidate_case3_channel_diffused_sweep.py`.
  * Critério de aceite: gera `consolidated/reference_dispersion.csv` ou nome equivalente, com frequência normalizada e constante de propagação normalizada.
  * Comando de teste: `python3 scripts/consolidate_case3_channel_diffused_sweep.py --sweep-root build/test_output/case3_sweep`.

* T-005 — Plotar Fig. 4

  * Objetivo: gerar SVG tipo Fig. 4 a partir do CSV consolidado.
  * Arquivos: `scripts/plot_case3_channel_diffused_sweep.py`, `tests/check_case3_sweep_outputs.py`.
  * Critério de aceite: gera `plots/fig4_like_reference.svg` e CTest verifica sua existência.
  * Comando de teste: `python3 scripts/plot_case3_channel_diffused_sweep.py --sweep-root build/test_output/case3_sweep`.

* T-006 — Resolver fórmula do Caso 4

  * Objetivo: recuperar a forma analítica de `f(x,y)` antes de qualquer código Gaussian-Gaussian.
  * Arquivos: `docs/05_guia_de_onda_de_canal_difuso_isotropico.md` apenas com observação técnica justificada, mais futuras interfaces de material.
  * Critério de aceite: fórmula documentada com fonte rastreável.
  * Comando de teste: não aplicável até haver implementação.

* T-007 — Introduzir contrato anisotrópico para Casos 5 e 6

  * Objetivo: preparar materiais com `nx2`, `nz2`, `gz2` espacialmente variáveis sem acoplar a lógica ao YAML bruto.
  * Arquivos: `include/waveguide_solver/material_profile.hpp`, `src/material_profile.cpp`, `tests/global_tests.cpp`.
  * Critério de aceite: teste unitário de material anisotrópico mínimo, sem tentar reproduzir Fig. 6/7 ainda.
  * Comando de teste: `cmake --build build -j && build/waveguide_global_tests`.

## 8. Próximo patch recomendado

Próximo patch recomendado: **T-002 — Adicionar CTest smoke do Caso 3**.

Justificativa:

- O Caso 3 já tem modelo, YAML e execução pontual.
- Ainda não está protegido por um CTest dedicado de artefatos.
- É pequeno, seguro e reversível.
- Fecha a lacuna imediata entre “o solver roda manualmente” e “o projeto garante reprodutibilidade mínima no CI/local”.
- Não exige inventar fórmula nova nem resolver ainda o sweep completo da Fig. 4.

Critério do patch:

```bash
cmake -S . -B build
cmake --build build -j
/usr/bin/ctest --test-dir build --output-on-failure
```

Resultado esperado após o patch:

- a suíte continua passando;
- aparece teste CTest específico do Caso 3;
- os CSVs mínimos do Caso 3 são verificados automaticamente.
