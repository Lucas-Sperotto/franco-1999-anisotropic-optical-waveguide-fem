# Tests

Esta pasta documenta a estratégia atual de testes.

Nesta fase, o projeto já expõe dezessete testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha, montagem global mínima e geração da estrutura básica de saída;
- `waveguide_solver_planar_smoke`: garante a execução completa do caso planar difuso isotrópico com perfil unilateral em profundidade;
- `waveguide_solver_case1_smoke`: garante a execução completa do caso homogêneo de canal isotrópico em degrau;
- `waveguide_solver_smoke_artifacts`: garante que a execução smoke produziu os artefatos globais esperados em `out/`;
- `waveguide_solver_planar_smoke_artifacts`: garante que o caso planar difuso exportou os artefatos numéricos esperados, já com cobertura `n0 = 1`, redução `x`-invariante e perfil material alinhado ao benchmark do artigo [6-19];
- `waveguide_solver_case1_smoke_artifacts`: garante que o caso base do guia de canal isotrópico exportou os artefatos numéricos globais esperados;
- `waveguide_geometry_tests`: garante Jacobiano, área, orientação, gradientes P1, quadratura no triângulo de referência, redução correta para coeficientes constantes e a decomposição local `M`, `F1`, `F2`, `F3`, `F4`, `F` para casos constantes e nodalmente variáveis.
- `waveguide_global_tests`: garante montagem global constante e variável, consistência entre o caminho genérico e o caso homogêneo, não simetria esperada no caso planar difuso, simetria esperada no canal homogêneo em degrau e resolução do autoproblema denso, incluindo a redução `x`-invariante do caso planar da fonte.
- `waveguide_planar_sweep_smoke`: executa um sweep reduzido do Caso 2 com a malha planar de referência.
- `waveguide_planar_sweep_consolidate`: consolida os pontos do sweep em CSV rastreáveis, já com `b`, `k0`, `k0_b`, rótulos `TE0/TE1/TE2` e a referência analítica TE de [6-19].
- `waveguide_planar_sweep_plot`: gera os gráficos SVG do sweep consolidado com o mesmo par de grandezas da Fig. 2.
- `waveguide_planar_sweep_artifacts`: garante a presença dos arquivos consolidados e dos três modos mais baixos quando disponíveis, tanto por índice modal quanto por rótulo `TE0/TE1/TE2`, além da consistência da hipótese atual `b = 1` usada para o Caso 2, da comparação preliminar com pontos externos da Fig. 2, da geração da referência analítica e do cálculo do erro relativo percentual.
- `waveguide_case1_sweep_smoke`: executa um sweep reduzido do Caso 1 no guia de canal homogêneo.
- `waveguide_case1_sweep_consolidate`: consolida os pontos do sweep do Caso 1 nas grandezas normalizadas da Fig. 1.
- `waveguide_case1_sweep_plot`: gera o gráfico SVG preliminar do Caso 1 em frequência normalizada versus constante de propagação normalizada.
- `waveguide_case1_sweep_artifacts`: garante a presença dos arquivos consolidados do Caso 1, a monotonicidade básica da curva smoke e a geração do SVG final.

Esses testes agora cobrem a base geométrica, a camada de coeficientes materiais P1, a montagem local geral, a montagem global mínima, o primeiro caso global com perfil isotrópico planar difuso, o primeiro caso global de canal homogêneo em degrau e a automação reproduzível dos sweeps dos Casos 1 e 2.
