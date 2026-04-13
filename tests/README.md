# Tests

Esta pasta documenta a estratégia inicial de testes.

Nesta fase, o projeto já expõe dois testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha e geração da estrutura básica de saída.

Esses testes são de infraestrutura. Testes matemáticos e numéricos virão depois, quando a formulação começar a ser implementada.
