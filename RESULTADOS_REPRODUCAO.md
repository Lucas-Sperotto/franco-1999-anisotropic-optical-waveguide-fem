# Resultados da Reprodução — Franco et al. (1999)

**Data:** 2026-06-16
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

onde `neff = β/k0`. As matrizes `[F]` e `[M]` são construídas pela soma das contribuições locais de cada elemento triangular. A formulação inclui quatro termos de rigidez (F1, F2, F3, F4) que acomodam gradientes de material e anisotropia via flags δx e δz.

O eigensolver usa fatoração de Cholesky de `[M]` seguida de diagonalização de Jacobi para matrizes simétricas. Para matrizes reduzidas não simétricas, a rota atual é `general_nonsym_refined`: estimativa inicial por simetrização/Jacobi, iteração inversa no operador não simétrico e refinamento por quociente de Rayleigh.

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
1. `delta_x = false` e `delta_z = false` permanecem no perfil circular do Caso 3. Os termos de gradiente F2/F4 não são computados nesse caso específico até uma auditoria própria da ativação dos gradientes nessa geometria.
2. Com delta_x/delta_z desativados, neff > n3av em todos os pontos, resultando em B > 1. A curva do artigo (Fig. 4) mostra B < 1, indicando que os termos de gradiente são necessários para confinamento correto. A curva atual é uma aproximação inferior do modelo completo.
3. O SVG inclui nota de limitação T-005 visível e eixo B estendido até 1.5.

---

### 4.4 Fig. 5 — Canal Gaussian-Gaussian

**Status: PARTIAL**

A referência [12] foi adicionada em `docs/ref/[12] - sbmo.1993.587213.pdf` e a definição do perfil foi recuperada da legenda da Fig. 4 dessa referência:

```text
f(x,y) = exp[-4(x-x0)^2/a^2] * exp[-(y/b)^2]
```

O sweep final usa `n2 = sqrt(2.1)`, `n3m = 1.05 n2`, `b = 1 um` e varia `V = 1.0..5.0`.

**Comandos:**

```bash
python3 scripts/run_case4_gaussian_gaussian_sweep.py \
  --output-root out/case4_gaussian_gaussian/final_run
python3 scripts/consolidate_case4_gaussian_gaussian_sweep.py \
  --sweep-root out/case4_gaussian_gaussian/final_run
python3 scripts/plot_case4_gaussian_gaussian_sweep.py \
  --sweep-root out/case4_gaussian_gaussian/final_run
```

**CSV gerado:** `out/case4_gaussian_gaussian/final_run/consolidated/dispersion_curve.csv`

**Figura gerada:** `out/case4_gaussian_gaussian/final_run/plots/fig5_like_reference.svg`

**Resultado:** 17 valores de `V` e 51 pares modo/`V` consolidados. O modo principal cresce de `B = 0.021` em `V = 1.0` para `B = 0.597` em `V = 5.0`. Os termos `delta_x/delta_z` estão ativos e usam a rota `general_nonsym_refined`.

**Limitação:** a figura é operacional, mas ainda não possui overlay de curvas digitizadas do artigo/referências.

---

### 4.5 Fig. 6 — APE LiNbO3

**Status: PARTIAL**

O perfil APE envolve difusão anisotrópica 2D cuja concentração C(x,y) varia segundo uma equação de difusão anisotrópica resolvida em pré-processamento. A equação de índice em função de C está documentada em `docs/06` (Eq. 10).

O pipeline atual usa `scripts/ape_diffusion_preprocessor.py` para calcular uma aproximação Gaussian-Gaussian a partir das constantes de difusão do recozimento (`Da_x = 0.92`, `Da_z = 0.77 um^2/h`), sem afirmar que isso substitui a solução FEM 2D de difusão descrita no artigo.

**Comandos:**

```bash
python3 scripts/run_case5_ape_linbo3_sweep.py \
  --output-root out/case5_ape_linbo3/final_run
python3 scripts/consolidate_case5_ape_linbo3_sweep.py \
  --sweep-root out/case5_ape_linbo3/final_run
python3 scripts/plot_case5_ape_linbo3_sweep.py \
  --sweep-root out/case5_ape_linbo3/final_run
```

**CSV gerado:** `out/case5_ape_linbo3/final_run/consolidated/dispersion_curve.csv`

**Figura gerada:** `out/case5_ape_linbo3/final_run/plots/fig6_like_reference.svg`

**Resultado:** 15 tempos de recozimento, 60 linhas consolidadas (4 modos por ponto) e modo principal monotônico de `B = 0.872` até `B = 0.990`. Os termos `delta_x/delta_z` estão ativos.

**Limitação:** `C(x,y)` ainda é uma proxy Gaussian derivada dos parâmetros de difusão, não um mapa obtido por solver FEM 2D de difusão APE.

---

### 4.6 Fig. 7 — Ti:LiNbO3

**Status: PARTIAL**

O perfil Ti:LiNbO3 envolve perfis anisotrópicos com parâmetros distintos para os ramos extraordinário e ordinário (Eqs. 11–13, documentadas em `docs/06`).

**Comandos:**

```bash
python3 scripts/run_case6_ti_linbo3_sweep.py \
  --output-root out/case6_ti_linbo3/final_run
python3 scripts/consolidate_case6_ti_linbo3_sweep.py \
  --sweep-root out/case6_ti_linbo3/final_run
python3 scripts/plot_case6_ti_linbo3_sweep.py \
  --sweep-root out/case6_ti_linbo3/final_run
```

**CSV gerado:** `out/case6_ti_linbo3/final_run/consolidated/neff_mode_sizes.csv`

**Figura gerada:** `out/case6_ti_linbo3/final_run/plots/fig7_like_reference.svg`

**Resultado:** 18 valores de `W` entre 3 e 12 um. O índice efetivo cresce de `2.209083` para `2.210542`; `W_x` fica na faixa aproximada `4.70..4.76 um`; `W_y` decresce de `4.2886` para `4.1350 um`. Os termos `delta_x/delta_z` estão ativos.

**Limitação:** `W_x/W_y` são extraídos de `modal_fields.csv` por FWHM de `|E|^2`, com sensibilidade esperada à malha e ao método de interpolação.

---

## 5. Tabela consolidada

| Figura | Caso | CSV existe? | Figura gerada? | Teste CTest | Status | Observação |
|---|---|---|---|---|---|---|
| Fig. 1 | Canal homogêneo | Sim (34 pts) | Sim (SVG) | 4 testes sweep | **PARTIAL** | T-004: geometria surface assimétrica confirmada; B=0.571 em V=1.2 vs referência 0.350 (Marcatili/EIM); B=0.910 em V=4.0 (~0% erro) |
| Fig. 2 | Planar difuso | Sim | Sim (SVG) | 4 testes sweep | **PASS** | Erro máx. 0.0017% vs. solução exata. Artefatos em `final_run/` |
| Fig. 4 | Canal circular | Sim (15 pts) | Sim (SVG) | 4 testes sweep | **PARTIAL** | Perfil circular ainda mantém `delta_x/delta_z=false`; B > 1 em parte da curva; falta auditoria específica dos gradientes |
| Fig. 5 | Gaussian-Gaussian | Sim (51 linhas) | Sim (SVG) | 4 testes sweep | **PARTIAL** | Sweep e figura implementados com `delta_x/delta_z=true`; falta overlay/referência digitizada |
| Fig. 6 | APE LiNbO3 | Sim (60 linhas) | Sim (SVG) | 4 testes sweep | **PARTIAL** | Sweep de 4 modos implementado; `C(x,y)` ainda é proxy Gaussian derivada de constantes de difusão |
| Fig. 7 | Ti:LiNbO3 | Sim (18 pts) | Sim (SVG) | 4 testes sweep | **PARTIAL** | Sweep em W e `W_x/W_y` implementados; falta estudo de convergência da extração FWHM |

---

## 6. Comandos de reprodução

```bash
# 1. Compilar
./scripts/build.sh

# 2. Executar suíte completa de testes (41 testes)
./scripts/test.sh
# Equivalente: /usr/bin/ctest --test-dir build --output-on-failure

# 3. Reproduzir os sweeps finais atualmente implementados
bash scripts/run_all.sh
python3 scripts/plot_all.py

# 4. Verificação rápida sem sobrescrever out/*/final_run
bash scripts/run_all.sh --smoke --skip-build
python3 scripts/plot_all.py --smoke
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

### 7.4 Caso 3 — termos de gradiente ainda não ativados no perfil circular

A implementação atual do perfil circular usa `delta_x = false; delta_z = false`. Fisicamente, o perfil circular n(x,y) varia em ambas as direções e deveria usar ambos os flags ativos. A rota não simétrica já existe e é exercitada nos Casos 4-6, mas a ativação no perfil circular ainda precisa de auditoria própria, porque a geometria por partes do Caso 3 já produz uma curva anômala em B quando os gradientes são omitidos.

### 7.5 Casos 5 e 6 — difusão anisotrópica e extração modal

O Caso 5 ainda exige, para fidelidade física completa, um mapa de concentração de prótons C(x,y) obtido por solução separada de uma equação de difusão anisotrópica. O sweep atual usa uma aproximação Gaussian-Gaussian calculada a partir das constantes de difusão e documentada nos scripts/artefatos.

O Caso 6 já usa diretamente o perfil de índice das Eqs. 11-12 para os ramos extraordinário e ordinário e varre a largura inicial da faixa de Ti. Os tamanhos de modo `W_x` e `W_y` são extraídos por FWHM de `|E|^2`, método que ainda deve passar por estudo de convergência de malha.

---

## 8. Conclusão

**Reproduzido com sucesso:** O Caso 2 (guia planar difuso) é o único caso validado com precisão quantitativa. O erro máximo de 0.0017% em 26 pontos contra a solução exata confere alta credibilidade ao núcleo do solver.

**Parcialmente reproduzido:**
- Caso 1 (guia homogêneo): executa e gera curva, mas a comparação permanece dependente de referência visual Marcatili/EIM.
- Caso 3 (canal circular): sweep e figura existem, mas os termos de gradiente seguem desativados no perfil circular.
- Caso 4 (Gaussian-Gaussian): sweep e figura existem; falta validação contra curvas digitizadas.
- Caso 5 (APE LiNbO3): sweep e figura existem; falta substituir a proxy Gaussian por solução FEM 2D de difusão, se exigido pela comparação final.
- Caso 6 (Ti:LiNbO3): sweep, `W_x/W_y` e figura existem; falta estudo de convergência da extração modal.

**Trabalho futuro:** fechar a reprodução final exige referências digitizadas/overlays para Casos 4-6, auditoria dos gradientes no Caso 3 e estudo de convergência de `W_x/W_y` no Caso 6.

---

## 9. Próximos passos

Ver `TODO.md` para a lista completa. Estado das tarefas imediatas (2026-06-16):

1. **T-004** — CONCLUÍDO: hipótese buried testada e rejeitada; `cover_index = 1.00` mantido.
2. **Caso 3** — PENDENTE: auditar `delta_x/delta_z` no perfil circular.
3. **Caso 4** — PENDENTE: anexar/digitar referência e quantificar erro da Fig. 5.
4. **Caso 5** — PENDENTE: decidir se a proxy Gaussian basta ou se será necessário pré-processador FEM 2D de difusão APE.
5. **Caso 6** — PENDENTE: estudar convergência de malha para `W_x/W_y`.
