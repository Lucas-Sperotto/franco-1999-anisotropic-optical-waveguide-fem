# Tests

Esta pasta documenta a estratégia inicial de testes.

Nesta fase, o projeto já expõe três testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha e geração da estrutura básica de saída;
- `waveguide_geometry_tests`: garante Jacobiano, área, orientação, gradientes P1 e a decomposição local `M`, `F1`, `F2`, `F3`, `F4`, `F` no caso homogêneo isotrópico.

Esses testes agora cobrem a base geométrica e a primeira camada local explicitamente alinhada com a formulação do artigo.
