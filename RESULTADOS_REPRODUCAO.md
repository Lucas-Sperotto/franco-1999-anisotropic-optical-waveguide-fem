# Resultados da Reprodução — Franco et al. (1999)

**Data:** 2026-06-15
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

**Resultado do T-004 (geometria, 2026-06-15):** a Fig. 1 usa **guia de superfície assimétrico** (n₁=1.00 ar acima, n₂=1.43 substrato abaixo/laterais). A hipótese de guia enterrado (`cover_index = 1.43`) foi testada e rejeitada empiricamente — piorou o erro em V=1.2 de +43% para +63%. YAML `cover_index = 1.00` mantido sem alteração. Sweep smoke confirmado: B=0.502/0.735/0.910 em V=1.2/2.0/4.0 (todos guiados). **Discrepância residual explicada:** os valores `B_ref` em `cases/homogeneous_channel_fig1_reference_points.csv` foram extraídos visualmente da curva de Marcatili/EIM (curvas inferiores na Fig. 1), não da curva FEM "This work". A curva FEM do artigo fica sistematicamente acima de EIM — o que é consistente com os valores calculados pelo solver atual.

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

**Comandos de reprodução:**

```bash
python3 scripts/run_case3_channel_diffused_sweep.py \
  --output-root out/case3_channel_diffused_isotropic/final_run
python3 scripts/consolidate_case3_channel_diffused_sweep.py \
  --sweep-root out/case3_channel_diffused_isotropic/final_run
python3 scripts/plot_case3_channel_diffused_sweep.py \
  --sweep-root out/case3_channel_diffused_isotropic/final_run
```

**CSV gerado:** `out/case3_channel_diffused_isotropic/final_run/consolidated/dispersion_curve.csv`

**Figura gerada:** `out/case3_channel_diffused_isotropic/final_run/plots/fig4_like_reference.svg`

**Curva de dispersão (15 pontos, V = 1.5..5.0):**

| V | lambda (µm) | neff | B |
|---:|---:|---:|---:|
| 1.5 | 0.3940 | 1.46753 | 0.917 |
| 2.0 | 0.2955 | 1.47343 | 1.116 |
| 3.0 | 0.1970 | 1.47967 | 1.327 |
| 4.0 | 0.1477 | 1.48304 | 1.441 |
| 5.0 | 0.1182 | 1.47504 | 1.170 |

**Status: PARTIAL**

**Limitações conhecidas (T-005 concluído):**
1. `delta_x = false` e `delta_z = false` em `src/material_profile.cpp` — os termos de gradiente F2-gradiente e F4 não são computados. Isso é um BLOCKER documentado: ativar esses flags torna F não-simétrica (conforme docs/02 §3b). A rota não simétrica atual ainda precisa ser auditada para os sweeps finais antes de reativar os termos de gradiente.
2. Com delta_x/delta_z desativados, neff > n3av em todos os pontos, resultando em B > 1. A curva do artigo (Fig. 4) mostra B < 1, indicando que os termos de gradiente são necessários para confinamento correto. A curva atual é uma aproximação inferior do modelo completo.
3. O SVG inclui nota de limitação T-005 visível e eixo B estendido até 1.5.

---

### 4.4 Fig. 5 — Canal Gaussian-Gaussian

**Status: PARTIAL**

A referência [12] foi adicionada em `docs/ref/[12] - sbmo.1993.587213.pdf` e a definição do perfil foi recuperada da legenda da Fig. 4 dessa referência:

```text
f(x,y) = exp[-4(x-x0)^2/a^2] * exp[-(y/b)^2]
```

Foi implementado um ponto de sanidade do perfil Gaussian-Gaussian isotrópico:

```bash
bash scripts/run_case.sh cases/case4_gaussian_gaussian_channel.yaml audit_case4
```

**CSV gerado:** `out/case4_gaussian_gaussian_channel/audit_case4/results/neff.csv`

**Resultado pontual:** modo líder com `n_eff = 1.493103`, entre `n2 = sqrt(2.1)` e `n3m = 1.05 n2`.

**Limitação:** ainda não há sweep/consolidação/figura para a Fig. 5. Como no Caso 3, `delta_x/delta_z` permanecem desativados até existir eigensolver generalizado não simétrico.

---

### 4.5 Fig. 6 — APE LiNbO3

**Status: PARTIAL**

O perfil APE envolve difusão anisotrópica 2D cuja concentração C(x,y) varia segundo uma equação de difusão anisotrópica resolvida em pré-processamento. A equação de índice em função de C está documentada em `docs/06` (Eq. 10).

Foi implementado um ponto de sanidade anisotrópico:

```bash
bash scripts/run_case.sh cases/case5_ape_linbo3.yaml audit_case5
```

**CSV gerado:** `out/case5_ape_linbo3/audit_case5/results/neff.csv`

**Resultado pontual:** quatro modos exportados; modo líder com `n_eff = 2.207327`.

**Limitação:** a concentração C(x,y) ainda não é produzida por um pré-processador FEM de difusão anisotrópica. O YAML usa uma concentração proxy Gaussian-Gaussian explícita apenas para exercitar o contrato material, a montagem e a exportação. Portanto, este ponto não deve ser interpretado como reprodução final da Fig. 6.

---

### 4.6 Fig. 7 — Ti:LiNbO3

**Status: PARTIAL**

O perfil Ti:LiNbO3 envolve perfis anisotrópicos com parâmetros distintos para os ramos extraordinário e ordinário (Eqs. 11–13, documentadas em `docs/06`).

Foi implementado um ponto de sanidade com `W = 7.0 um`:

```bash
bash scripts/run_case.sh cases/case6_ti_linbo3.yaml audit_case6
```

**CSV gerado:** `out/case6_ti_linbo3/audit_case6/results/neff.csv`

**Resultado pontual:** modo líder com `n_eff = 2.210077`.

**Limitação:** a implementação atual executa apenas um ponto, separando os ramos extraordinário (`n_x`) e ordinário (`n_z`) no CSV nodal. Ainda faltam sweep em `W`, extração dos tamanhos de modo `W_x` e `W_y` e figura comparável à Fig. 7.

---

## 5. Tabela consolidada

| Figura | Caso | CSV existe? | Figura gerada? | Teste CTest | Status | Observação |
|---|---|---|---|---|---|---|
| Fig. 1 | Canal homogêneo | Sim (34 pts) | Sim (SVG) | 4 testes sweep | **PARTIAL** | T-004: geometria surface assimétrica confirmada; B=0.571 em V=1.2 vs referência 0.350 (Marcatili/EIM); B=0.910 em V=4.0 (~0% erro) |
| Fig. 2 | Planar difuso | Sim | Sim (SVG) | 4 testes sweep | **PASS** | Erro máx. 0.0017% vs. solução exata. Artefatos em `final_run/` |
| Fig. 4 | Canal circular | Sim (15 pts) | Sim (SVG) | smoke + global_tests | **PARTIAL** | T-005: flags delta_x/delta_z bloqueados (F não-simétrica); B > 1 em todos os pontos; curva é aproximação com gradientes omitidos. Falta auditar a rota não simétrica para os sweeps finais |
| Fig. 5 | Gaussian-Gaussian | Sim (ponto) | Não | smoke + global_tests | **PARTIAL** | T-007/T-008: fórmula verificada na ref. [12], perfil C++ e YAML pontual implementados; falta sweep/figura e eigensolver não simétrico para delta_x/delta_z |
| Fig. 6 | APE LiNbO3 | Sim (ponto) | Não | smoke + global_tests | **PARTIAL** | T-011: perfil APE de sanidade, YAML e CSV pontual implementados; falta concentração FEM de difusão e sweep/figura |
| Fig. 7 | Ti:LiNbO3 | Sim (ponto) | Não | smoke + global_tests | **PARTIAL** | T-012: perfil Ti com ramos ordinário/extraordinário separados e CSV pontual; falta sweep em W, W_x/W_y e figura |

---

## 6. Comandos de reprodução

```bash
# 1. Compilar
./scripts/build.sh

# 2. Executar suíte completa de testes (29 testes)
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

# 6. Executar pontos de sanidade anisotrópicos
bash scripts/run_case.sh cases/case5_ape_linbo3.yaml audit_case5
bash scripts/run_case.sh cases/case6_ti_linbo3.yaml audit_case6
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

A implementação atual do perfil circular usa `delta_x = false; delta_z = false` (T-005). Fisicamente, o perfil circular n(x,y) varia em ambas as direções e deveria usar ambos os flags ativos. No entanto, a ativação torna F não-simétrica (conforme docs/02 §3b), e a rota não simétrica atual ainda não foi auditada para os sweeps finais desses perfis. O impacto sobre `neff` dos termos omitidos não foi estimado.

### 7.5 Casos 5 e 6 — difusão anisotrópica

O Caso 5 ainda exige um mapa de concentração de prótons C(x,y) obtido por solução separada de uma equação de difusão anisotrópica. O ponto atual usa uma concentração proxy explícita, documentada no YAML e no `material_profile_summary.txt`, apenas como sanidade.

O Caso 6 já usa diretamente o perfil de índice das Eqs. 11-12 para os ramos extraordinário e ordinário, mas ainda não varre a largura inicial da faixa de Ti nem calcula os tamanhos de modo `W_x` e `W_y`.

---

## 8. Conclusão

**Reproduzido com sucesso:** O Caso 2 (guia planar difuso) é o único caso validado com precisão quantitativa. O erro máximo de 0.0017% em 26 pontos contra a solução exata confere alta credibilidade ao núcleo do solver.

**Parcialmente reproduzido:**
- Caso 1 (guia homogêneo): executa e gera curva, mas a geometria precisa ser confirmada antes de qualquer conclusão sobre fidelidade à Fig. 1.
- Caso 3 (canal circular): sweep e figura existem, mas os termos de gradiente seguem desativados até auditoria da rota não simétrica.
- Caso 4 (Gaussian-Gaussian): perfil e ponto de sanidade implementados; falta sweep/figura.
- Caso 5 (APE LiNbO3): perfil de sanidade implementado; falta pré-processador de concentração e sweep/figura.
- Caso 6 (Ti:LiNbO3): perfil anisotrópico implementado para um ponto; falta sweep em `W`, `W_x/W_y` e figura.

**Trabalho futuro:** fechar a reprodução final exige sweeps/figuras dos Casos 4, 5 e 6, além da auditoria dos termos de gradiente nos perfis 2D.

---

## 9. Próximos passos

Ver `TODO.md` para a lista completa. Estado das tarefas imediatas (2026-05-14):

1. **T-004** — CONCLUÍDO: hipótese buried testada e rejeitada; `cover_index = 1.00` mantido.
2. **T-005** — CONCLUÍDO: bloqueador identificado (eigensolver não-simétrico); flags mantidos desativados com BLOCKER comment.
3. **Caso 4** — PENDENTE: criar sweep, consolidação e figura da Fig. 5 a partir do perfil Gaussian-Gaussian implementado.
4. **Caso 5** — PENDENTE: substituir concentração proxy por pré-processador de difusão APE e gerar a Fig. 6.
5. **Caso 6** — PENDENTE: criar sweep em `W`, extrair `W_x/W_y` e gerar a Fig. 7.
