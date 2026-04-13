# Tests

Esta pasta documenta a estratégia atual de testes.

Nesta fase, o projeto já expõe onze testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha, montagem global mínima e geração da estrutura básica de saída;
- `waveguide_solver_planar_smoke`: garante a execução completa do primeiro caso global com perfil planar difuso isotrópico;
- `waveguide_solver_smoke_artifacts`: garante que a execução smoke produziu os artefatos globais esperados em `out/`;
- `waveguide_solver_planar_smoke_artifacts`: garante que o caso planar difuso exportou os artefatos numéricos esperados;
- `waveguide_geometry_tests`: garante Jacobiano, área, orientação, gradientes P1, quadratura no triângulo de referência, redução correta para coeficientes constantes e a decomposição local `M`, `F1`, `F2`, `F3`, `F4`, `F` para casos constantes e nodalmente variáveis.
- `waveguide_global_tests`: garante montagem global constante e variável, consistência entre o caminho genérico e o caso homogêneo, não simetria esperada no caso planar difuso e resolução do autoproblema denso.
- `waveguide_planar_sweep_smoke`: executa um sweep reduzido do Caso 2 com quatro estudos geométricos.
- `waveguide_planar_sweep_consolidate`: consolida os pontos do sweep em CSV rastreáveis, já com `b`, `k0`, `k0_b` e rótulos `TE0/TE1/TE2`.
- `waveguide_planar_sweep_plot`: gera os gráficos SVG do sweep consolidado com o mesmo par de grandezas da Fig. 2.
- `waveguide_planar_sweep_artifacts`: garante a presença dos arquivos consolidados e dos três modos mais baixos quando disponíveis, tanto por índice modal quanto por rótulo `TE0/TE1/TE2`.

Esses testes agora cobrem a base geométrica, a camada de coeficientes materiais P1, a montagem local geral, a montagem global mínima, o primeiro caso global com perfil isotrópico planar difuso e a automação reproduzível do sweep do Caso 2.
