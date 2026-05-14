# Log de Redação — Relatório Final de Resultados

**Data:** 2026-05-14
**Redator:** Claude (Sonnet 4.6)
**Produto:** `RESULTADOS_REPRODUCAO.md`

---

## Arquivos consultados

| Arquivo | Propósito |
|---|---|
| `README.md` | Comandos de build e testes |
| `TODO.md` | Estado de tarefas pendentes |
| `PLANS.md` | Histórico de decisões do projeto |
| `docs/02_formulacao_por_elementos_finitos.md` | Formulação FEM (equações 1–4) |
| `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md` | Parâmetros e estado do Caso 1 |
| `docs/04_guia_de_onda_planar_difuso_isotropico.md` | Parâmetros do Caso 2 |
| `docs/05_guia_de_onda_de_canal_difuso_isotropico.md` | Parâmetros dos Casos 3 e 4 |
| `docs/06_guia_de_onda_de_canal_difuso_anisotropico.md` | Parâmetros dos Casos 5 e 6 |
| `ai_logs/2026-05-14_claude_auditoria_documental_final.md` | Diagnósticos desta sessão |
| `ai_logs/2026-05-14_codex_auditoria_tecnica_final.md` | Estado de build, testes e scripts |
| `cases/homogeneous_channel_isotropic_case.yaml` | Configuração usada nos testes do Caso 1 |
| `cases/channel_diffused_isotropic_case.yaml` | Configuração usada no Caso 3 pontual |
| `src/material_profile.cpp` | Verificação do TODO delta_x/delta_z do Caso 3 |

## Resultados usados no relatório

### Caso 1 — dados do CTest smoke

**Fonte:** `build/test_output/case1_sweep/consolidated/reference_comparison.csv`

| V | B_ref | B_calc | Erro |
|---|---|---|---|
| 1.2 | 0.350 | 0.502 | +43.5% |
| 2.0 | 0.675 | 0.735 | −8.9% |
| 4.0 | 0.910 | 0.910 | +0.05% |

Nota: esses dados foram gerados com a malha smoke (`channel_a2b_b1_smoke.mesh`, 16 nós livres) e `cover_index = 1.0`. O run `reference_run_v4_mode_tracking` em `out/` usa a malha de referência mas o CSV de comparação consolidada nesse diretório apresenta `B_calc = 0` para V < 2.4, sugerindo que foi gerado antes da correção do Jacobi (commit `514e678`). **Os dados do CTest são os mais confiáveis e recentes.**

### Caso 2 — dados do run refinado

**Fonte:** `out/planar_diffuse_sweep/case2_exact_refined/consolidated/fem_vs_exact_comparison.csv`

- 26 pontos de comparação (TE0, TE1, TE2)
- k0d de 10 a 150
- Erro máximo: 0.0017%
- Fonte analítica: equação exata de transferência de matrizes, referência [19] do artigo

### Caso 3 — dados do run pontual

**Fonte:** `out/case03_channel_diffused_isotropic/results/neff.csv` e `material_profile_summary.txt`

- k0·b = 21.265341 µm⁻¹
- n_eff = 1.473429
- Parâmetros: n2=1.44, n3m=1.50, a=2, b=1
- Nota: B = 0.552 usando n3m como referência; B > 1 se usar n3av=1.47 (modo próximo ao pico do perfil)

---

## Limitações encontradas durante a redação

1. **Ausência de figura de saída para Casos 3–6:** Nenhum SVG ou PNG foi gerado para as Figs. 4–7 do artigo. Documentado como MISSING e PARTIAL conforme a situação.

2. **CSV de comparação do Caso 1 desatualizado em `out/`:** O arquivo `out/case1_homogeneous_channel/reference_run_v4_mode_tracking/consolidated/reference_comparison.csv` mostra `B_calc = 0` para V < 2.4 — evidência de que o sweep desse diretório foi gerado com o eigensolver pré-correção do Jacobi. O relatório usa exclusivamente os dados do CTest (`build/test_output/case1_sweep/`), que são os mais recentes.

3. **Ambiguidade no B do Caso 3:** Com n_eff = 1.473 e n3av = 1.47 como denominador, B > 1 (sem sentido físico). O modo calculado está acima de n3av, o que pode ocorrer porque n3av é a média e o pico é 1.50. Usando n3m = 1.50, B = 0.552. O artigo usa n3av = 1.47 na normalização da Fig. 4, o que implica que o solver está superestimando neff ou que a normalização precisa ser revisada.

4. **Sem dados tabulados para Casos 4–6:** O artigo apresenta apenas figuras gráficas para esses casos, sem tabelas. Toda comparação é visual.

5. **Covertura de ar vs. buried:** O TODO de geometria do Caso 1 impede classificar o resultado como válido. O relatório registra a hipótese mas não altera os valores nem inventa corrações.

---

## Pontos que precisam de conferência humana

1. **Geometria do Caso 1:** Verificar na referência [7] se a Fig. 1 usa guia buried (n_cover = n_substrate = 1.43) ou guia de superfície (n_cover = 1.0). Isso determina se o YAML precisa ser corrigido.

2. **Normalização da Fig. 4:** Verificar se n3av = 1.47 (índice médio do núcleo) é a referência correta para normalização de B, e por que o solver calcula n_eff > n3av no único ponto disponível.

3. **Ativação do termo F4 no Caso 3:** O TODO em `src/material_profile.cpp:309-314` indica que `delta_x` e `delta_z` foram desativados conservadoramente. A questão é se o perfil circular tem gradiente de material relevante para esses termos — decisão que requer leitura cuidadosa de `docs/02`.

4. **Dados de saída desatualizados em `out/`:** Antes de considerar os dados de `out/case1_homogeneous_channel/reference_run_v4_mode_tracking/` como canônicos, reexecutar o sweep com o solver atual (pós-correção do Jacobi).
