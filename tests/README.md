# Tests

Esta pasta documenta a estratégia inicial de testes.

Nesta fase, o projeto já expõe três testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha e geração da estrutura básica de saída;
- `waveguide_geometry_tests`: garante Jacobiano, área, orientação, gradientes P1 e matrizes locais básicas para um triângulo simples.

Esses testes agora cobrem a base geométrica e a camada elementar local mínima necessária para a futura montagem global.
