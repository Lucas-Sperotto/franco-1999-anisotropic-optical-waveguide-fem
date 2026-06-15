# Relatorio de entrega - Casos 1 e 2

Data da execucao: 2026-06-02  
Repositorio: `franco-1999-anisotropic-optical-waveguide-fem`

Este arquivo resume as reproducoes numericas atualmente prontas para apresentar ao orientador:

- Caso 1: guia de canal retangular isotropico homogeneo, comparavel a Fig. 1.
- Caso 2: guia planar difuso isotropico, comparavel a Fig. 2.

As figuras consolidadas estao em `out/entrega_casos_1_2/figures/`. Os CSVs completos permanecem nas pastas originais dos sweeps para auditoria.

Observacao sobre a orientacao geometrica: no codigo e nos CSVs, a superficie fica em
`y = 0`; a cobertura/ar fica em `y < 0`; o substrato fica em `y >= 0`. Para
evitar a leitura visual invertida do modelo fisico, as figuras de perfil de
indice e campo modal usam o eixo vertical invertido, isto e, profundidade
crescendo para baixo.

## 1. Formulacao usada

O repositorio implementa a formulacao escalar para modos `E^x`, com tensor de permissividade diagonal:

$$
\bar{\varepsilon}_r =
\begin{bmatrix}
n_x^2(x,y) & 0 & 0 \\
0 & n_y^2(x,y) & 0 \\
0 & 0 & n_z^2(x,y)
\end{bmatrix}.
$$

A equacao escalar adotada para o campo transversal e:

$$
\frac{\partial^2}{\partial x^2}\left(n_x^2 E_x\right)
+ n_z^2 \frac{\partial^2 E_x}{\partial y^2}
+ n_z^2 \frac{\partial}{\partial x}\left(\frac{1}{n_z^2}\right)
\frac{\partial}{\partial x}\left(n_x^2 E_x\right)
- \beta^2 n_x^2 E_x
+ k_0^2 n_x^2 n_z^2 E_x = 0.
$$

Com elementos triangulares lineares P1:

$$
E_x(x,y) = \{N\}\{E_x\}^T,
$$

$$
n_k^2(x,y) = \{N\}\{n_k^2\}^T,\quad k=x,z,
$$

$$
g_z^2(x,y)=\frac{1}{n_z^2(x,y)}=\{N\}\{g_z^2\}^T.
$$

A discretizacao leva ao problema generalizado de autovalor:

$$
[F]\{E_x\}=n_{\mathrm{eff}}^2[M]\{E_x\},
\qquad
n_{\mathrm{eff}}=\frac{\beta}{k_0}.
$$

As matrizes locais seguem a decomposicao documentada no artigo:

$$
[F]=[F_1]-[F_2]-[F_3]+[F_4],
$$

com matriz de massa:

$$
[M] = 2Ak_0^2\int_{\zeta_1}\int_{\zeta_2}
n_z^2\{N\}^T\{N\}\,d\zeta_1\,d\zeta_2.
$$

Na implementacao, as integrais locais sao avaliadas por quadratura de Dunavant de grau 4. A montagem global aplica as condicoes de contorno de Dirichlet indicadas em cada YAML e resolve:

$$
\lambda=n_{\mathrm{eff}}^2,\qquad n_{\mathrm{eff}}=\sqrt{\lambda}.
$$

## 2. Caso 1 - Guia de canal isotropico homogeneo

### Configuracao fisica

O Caso 1 usa um nucleo retangular isotropico com:

| Parametro | Valor |
|---|---:|
| Indice da cobertura `n1` | 1.00 |
| Indice do substrato `n2` | 1.43 |
| Indice do nucleo `n3` | 1.50 |
| Largura do nucleo `a` | 2.0 |
| Altura do nucleo `b` | 1.0 |
| Centro em x | 0.0 |
| Superficie | `y = 0` |
| Condicao de contorno | Dirichlet zero na fronteira externa |

Pela convencao implementada, o nucleo ocupa `-1 <= x <= 1` e
`0 <= y <= 1`. Portanto, ele esta no lado do substrato da interface
`y = 0`, com a face superior na superficie. Fora do nucleo, a regiao
`y < 0` recebe o indice de cobertura e a regiao `y >= 0` recebe o indice
do substrato.

A malha de referencia usada na curva final foi:

| Quantidade | Valor |
|---|---:|
| Arquivo | `meshes/channel_a2b_b1_farfield.mesh` |
| Nos | 460 |
| Elementos triangulares | 836 |
| Graus de liberdade montados | 460 |
| Graus de liberdade livres | 378 |
| Modos solicitados por ponto | 16 |
| Eigensolver | `symmetric_jacobi` |

### Condicoes de contorno

No Caso 1 foi usada a condicao `dirichlet_zero_on_boundary_nodes`.
Isso significa:

$$
E_x = 0
$$

em todos os nos do contorno externo da malha truncada. Para a malha de
entrega, o dominio numerico vai de `x = -10` a `x = 10` e de `y = -6`
a `y = 14`; portanto, ha Dirichlet nos quatro lados externos do retangulo
computacional.

Nao ha trecho externo com Neumann imposto nesta rodada. As interfaces entre
cobertura, nucleo e substrato nao recebem condicao de contorno separada; elas
sao interfaces materiais internas tratadas pela montagem FEM.

![Caso 1 - condicoes de contorno](out/entrega_casos_1_2/figures/case1_boundary_conditions.png)

### Normalizacao da Fig. 1

O eixo horizontal e a frequencia normalizada:

$$
V =
\left(\frac{k_0 b}{\pi}\right)
\sqrt{n_3^2-n_2^2}.
$$

O eixo vertical e a constante de propagacao normalizada:

$$
B =
\frac{n_{\mathrm{eff}}^2-n_2^2}{n_3^2-n_2^2}.
$$

Foram rodados pontos em:

$$
V = 0.4, 0.6, 0.8,\ldots,4.0.
$$

O ponto `V=0.4` foi mantido no CSV, mas omitido do grafico final porque o modo selecionado nao foi classificado como guiado (`guided=no`). Assim, a curva FEM apresentada comeca em `V=0.6`.

### Curva de dispersao

![Caso 1 - curva de dispersao](out/entrega_casos_1_2/figures/case1_dispersion.png)

Arquivos associados:

- CSV FEM: `out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error/consolidated/reference_dispersion.csv`
- CSV FEM vs Marcatili: `out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error/consolidated/fem_vs_marcatili_ex11.csv`
- Figura PNG: `out/entrega_casos_1_2/figures/case1_dispersion.png`

### Erro relativo contra Marcatili

![Caso 1 - erro relativo](out/entrega_casos_1_2/figures/case1_error_vs_frequency.png)

Resumo numerico contra a referencia auxiliar de Marcatili `Ex11`:

| Metrica | Valor |
|---|---:|
| Pontos comparados | 17 |
| Menor erro relativo vs Marcatili exact | 0.015801% |
| Maior erro relativo vs Marcatili exact | 58.291976% |
| Erro medio vs Marcatili exact | 5.676804% |

O erro alto ocorre proximo ao corte, onde a aproximacao de Marcatili e a sensibilidade ao truncamento sao mais severas. A partir de `V=2.0`, a curva FEM fica praticamente sobreposta as curvas de Marcatili.

### Perfil de indice e campos modais

Perfil de indice usado no ponto de campo:

![Caso 1 - perfil de indice](out/entrega_casos_1_2/figures/case1_index_profile.png)

Campos `E^x` normalizados no ponto `V=2.0`, com `k0 = 13.873851`:

![Caso 1 - modo 1](out/entrega_casos_1_2/figures/case1_mode_1_field_v2p00.png)

![Caso 1 - modo 2](out/entrega_casos_1_2/figures/case1_mode_2_field_v2p00.png)

Observacao: o sinal do autovetor e arbitrario em problemas de autovalor. Por isso, as figuras mostram `E_x / max|E_x|`; a informacao fisica relevante e a forma espacial e os nos do campo.

## 3. Caso 2 - Guia planar difuso isotropico

### Configuracao fisica

O Caso 2 usa um guia planar com perfil unilateral exponencial:

Para a cobertura:

$$
n(y)=n_0=1.0,\qquad y<0.
$$

Para o substrato difundido:

$$
n(y)=n_s+\Delta n\exp\left(-\frac{y}{d}\right),
\qquad y\ge 0,
$$

Assim, o perfil guiado fica no lado do substrato a partir da interface
`y = 0`. Nas figuras, essa direcao aparece para baixo por escolha de
visualizacao.

com:

| Parametro | Valor |
|---|---:|
| Indice da cobertura `n0` | 1.00 |
| Indice base do substrato `ns` | 2.20 |
| Incremento `Delta n` | 0.01 |
| Profundidade de difusao `d` | 1.00 |
| Permissividade linearizada | sim |
| Condicao de contorno | Dirichlet zero nos extremos em `y` |
| Reducao `x`-invariante | ativa |

No substrato, a reproducao usa a forma linearizada:

$$
\varepsilon_r(y)
= n_s^2 + 2n_s\Delta n
\exp\left(-\frac{y}{d}\right),
\qquad y\ge 0.
$$

A malha de referencia usada na curva final foi:

| Quantidade | Valor |
|---|---:|
| Arquivo | `meshes/planar_d10_a2b_reference_x2y2.mesh` |
| Nos geometricos | 296 |
| Elementos triangulares | 438 |
| Graus de liberdade montados apos reducao planar | 74 |
| Graus de liberdade livres | 72 |
| Modos solicitados por ponto | 3 |
| Eigensolver | `general_qr` |

### Condicoes de contorno

No Caso 2 foi usada a condicao `dirichlet_zero_on_y_extrema`, com reducao
planar `x`-invariante. Assim:

$$
E_x = 0
$$

nos extremos superior e inferior do dominio numerico, isto e, em `y = -2`
e `y = 8` na malha de entrega. As laterais em `x` nao recebem Dirichlet;
como nao ha termo de contorno prescrito na forma fraca, elas ficam com
tratamento natural de fluxo normal zero. Com a reducao planar, essas laterais
servem apenas como suporte geometrico da malha 2D usada para representar o
problema efetivamente unidimensional em `y`.

A interface `y = 0` entre cobertura e substrato difundido tambem nao e uma
condicao de contorno; e uma interface material interna.

![Caso 2 - condicoes de contorno](out/entrega_casos_1_2/figures/case2_boundary_conditions.png)

### Parametro de varredura

O eixo horizontal da Fig. 2 e:

$$
k_0d.
$$

Como `d=1`, os pontos rodados foram:

$$
k_0d \in
\{2,3,4,5,6,8,10,15,20,30,40,50,70,90,110,150\}.
$$

Os pontos abaixo do corte esperado entram como diagnostico; a consolidacao marca esses modos com `cutoff_expected` quando apropriado.

### Curva de dispersao

![Caso 2 - curva de dispersao](out/entrega_casos_1_2/figures/case2_dispersion.png)

Arquivos associados:

- CSV FEM: `out/planar_diffuse_sweep/20260602-084655-fig2-k0b2-error/consolidated/reference_dispersion.csv`
- CSV solucao exata: `out/planar_diffuse_sweep/20260602-084655-fig2-k0b2-error/consolidated/analytic_reference.csv`
- CSV FEM vs exato: `out/planar_diffuse_sweep/20260602-084655-fig2-k0b2-error/consolidated/fem_vs_exact_comparison.csv`
- Figura PNG: `out/entrega_casos_1_2/figures/case2_dispersion.png`

### Erro relativo contra solucao exata

![Caso 2 - erro relativo](out/entrega_casos_1_2/figures/case2_error_vs_frequency.png)

Resumo do erro relativo absoluto:

| Modo | Pontos | Erro minimo (%) | Erro maximo (%) | Erro medio (%) |
|---|---:|---:|---:|---:|
| TE0 | 12 | 0.000273 | 0.011000 | 0.002012 |
| TE1 | 9 | 0.000409 | 0.000953 | 0.000797 |
| TE2 | 7 | 0.000045 | 0.000363 | 0.000240 |

O ponto de maior erro do TE0 ocorre no trecho de baixa frequencia incluido nesta rodada estendida. Na faixa historica de validacao principal (`k0d >= 10`), os erros permanecem da ordem de `10^-3 %` ou menores.

### Perfil de indice

![Caso 2 - perfil de indice](out/entrega_casos_1_2/figures/case2_index_profile_k0b40.png)

O perfil acima foi gerado no ponto `k0d=40`.

### Campos modais FEM reconstruidos

Os campos abaixo foram reconstruidos em pos-processamento a partir das
matrizes reduzidas FEM `global_F_reduced.csv` e `global_M_reduced.csv` do
ponto `k0d=40`. Como o caso planar esta com reducao `x`-invariante, os campos
dependem apenas de `y`; a extensao em `x` na figura apenas mostra essa
invariancia planar.

![Caso 2 - campo TE0](out/entrega_casos_1_2/figures/case2_te0_field_k0b40.png)

![Caso 2 - campo TE1](out/entrega_casos_1_2/figures/case2_te1_field_k0b40.png)

Arquivo nodal associado:

- CSV campos FEM reconstruidos: `out/entrega_casos_1_2/figures/case2_fem_modal_fields_k0b40.csv`

## 4. Comandos de reproducao

Build:

```bash
./scripts/build.sh
```

Caso 1, sweep estendido:

```bash
python3 scripts/run_case1_homogeneous_channel_sweep.py \
  --skip-build \
  --normalized-frequency-min 0.4 \
  --normalized-frequency-max 4.0 \
  --normalized-frequency-step 0.2 \
  --output-root out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error

python3 scripts/consolidate_case1_homogeneous_channel_sweep.py \
  --sweep-root out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error

python3 scripts/generate_case1_marcatili_reference.py \
  --sweep-root out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error \
  --output-root out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error_marcatili_reference \
  --normalized-frequency-min 0.4 \
  --normalized-frequency-max 4.0 \
  --point-count 181

python3 scripts/plot_case1_homogeneous_channel_sweep.py \
  --sweep-root out/case1_homogeneous_channel/20260602-084314-fig1-v04-marcatili-error \
  --hide-reference-points \
  --legend-y-offset 230 \
  --output-name fig1_like_reference_clean.svg
```

Caso 2, sweep estendido:

```bash
python3 scripts/run_planar_diffuse_sweep.py \
  --skip-build \
  --k0-b-values 2,3,4,5,6,8,10,15,20,30,40,50,70,90,110,150 \
  --output-root out/planar_diffuse_sweep/20260602-084655-fig2-k0b2-error

python3 scripts/consolidate_planar_diffuse_sweep.py \
  --sweep-root out/planar_diffuse_sweep/20260602-084655-fig2-k0b2-error

python3 scripts/plot_planar_diffuse_sweep.py \
  --sweep-root out/planar_diffuse_sweep/20260602-084655-fig2-k0b2-error \
  --legend-y-offset 250
```

Figuras de campo/perfil:

```bash
python3 scripts/plot_delivery_case12_fields.py \
  --case1-run out/entrega_casos_1_2/field_runs/case1_v2p00_checked \
  --case2-run out/entrega_casos_1_2/field_runs/case2_k0b40_checked \
  --output-dir out/entrega_casos_1_2/figures
```

## 5. Validacao automatizada

Foram executados testes dos pipelines afetados:

```bash
./scripts/test.sh -R case1_sweep_plot
./scripts/test.sh -R planar_sweep_plot
```

Ambos passaram no estado atual. A execucao mais ampla ja realizada para os pipelines de Caso 1 e Caso 2 foi:

```bash
./scripts/test.sh -R 'case1|planar_sweep'
```

Resultado: `10/10` testes passaram.

## 6. Limitacoes e proximos passos

1. O Caso 1 esta reprodutivel com curva FEM, curva de Marcatili exact e curva de Marcatili closed-form. A discrepancia em baixa frequencia e esperada na comparacao com Marcatili e tambem e sensivel ao corte/truncamento do dominio.
2. O Caso 2 esta validado numericamente contra solucao exata TE com erro muito pequeno na faixa principal. A extensao para `k0d < 5` foi mantida como diagnostico de corte.
3. Os campos modais do Caso 1 sao exportados diretamente em `modal_fields.csv` e plotados neste relatorio.
4. Os campos `TE0` e `TE1` do Caso 2 foram reconstruidos em pos-processamento a partir das matrizes FEM reduzidas. O proximo passo tecnico e fazer o caminho C++ `general_qr` persistir autovetores nodais diretamente, preferencialmente com LAPACK/QZ ou rotina equivalente.
