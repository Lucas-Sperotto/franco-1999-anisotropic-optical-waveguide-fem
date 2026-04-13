# Tests

Esta pasta documenta a estratégia inicial de testes.

Nesta fase, o projeto já expõe dois testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha e geração da estrutura básica de saída;
- `waveguide_geometry_tests`: garante área, orientação e gradientes P1 para um triângulo simples.

Esses testes ainda são de base, mas já cobrem a primeira camada geométrica necessária para a futura montagem elementar.
