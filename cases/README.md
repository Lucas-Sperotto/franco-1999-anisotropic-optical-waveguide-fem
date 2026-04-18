# Casos

Esta pasta guarda os arquivos de entrada dos casos do projeto.

Convenção inicial:

- um arquivo YAML por caso;
- `schema_version` explícito no topo do arquivo;
- chaves mínimas: `case`, `mesh`, `material`, `boundary`, `solver` e `output`;
- caminhos de malha podem ser relativos ao próprio arquivo YAML;
- os nomes dos arquivos devem ser estáveis e legíveis.

O arquivo [smoke_case.yaml](smoke_case.yaml) é um caso de fumaça de infraestrutura. Nesta etapa ele já demonstra leitura de entrada, montagem global mínima do caso homogêneo isotrópico constante, aplicação explícita de Dirichlet na fronteira e geração dos artefatos principais do autoproblema reduzido.

O arquivo [planar_diffuse_isotropic_case.yaml](planar_diffuse_isotropic_case.yaml) introduz o primeiro caso global com coeficientes variáveis. Na configuração atual do repositório, ele segue a leitura do caso fonte como um perfil planar unilateral em profundidade, com

`n(y) = 1.0` para `y < 0` e uma permissividade linearizada

`epsilon_r(y) = n_s^2 + 2 n_s \Delta n exp(-y/d)` para `y >= 0`,

com `n_s = 2.20`, `\Delta n = 0.01` e `d = 1`, em linha com o benchmark TE exato do artigo [6-19]. O caso também ativa uma redução global `x`-invariante para eliminar modos laterais numéricos em um problema que, fisicamente, é planar.

O sweep completo do Caso 2 é automatizado por `scripts/run_planar_diffuse_sweep.py`. Nesta etapa, o repositório assume `d = 1` no arquivo-base do caso e varia `k0` via `solver.wavelength_um`, exportando os resultados consolidados no mesmo par de grandezas usado na figura de referência: `k0 d` no eixo horizontal e `n_eff` no eixo vertical. O domínio numérico é `10 x 10`, e a direção `x` é usada como buffer numérico para o caso planar, não como largura física do guia.

Nesta etapa, a consolidação do Caso 2 usa apenas a referência analítica TE baseada na equação característica do artigo [6-19], evitando dependência de pontos visuais aproximados da figura.

O arquivo [homogeneous_channel_isotropic_case.yaml](homogeneous_channel_isotropic_case.yaml) abre a reprodução do **Caso 1** como um guia de canal isotrópico homogêneo em degrau, com hipótese geométrica inicial `a = 2b`, `b = 1`, `a = 2`, índices `n1 = 1.0`, `n2 = 1.43` e `n3 = 1.50`, e núcleo retangular alinhado às interfaces `x = ±1`, `y = 0` e `y = 1`. Nesta etapa, ele serve como caso-base para um sweep na frequência normalizada

`V = (k0 b / pi) * sqrt(n3^2 - n2^2)`

e para a extração da constante de propagação normalizada

`B = (n_eff^2 - n2^2) / (n3^2 - n2^2)`.

O sweep preliminar do Caso 1 é automatizado por `scripts/run_case1_homogeneous_channel_sweep.py`, com consolidação em `scripts/consolidate_case1_homogeneous_channel_sweep.py` e gráfico SVG em `scripts/plot_case1_homogeneous_channel_sweep.py`. Os pontos aproximados da Fig. 1 usados para comparação visual preliminar estão em [homogeneous_channel_fig1_reference_points.csv](homogeneous_channel_fig1_reference_points.csv).
