# Plano Consolidado de Finalização

**Data:** 2026-05-14  
**Consolidador:** Codex  
**Fontes:** `ai_logs/2024-05-21_gemini_auditoria_final.md`, `ai_logs/2026-05-14_claude_auditoria_documental_final.md`, `ai_logs/2026-05-14_codex_auditoria_tecnica_final.md`

## 1. Veredito geral

O projeto está **parcialmente pronto**.

A base técnica compila, a suíte passa quando o binário correto do CTest é usado (`/usr/bin/ctest`), e os Casos 1 e 2 já têm pipelines que geram CSV e figura. O Caso 2 é o único caso atualmente pronto como reprodução final: tem CSV, figura e comparação analítica no pipeline. O Caso 1 é reprodutível, mas ainda não validado numericamente contra a Fig. 1 por causa da pendência de geometria/documentação. O Caso 3 já executa como modelo pontual e gera CSV, mas não tem sweep, figura nem CTest de artefatos. Os Casos 4, 5 e 6 ainda não estão implementados como reprodução.

Casos já prontos:

- Caso 2 - Fig. 2: guia planar isotrópico difundido, com CSV, figura e referência analítica.

Casos implementados ou reprodutíveis, mas ainda não prontos:

- Caso 1 - Fig. 1: CSV e figura existem, mas a validação final depende de resolver a geometria `cover_index`/`substrate_index`.
- Caso 3 - Fig. 4: solver e YAML existem; execução pontual gera CSV; faltam sweep, figura, CTest dedicado e auditoria do TODO `delta_x`/`delta_z`.

Casos faltantes:

- Caso 4 - Fig. 5: perfil Gaussian-Gaussian ainda depende da forma analítica de `f(x,y)`.
- Caso 5 - Fig. 6: APE em LiNbO3 ainda não implementado.
- Caso 6 - Fig. 7: Ti:LiNbO3 ainda não implementado.

## 2. Matriz de reprodução

| Caso | Figura | Status atual | O que falta | Responsável sugerido |
|---|---|---|---|---|
| Caso 1 - guia homogêneo isotrópico | Fig. 1 | Parcial: executa, gera CSV e SVG; validação numérica ainda preliminar | Resolver geometria buried/surface, regenerar curva e atualizar `docs/03` | Claude |
| Caso 2 - guia planar isotrópico difundido | Fig. 2 | Pronto: executa, gera CSV e SVG, possui comparação analítica | Incluir no relatório final e manter em regressão | Claude |
| Caso 3 - canal isotrópico circular | Fig. 4 | Parcial: modelo, YAML e CSV pontual existem; sem figura | Auditar `delta_x`/`delta_z`, criar CTest dedicado, sweep, consolidação e plot | Codex + Claude |
| Caso 4 - canal Gaussian-Gaussian | Fig. 5 | Faltando | Recuperar/documentar `f(x,y)` da referência [12], depois implementar perfil, caso, testes e figura | Gemini + Codex |
| Caso 5 - APE LiNbO3 | Fig. 6 | Faltando | Preparar contrato anisotrópico exercitado, implementar perfil APE, YAML, sweep, CSV e figura | Gemini + Codex |
| Caso 6 - Ti:LiNbO3 | Fig. 7 | Faltando | Preparar parâmetros ordinário/extraordinário, implementar perfil Ti, YAML, sweep, CSV e figura | Gemini + Codex |

## 3. TODO por fases

### Fase A - Correções de build e testes

- [ ] T-001 — Criar comando reprodutível de testes
  - Responsável: Codex
  - Arquivos: `scripts/test.sh` (a criar), `README.md`, `tests/README.md`
  - Critério de aceite: `./scripts/test.sh` executa `/usr/bin/ctest --test-dir build --output-on-failure` e evita o wrapper Python quebrado em `/home/sperotto/.local/bin/ctest`.
  - Comando de teste: `./scripts/test.sh`

- [ ] T-002 — Adicionar CTest smoke dedicado ao Caso 3
  - Responsável: Codex
  - Arquivos: `CMakeLists.txt`, `tests/check_case3_outputs.py` ou `tests/check_case3_outputs.cmake`
  - Critério de aceite: a suíte CTest executa `cases/channel_diffused_isotropic_case.yaml` e verifica `neff.csv`, `dispersion_curve_points.csv` e `nodal_material_fields.csv`.
  - Comando de teste: `/usr/bin/ctest --test-dir build --output-on-failure -R case3`

- [ ] T-003 — Atualizar documentação curta da suíte de testes
  - Responsável: Codex
  - Arquivos: `tests/README.md`, `README.md`
  - Critério de aceite: a documentação informa 17 testes atuais, o novo teste do Caso 3 quando criado, e o uso de `/usr/bin/ctest` ou `./scripts/test.sh`.
  - Comando de teste: `/usr/bin/ctest --test-dir build --output-on-failure`

### Fase B - Fechamento dos casos numéricos

- [ ] T-004 — Resolver a geometria do Caso 1
  - Responsável: Claude
  - Arquivos: `cases/homogeneous_channel_isotropic_case.yaml`, `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`, `scripts/run_case1_homogeneous_channel_sweep.py`
  - Critério de aceite: fica documentado se a Fig. 1 usa guia buried simétrico ou superfície assimétrica; o YAML é ajustado apenas se a hipótese for confirmada; a nova curva reduz a discrepância sem mascarar o método.
  - Comando de teste: `python3 scripts/run_case1_homogeneous_channel_sweep.py --smoke --output-root build/test_output/case1_geometry_check`

- [ ] T-005 — Auditar o termo F4 no Caso 3
  - Responsável: Claude
  - Arquivos: `docs/02_formulacao_por_elementos_finitos.md`, `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`, `src/material_profile.cpp`, `src/local_assembly.cpp`
  - Critério de aceite: a decisão sobre `delta_x` e `delta_z` no perfil circular fica registrada com justificativa; se a documentação não sustentar mudança, manter o caso conservador e registrar TODO explícito.
  - Comando de teste: verificação documental e `build/waveguide_global_tests`

- [ ] T-006 — Criar pipeline completo da Fig. 4
  - Responsável: Codex
  - Arquivos: `scripts/run_case3_channel_diffused_sweep.py`, `scripts/consolidate_case3_channel_diffused_sweep.py`, `scripts/plot_case3_channel_diffused_sweep.py`, `tests/check_case3_sweep_outputs.py`
  - Critério de aceite: o Caso 3 gera CSV consolidado e SVG tipo Fig. 4; o status da figura indica explicitamente se F4 foi auditado.
  - Comando de teste: `python3 scripts/run_case3_channel_diffused_sweep.py --smoke --output-root build/test_output/case3_sweep`

- [ ] T-007 — Recuperar a fórmula do Caso 4
  - Responsável: Gemini
  - Arquivos: `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`, `docs/08_referencias.md`, eventual nota em `ai_logs/`
  - Critério de aceite: a forma analítica de `f(x,y)` é registrada com fonte rastreável; sem fonte, o Caso 4 permanece formalmente bloqueado.
  - Comando de teste: verificação manual da referência e da nota técnica

- [ ] T-008 — Implementar o Caso 4 após recuperar `f(x,y)`
  - Responsável: Codex
  - Arquivos: `include/waveguide_solver/material_profile.hpp`, `src/material_profile.cpp`, `src/config.cpp`, `src/global_assembly.cpp`, `src/app.cpp`, `cases/case4_gaussian_gaussian_channel.yaml`, `tests/global_tests.cpp`
  - Critério de aceite: perfil implementado sem fórmula inventada, YAML executa, teste de sanidade passa e gera CSV pontual.
  - Comando de teste: `cmake --build build -j && build/waveguide_global_tests`

- [ ] T-009 — Criar contrato de material anisotrópico exercitado
  - Responsável: Codex
  - Arquivos: `include/waveguide_solver/material_profile.hpp`, `src/material_profile.cpp`, `tests/global_tests.cpp`
  - Critério de aceite: há teste mínimo mostrando que material com `nx2 != nz2` produz montagem diferente do equivalente isotrópico, sem misturar ainda os perfis APE/Ti.
  - Comando de teste: `cmake --build build -j && build/waveguide_global_tests`

- [ ] T-010 — Consolidar tabela de parâmetros dos Casos 5 e 6
  - Responsável: Gemini
  - Arquivos: `docs/06_guia_de_onda_de_canal_difuso_anisotropico.md`, `docs/09_resumo_dos_casos_de_teste.md`, `ai_logs/`
  - Critério de aceite: todos os parâmetros necessários para APE e Ti:LiNbO3 estão listados, com unidade, símbolo, fonte e lacunas explícitas.
  - Comando de teste: verificação manual das tabelas

- [ ] T-011 — Implementar o Caso 5, APE LiNbO3
  - Responsável: Codex
  - Arquivos: `src/material_profile.cpp`, `src/config.cpp`, `src/global_assembly.cpp`, `src/app.cpp`, `cases/case5_ape_linbo3.yaml`, `tests/global_tests.cpp`
  - Critério de aceite: o solver executa pelo menos um ponto da Fig. 6, gera CSV e deixa limitações da difusão anisotrópica documentadas.
  - Comando de teste: `bash scripts/run_case.sh cases/case5_ape_linbo3.yaml audit_case5`

- [ ] T-012 — Implementar o Caso 6, Ti:LiNbO3
  - Responsável: Codex
  - Arquivos: `src/material_profile.cpp`, `src/config.cpp`, `src/global_assembly.cpp`, `src/app.cpp`, `cases/case6_ti_linbo3.yaml`, `tests/global_tests.cpp`
  - Critério de aceite: o solver executa pelo menos um ponto da Fig. 7, gera CSV e separa corretamente parâmetros ordinário/extraordinário.
  - Comando de teste: `bash scripts/run_case.sh cases/case6_ti_linbo3.yaml audit_case6`

### Fase C - Geração de CSVs e figuras

- [ ] T-013 — Regenerar CSV e figura finais do Caso 1
  - Responsável: Gemini
  - Arquivos: `out/case1_homogeneous_channel/final_run/`
  - Critério de aceite: `reference_dispersion.csv`, `consolidated_curve.csv` e `fig1_like_reference.svg` são gerados após a decisão de geometria.
  - Comando de teste: `python3 scripts/plot_case1_homogeneous_channel_sweep.py --sweep-root out/case1_homogeneous_channel/final_run`

- [ ] T-014 — Fixar artefatos finais do Caso 2
  - Responsável: Gemini
  - Arquivos: `out/planar_diffuse_sweep/final_run/`
  - Critério de aceite: CSVs consolidados, comparação analítica e `fig2_like_reference.svg` existem em pasta final reproduzível.
  - Comando de teste: `python3 scripts/plot_planar_diffuse_sweep.py --sweep-root out/planar_diffuse_sweep/final_run`

- [ ] T-015 — Gerar CSV e figura finais do Caso 3
  - Responsável: Gemini
  - Arquivos: `out/case3_channel_diffused_isotropic/final_run/`
  - Critério de aceite: CSV consolidado e `fig4_like_reference.svg` existem; o relatório marca claramente qualquer ressalva de F4.
  - Comando de teste: `python3 scripts/plot_case3_channel_diffused_sweep.py --sweep-root out/case3_channel_diffused_isotropic/final_run`

- [ ] T-016 — Criar orquestradores finais de reprodução
  - Responsável: Codex
  - Arquivos: `scripts/run_all.sh`, `scripts/plot_all.py`
  - Critério de aceite: um comando roda os casos implementados e outro gera/consolida as figuras disponíveis, sem fingir que Casos 4-6 estão prontos.
  - Comando de teste: `bash scripts/run_all.sh && python3 scripts/plot_all.py`

### Fase D - Documentação científica

- [ ] T-017 — Atualizar `docs/03` com o estado real do Caso 1
  - Responsável: Claude
  - Arquivos: `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`
  - Critério de aceite: a tabela antiga com resultados pré-correção não aparece como resultado atual; a seção explica geometria, desvios e limites da comparação.
  - Comando de teste: verificação manual

- [ ] T-018 — Atualizar `docs/09` com a matriz real dos casos
  - Responsável: Claude
  - Arquivos: `docs/09_resumo_dos_casos_de_teste.md`
  - Critério de aceite: Caso 2 aparece como pronto; Caso 1 como parcial; Caso 3 como solver/ponto implementado mas sem figura; Casos 4-6 como pendentes.
  - Comando de teste: verificação manual

- [ ] T-019 — Documentar o Caso 3 depois do sweep
  - Responsável: Claude
  - Arquivos: `docs/05_guia_de_onda_de_canal_difuso_isotropico.md`, `RESULTADOS_REPRODUCAO.md`
  - Critério de aceite: parâmetros, fórmula usada, artefatos e ressalva de F4 aparecem de forma auditável.
  - Comando de teste: verificação manual

### Fase E - Relatório final

- [ ] T-020 — Escrever `RESULTADOS_REPRODUCAO.md`
  - Responsável: Claude
  - Arquivos: `RESULTADOS_REPRODUCAO.md`
  - Critério de aceite: o relatório lista metodologia, comandos, tabelas, CSVs e figuras dos casos prontos; casos pendentes são declarados como pendentes, não como validados.
  - Comando de teste: `/usr/bin/ctest --test-dir build --output-on-failure`

### Fase F - Limpeza final do repositório

- [ ] T-021 — Atualizar `README.md`
  - Responsável: Gemini
  - Arquivos: `README.md`
  - Critério de aceite: README inclui estado por caso, comandos reais, dependências e caminho dos artefatos finais.
  - Comando de teste: verificação manual

- [ ] T-022 — Limpar e organizar saídas finais
  - Responsável: Codex
  - Arquivos: `out/README.md`, `out/case1_homogeneous_channel/final_run/`, `out/planar_diffuse_sweep/final_run/`, `out/case3_channel_diffused_isotropic/final_run/`
  - Critério de aceite: saídas exploratórias ficam separadas das saídas finais; nenhum resultado solto na raiz é necessário para reproduzir o relatório.
  - Comando de teste: `find out -maxdepth 3 -type f | sort`

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
- Criar o CTest do Caso 3, pipelines de sweep/plot, orquestradores finais e perfis materiais futuros quando a fórmula estiver documentada.

## 5. Comandos finais esperados

Comandos reais disponíveis hoje:

```bash
cmake -S . -B build
cmake --build build -j
/usr/bin/ctest --test-dir build --output-on-failure

python3 scripts/run_case1_homogeneous_channel_sweep.py --output-root out/case1_homogeneous_channel/final_run
python3 scripts/consolidate_case1_homogeneous_channel_sweep.py --sweep-root out/case1_homogeneous_channel/final_run
python3 scripts/plot_case1_homogeneous_channel_sweep.py --sweep-root out/case1_homogeneous_channel/final_run

python3 scripts/run_planar_diffuse_sweep.py --output-root out/planar_diffuse_sweep/final_run
python3 scripts/consolidate_planar_diffuse_sweep.py --sweep-root out/planar_diffuse_sweep/final_run
python3 scripts/plot_planar_diffuse_sweep.py --sweep-root out/planar_diffuse_sweep/final_run

bash scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml final_point_case3
```

Comandos esperados ao final das tarefas:

```bash
./scripts/test.sh
bash scripts/run_all.sh
python3 scripts/plot_all.py

python3 scripts/run_case3_channel_diffused_sweep.py --output-root out/case3_channel_diffused_isotropic/final_run
python3 scripts/consolidate_case3_channel_diffused_sweep.py --sweep-root out/case3_channel_diffused_isotropic/final_run
python3 scripts/plot_case3_channel_diffused_sweep.py --sweep-root out/case3_channel_diffused_isotropic/final_run
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
- `cases/case4_gaussian_gaussian_channel.yaml` - a criar quando a fórmula estiver definida.
- `cases/case5_ape_linbo3.yaml` - a criar.
- `cases/case6_ti_linbo3.yaml` - a criar.
- `scripts/build.sh`
- `scripts/test.sh` - a criar.
- `scripts/run_case.sh`
- `scripts/run_all.sh` - a criar.
- `scripts/plot_all.py` - a criar.
- `scripts/run_case1_homogeneous_channel_sweep.py`
- `scripts/consolidate_case1_homogeneous_channel_sweep.py`
- `scripts/plot_case1_homogeneous_channel_sweep.py`
- `scripts/run_planar_diffuse_sweep.py`
- `scripts/consolidate_planar_diffuse_sweep.py`
- `scripts/plot_planar_diffuse_sweep.py`
- `scripts/run_case3_channel_diffused_sweep.py` - a criar.
- `scripts/consolidate_case3_channel_diffused_sweep.py` - a criar.
- `scripts/plot_case3_channel_diffused_sweep.py` - a criar.
- `tests/check_case3_outputs.py` ou `tests/check_case3_outputs.cmake` - a criar.
- `tests/check_case3_sweep_outputs.py` - a criar.
- `out/case1_homogeneous_channel/final_run/consolidated/*.csv`
- `out/case1_homogeneous_channel/final_run/plots/*.svg`
- `out/planar_diffuse_sweep/final_run/consolidated/*.csv`
- `out/planar_diffuse_sweep/final_run/plots/*.svg`
- `out/case3_channel_diffused_isotropic/final_run/consolidated/*.csv` - após T-006.
- `out/case3_channel_diffused_isotropic/final_run/plots/*.svg` - após T-006.
- `ai_logs/2024-05-21_gemini_auditoria_final.md`
- `ai_logs/2026-05-14_claude_auditoria_documental_final.md`
- `ai_logs/2026-05-14_codex_auditoria_tecnica_final.md`
- `ai_logs/2026-05-14_conselho_ias_plano_finalizacao.md`

## 7. Próxima ação recomendada

Próximo prompt recomendado: enviar para **Codex**.

Tarefa: **T-001 — Criar comando reprodutível de testes**.

Motivo: a única falha objetiva da auditoria técnica é o comando literal `ctest`, que cai no wrapper Python quebrado do PATH. É uma correção pequena, segura e desbloqueia uma base limpa para os próximos patches. Depois dela, o próximo patch técnico deve ser T-002, o CTest dedicado do Caso 3.

Prompt sugerido:

```text
Implemente T-001 do TODO.md: crie scripts/test.sh para executar /usr/bin/ctest --test-dir build --output-on-failure, atualize README.md e tests/README.md com o comando correto, rode cmake -S . -B build, cmake --build build -j e ./scripts/test.sh. Não altere comportamento numérico.
```
