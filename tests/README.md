# Tests

Esta pasta documenta a estratégia atual de testes.

Nesta fase, o projeto já expõe cinco testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha, montagem global mínima e geração da estrutura básica de saída;
- `waveguide_solver_smoke_artifacts`: garante que a execução smoke produziu os artefatos globais esperados em `out/`;
- `waveguide_geometry_tests`: garante Jacobiano, área, orientação, gradientes P1, quadratura no triângulo de referência, redução correta para coeficientes constantes e a decomposição local `M`, `F1`, `F2`, `F3`, `F4`, `F` para casos constantes e nodalmente variáveis.
- `waveguide_global_tests`: garante montagem global, simetria de `M` e `F` no caso homogêneo isotrópico, eliminação de Dirichlet e resolução do autoproblema em uma malha mínima com nó interno.

Esses testes agora cobrem a base geométrica, a camada de coeficientes materiais P1, a montagem local geral e a primeira montagem global mínima explicitamente alinhada com a formulação do artigo.
