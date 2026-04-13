# Tests

Esta pasta documenta a estratégia atual de testes.

Nesta fase, o projeto já expõe sete testes simples via `ctest`:

- `waveguide_solver_help`: garante que o executável responde ao `--help`;
- `waveguide_solver_smoke`: garante leitura do caso YAML, resolução do path da malha, montagem global mínima e geração da estrutura básica de saída;
- `waveguide_solver_planar_smoke`: garante a execução completa do primeiro caso global com perfil planar difuso isotrópico;
- `waveguide_solver_smoke_artifacts`: garante que a execução smoke produziu os artefatos globais esperados em `out/`;
- `waveguide_solver_planar_smoke_artifacts`: garante que o caso planar difuso exportou os artefatos numéricos esperados;
- `waveguide_geometry_tests`: garante Jacobiano, área, orientação, gradientes P1, quadratura no triângulo de referência, redução correta para coeficientes constantes e a decomposição local `M`, `F1`, `F2`, `F3`, `F4`, `F` para casos constantes e nodalmente variáveis.
- `waveguide_global_tests`: garante montagem global constante e variável, consistência entre o caminho genérico e o caso homogêneo, não simetria esperada no caso planar difuso e resolução do autoproblema denso.

Esses testes agora cobrem a base geométrica, a camada de coeficientes materiais P1, a montagem local geral, a montagem global mínima e o primeiro caso global com perfil isotrópico planar difuso explicitamente alinhado com a documentação do artigo.
