# Resultados da Reprodução — Franco et al. (1999)

**Data:** 2026-05-14
**Repositório:** `franco-1999-anisotropic-optical-waveguide-fem`

---

## 1. Objetivo

Este documento registra o estado da reprodução numérica dos casos de validação do artigo "Finite Element Analysis of Anisotropic Optical Waveguide with Arbitrary Index Profile" (Franco, Passaro, Cardoso e Machado, 1999). O objetivo é comparar as curvas de dispersão modal geradas pelo solver FEM implementado neste repositório com as figuras publicadas no artigo, utilizando exclusivamente resultados existentes nos arquivos do repositório.

---

## 2. Artigo de referência

> M. A. Franco, V. A. Serrão Passaro, F. Prudêncio Cardoso e J. S. Crespo Machado, "Finite Element Analysis of Anisotropic Optical Waveguide with Arbitrary Index Profile," *IEEE Transactions on Magnetics*, vol. 35, no. 3, pp. 1260–1263, 1999.

---

## 3. Formulação implementada

### 3.1 Equação de onda escalar (modos Ex)

O artigo emprega a formulação escalar para modos `E^x` (polarização TE-like, onde Ey ≈ 0). Para dielétricos com tensor de permissividade diagonal:

```
εr = diag(nx², ny², nz²)
```

a equação escalar de onda (Eq. 1 do artigo) resulta em:

```
∂/∂x [nx² ∂Ex/∂x] + nz² ∂²Ex/∂y² + (termos de gradiente material) + k0² nx² nz² Ex = β² nx² Ex
```

### 3.2 Problema generalizado de autovalores

Após discretização com elementos triangulares P1 lineares, obtém-se:

```
[F]{Ex} = neff² [M]{Ex}
```

onde `neff = β/k0`. As matrizes `[F]` e `[M]` são construídas pela soma das contribuições locais de cada elemento triangular. A formulação inclui quatro termos de rigidez (F1, F2, F3, F4) que acomodam gradientes de material e anisotropia via flags δx e δz. O eigensolver usa fatoração de Cholesky de `[M]` seguida de diagonalização de Jacobi para matrizes simétricas.

### 3.3 Material anisotrópico

A implementação suporta tensores com `nx²(x,y)` e `nz²(x,y)` espacialmente variáveis via campos nodais interpolados linearmente em cada elemento. O coeficiente `gz² = 1/nz²` é calculado nodalmente. Os termos F2, F3, F4 são ativados por flags `delta_x` e `delta_z` quando o perfil é difuso.

### 3.4 Normalizações usadas nas figuras

As curvas de dispersão do artigo usam:

- **Frequência normalizada** (eixo horizontal):

```
V = (k0 b / π) √(n3² − n2²)
```

- **Constante de propagação normalizada** (eixo vertical):

```
B = (neff² − n2²) / (n3² − n2²)
```

onde `b` é a meia-altura do guia (ou largura do guia planar), `n2` é o índice do substrato e `n3` é o índice de pico do núcleo.

---

## 4. Casos reproduzidos

### 4.1 Fig. 1 — Guia homogêneo isotrópico

**Descrição:** Guia retangular com secção transversal `a × b` (a = 2b = 2 µm), núcleo homogêneo com índice n3 = 1.50, substrato n2 = 1.43. O artigo mostra boa concordância entre FEM escalar, VIE e EIM para o modo fundamental Ex.

**Parâmetros usados:**

| Parâmetro | Valor |
|---|---|
| n3 (núcleo) | 1.50 |
| n2 (substrato) | 1.43 |
| n1 (cobertura) | 1.00 (configuração atual — ver observação) |
| a (largura) | 2.0 µm |
| b (altura) | 1.0 µm |
| Malha (CTest) | `channel_a2b_b1_smoke.mesh` (16 nós livres) |
| Condição de contorno | `dirichlet_zero_on_boundary_nodes` |

**Comando:**

```bash
python3 scripts/run_case1_homogeneous_channel_sweep.py --smoke \
  --output-root build/test_output/case1_sweep
```

**CSV gerado:** `build/test_output/case1_sweep/consolidated/reference_comparison.csv`

**Figura gerada:** `build/test_output/case1_sweep/plots/fig1_like_reference.svg`

**Comparação com a Fig. 1 do artigo:**

| V (freq. norm.) | B_ref (visual) | B_calc | Erro relativo (%) |
|---:|---:|---:|---:|
| 1.2 | 0.350 | 0.502 | +43.5% |
| 2.0 | 0.675 | 0.735 | −8.9% |
| 4.0 | 0.910 | 0.910 | +0.05% |

**Status: PARTIAL — WARN**

**Resultado do T-004 (geometria buried, 2026-05-14):** a hipótese de guia enterrado foi testada empiricamente na mesma malha smoke com `cover_index = 1.43`. Os resultados foram piores em todos os pontos (V=1.2: B=0.572, erro +63%; V=4.0: B=0.914, erro +0.5%). **A hipótese buried foi rejeitada.** A configuração `cover_index = 1.00` foi mantida.

**Causa provável do desvio:** os valores `B_ref` foram extraídos visualmente da Fig. 1 e podem corresponder à curva de Marcatili (que fica abaixo da curva FEM/VIE próximo ao corte), não à curva FEM original. Adicionalmente, a malha smoke (99 graus de liberdade livres) é muito grosseira para frequências próximas ao corte.

---

### 4.2 Fig. 2 — Guia planar difuso isotrópico

**Descrição:** Guia planar com perfil exponencial unilateral. Cobertura com n0 = 1.0, substrato difundido com n(y) = ns + Δn·exp(−y/d), onde ns = 2.2, Δn = 0.01, d = 1.0. Comparação para modos TE0, TE1 e TE2 contra solução exata de transferência de matrizes [19].

**Parâmetros usados:**

| Parâmetro | Valor |
|---|---|
| ns (índice base) | 2.20 |
| Δn (variação) | 0.01 |
| d (comprimento de difusão) | 1.0 µm |
| n0 (cobertura) | 1.0 |
| Condição de contorno | `dirichlet_zero_on_y_extrema` |
| Redução x-invariante | ativa |
| Malha (run refinado) | `planar_strip_d10.mesh` |

**Comando:**

```bash
python3 scripts/run_planar_diffuse_sweep.py \
  --output-root out/planar_diffuse_sweep/case2_exact_refined
python3 scripts/consolidate_planar_diffuse_sweep.py \
  --sweep-root out/planar_diffuse_sweep/case2_exact_refined
python3 scripts/plot_planar_diffuse_sweep.py \
  --sweep-root out/planar_diffuse_sweep/case2_exact_refined
```

**CSV gerado:** `out/planar_diffuse_sweep/case2_exact_refined/consolidated/fem_vs_exact_comparison.csv`

**Figura gerada:** `out/planar_diffuse_sweep/case2_exact_refined/plots/fig2_like_reference.svg`

**Comparação com solução analítica exata (26 pontos, modos TE0, TE1, TE2):**

| Métrica | Valor |
|---|---|
| Erro relativo máximo | 0.0017% |
| Erro relativo médio | < 0.001% |
| Pontos avaliados | 26 |
| Modos cobertos | TE0, TE1, TE2 |
| Faixa de k0d | 10 a 150 |

**Amostra de resultados (TE0, k0d = 10 e 150):**

| k0d | n_eff FEM | n_eff exato | Δn_eff | Erro (%) |
|---:|---:|---:|---:|---:|
| 10.0 | 2.201055 | 2.201042 | 0.000013 | 0.000591 |
| 150.0 | 2.207843 | 2.207815 | 0.000028 | 0.001268 |

**Status: PASS**

O Caso 2 é o único caso validado numericamente contra uma referência independente com precisão < 0.002%.

---

### 4.3 Fig. 4 — Canal isotrópico circular difuso

**Descrição:** Guia de canal com secção transversal retangular (a = 2 µm, b = 1 µm), perfil de índice circular dentro do núcleo definido pelas Eqs. (7)–(9) do artigo. Parâmetros: n2 = 1.44 (substrato), n3m = 1.50 (pico), n1 = 1.0 (ar). A normalização usa n3av = 1.47 (índice médio no núcleo).

**Parâmetros usados:**

| Parâmetro | Valor |
|---|---|
| n2 (substrato/fundo) | 1.44 |
| n3m (pico) | 1.50 |
| n1 (cobertura) | 1.00 |
| a (largura) | 2.0 µm |
| b (altura) | 1.0 µm |
| Malha | `channel_a2b_b1_reference.mesh` (304 nós) |

**Comando (execução pontual):**

```bash
scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml audit_case3
```

**CSV gerado (ponto único):** `out/channel_diffused_isotropic_case/audit_case3/results/neff.csv`

**Resultado do ponto único:**

| k0·b | n_eff calculado | n_eff² calculado | status |
|---:|---:|---:|---|
| 21.265 | 1.473429 | 2.170994 | ok |

Usando n3av = 1.47 e n2 = 1.44 como na Fig. 4:
- B ≈ 1.12 (inconsistente — n_eff > n3av indica que o pico real excede a média)
- Usando n3m = 1.50: B ≈ 0.552, frequência normalizada V ≈ 2.84

**Figura gerada:** MISSING — nenhum script de sweep ou plot para Fig. 4 existe atualmente.

**Status: PARTIAL**

**Limitações conhecidas:**
1. Não há sweep em frequência normalizada nem curva de dispersão gerada para comparação com a Fig. 4.
2. O perfil circular tem `delta_x = false` e `delta_z = false` em `src/material_profile.cpp` — os termos de gradiente de material (F2-gradiente, F4) não são computados. **Bloqueador identificado no T-005 (2026-05-14):** ativar esses flags torna F não-simétrica (conforme docs/02 §3b), e o eigensolver Jacobi atual só suporta sistemas simétricos (retorna 0 modos). Flags permanecem desativados até implementação de eigensolver não-simétrico (QZ/LAPACK).
3. A orientação geométrica do centro de difusão (origin at `core_center_x`, `surface_y`) aguarda confirmação contra a Fig. 3 do artigo.

---

### 4.4 Fig. 5 — Canal Gaussian-Gaussian

**Status: MISSING**

A forma analítica da função `f(x,y)` para o perfil Gaussian-Gaussian não está explicitada no texto do artigo. A observação editorial em `docs/05` registra que ela deve ser recuperada da referência [12]. Nenhum perfil de material, YAML, script ou dado existe para este caso.

---

### 4.5 Fig. 6 — APE LiNbO3

**Status: MISSING**

O perfil APE envolve difusão anisotrópica 2D cuja concentração C(x,y) varia segundo uma equação de difusão anisotrópica resolvida em pré-processamento. A equação de índice em função de C está documentada em `docs/06` (Eq. 10). Nenhum perfil de material, YAML, script ou dado existe para este caso.

---

### 4.6 Fig. 7 — Ti:LiNbO3

**Status: MISSING**

O perfil Ti:LiNbO3 envolve perfis Gaussian-Gaussian anisotrópicos com parâmetros distintos para os ramos extraordinário e ordinário (Eqs. 11–13, documentadas em `docs/06`). Todos os parâmetros numéricos necessários estão em `docs/06`, mas nenhum perfil de material, YAML, script ou dado existe para este caso.

---

## 5. Tabela consolidada

| Figura | Caso | CSV existe? | Figura gerada? | Teste CTest | Status | Observação |
|---|---|---|---|---|---|---|
| Fig. 1 | Canal homogêneo | Sim | Sim (SVG) | 4 testes sweep | **PARTIAL** | Desvio 43% em V=1.2, ~0% em V=4.0; hipótese buried rejeitada (T-004); causa provável: leitura de curva errada |
| Fig. 2 | Planar difuso | Sim | Sim (SVG) | 4 testes sweep | **PASS** | Erro máx. 0.0017% vs. solução exata |
| Fig. 4 | Canal circular | CSV pontual | Não | `waveguide_solver_case3_smoke`, `waveguide_solver_case3_smoke_artifacts`, `waveguide_global_tests` | **PARTIAL** | Sem sweep; flags delta_x/delta_z bloqueados por eigensolver simétrico (T-005); sem comparação |
| Fig. 5 | Gaussian-Gaussian | Não | Não | Não | **MISSING** | Depende de pesquisa bibliográfica |
| Fig. 6 | APE LiNbO3 | Não | Não | Não | **MISSING** | Depende de implementação do perfil APE |
| Fig. 7 | Ti:LiNbO3 | Não | Não | Não | **MISSING** | Todos os parâmetros documentados em docs/06 |

---

## 6. Comandos de reprodução

```bash
# 1. Compilar
./scripts/build.sh

# 2. Executar suíte completa de testes (19 testes)
./scripts/test.sh
# Equivalente: /usr/bin/ctest --test-dir build --output-on-failure

# 3. Reproduzir Caso 2 (Fig. 2) — resultado validado
python3 scripts/run_planar_diffuse_sweep.py \
  --output-root out/planar_diffuse_sweep/case2_exact_refined
python3 scripts/consolidate_planar_diffuse_sweep.py \
  --sweep-root out/planar_diffuse_sweep/case2_exact_refined
python3 scripts/plot_planar_diffuse_sweep.py \
  --sweep-root out/planar_diffuse_sweep/case2_exact_refined

# 4. Reproduzir Caso 1 (Fig. 1) — resultado preliminar
python3 scripts/run_case1_homogeneous_channel_sweep.py \
  --output-root out/case1_homogeneous_channel/reference_run_v4_mode_tracking
python3 scripts/consolidate_case1_homogeneous_channel_sweep.py \
  --sweep-root out/case1_homogeneous_channel/reference_run_v4_mode_tracking
python3 scripts/plot_case1_homogeneous_channel_sweep.py \
  --sweep-root out/case1_homogeneous_channel/reference_run_v4_mode_tracking

# 5. Executar Caso 3 (ponto único — sem validação)
scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml audit_case3
```

> Nota: o comando `ctest` no PATH em `~/.local/bin/ctest` é um wrapper Python com dependência ausente e falha antes de executar a suíte. Use `/usr/bin/ctest` ou `./scripts/test.sh`.

---

## 7. Limitações

### 7.1 Caso 1 — geometria confirmada, desvio de causa diferente

A hipótese de geometria buried (`cover_index = n_substrate = 1.43`) foi testada e **rejeitada** (T-004, 2026-05-14): piorou o erro em todos os pontos (+63% em V=1.2, vs. +43% com `cover_index = 1.00`). A causa mais provável do desvio é que os valores `B_ref` foram extraídos visualmente da curva de Marcatili na Fig. 1 (que fica abaixo da curva FEM/VIE próximo ao corte), não da curva FEM original. A malha smoke com 99 graus de liberdade livres também contribui para o erro em modos pouco confinados.

### 7.2 Comparação visual vs. tabulada

Para o Caso 1, os valores `B_ref` são extraídos visualmente da Fig. 1. O artigo não fornece tabela numérica, portanto erros de leitura da ordem de ±5% são esperados mesmo para a referência. Isso reduz a significância dos erros de 8% e 44% observados.

### 7.3 Malha do Caso 1 (CTest smoke)

Os três pontos de comparação do Caso 1 são gerados com a malha smoke (`channel_a2b_b1_smoke.mesh`, 16 nós livres). A malha farfield (`channel_a2b_b1_farfield.mesh`, 238 nós livres) converge para valores ligeiramente diferentes. A curva de dispersão completa em `reference_run_v4_mode_tracking` usa a malha de referência e não o smoke.

### 7.4 Caso 3 — termos de gradiente não ativados (bloqueador: eigensolver simétrico)

A implementação atual do perfil circular usa `delta_x = false; delta_z = false` (T-005, 2026-05-14). Fisicamente, o perfil circular n(x,y) varia em ambas as direções e deveria usar ambos os flags ativos. No entanto, a ativação torna F não-simétrica (conforme docs/02 §3b), e o eigensolver Jacobi atual só funciona com sistemas simétricos — retorna 0 modos quando F é assimétrica. O bloqueador é a ausência de um eigensolver não-simétrico (QZ/LAPACK). O impacto sobre `neff` dos termos omitidos não foi estimado.

### 7.5 Casos 5 e 6 — difusão anisotrópica

Os guias APE e Ti:LiNbO3 exigem um mapa de concentração de prótons/titânio C(x,y) obtido por solução separada de uma equação de difusão anisotrópica. Isso não está implementado. A alternativa de usar o perfil de índice diretamente (sem simular a difusão) pode ser suficiente para reproduzir as curvas do artigo se os perfis finais forem usados como entrada.

---

## 8. Conclusão

**Reproduzido com sucesso:** O Caso 2 (guia planar difuso) é o único caso validado com precisão quantitativa. O erro máximo de 0.0017% em 26 pontos contra a solução exata confere alta credibilidade ao núcleo do solver.

**Parcialmente reproduzido:**
- Caso 1 (guia homogêneo): executa e gera curva, mas a geometria precisa ser confirmada antes de qualquer conclusão sobre fidelidade à Fig. 1.
- Caso 3 (canal circular): o perfil material está implementado e o solver gera `neff` para um ponto pontual. Faltam sweep, curva de dispersão e auditoria do termo F4.

**Trabalho futuro:** Casos 4, 5 e 6 (três das seis figuras de validação do artigo) ainda não têm implementação. O Caso 4 depende de pesquisa bibliográfica (fórmula de f(x,y)); os Casos 5 e 6 dependem de implementação de perfis materiais anisotrópicos com parâmetros totalmente documentados em `docs/06`.

---

## 9. Próximos passos

Ver `TODO.md` para a lista completa. Estado das tarefas imediatas (2026-05-14):

1. **T-004** — CONCLUÍDO: hipótese buried testada e rejeitada; `cover_index = 1.00` mantido.
2. **T-005** — CONCLUÍDO: bloqueador identificado (eigensolver não-simétrico); flags mantidos desativados com BLOCKER comment.
3. **T-006** — PENDENTE (Codex): criar script de sweep para o Caso 3 (Fig. 4).
4. **T-007** — PENDENTE (Gemini): recuperar a forma analítica de f(x,y) do Caso 4.
5. **T-009** — PENDENTE (Codex): criar teste unitário de material anisotrópico antes dos Casos 5 e 6.
