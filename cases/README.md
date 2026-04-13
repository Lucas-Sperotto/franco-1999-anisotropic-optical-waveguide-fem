# Casos

Esta pasta guarda os arquivos de entrada dos casos do projeto.

Convenção inicial:

- um arquivo YAML por caso;
- `schema_version` explícito no topo do arquivo;
- chaves mínimas: `case`, `mesh`, `material`, `boundary`, `solver` e `output`;
- caminhos de malha podem ser relativos ao próprio arquivo YAML;
- os nomes dos arquivos devem ser estáveis e legíveis.

O arquivo [smoke_case.yaml](smoke_case.yaml) é um caso de fumaça de infraestrutura. Nesta etapa ele já demonstra leitura de entrada, montagem global mínima do caso homogêneo isotrópico constante, aplicação explícita de Dirichlet na fronteira e geração dos artefatos principais do autoproblema reduzido.

O arquivo [planar_diffuse_isotropic_case.yaml](planar_diffuse_isotropic_case.yaml) introduz o primeiro caso global com coeficientes variáveis. Ele usa um perfil isotrópico planar difuso dependente de `y`, gera campos nodais de material e exporta artefatos suficientes para comparar autovalores e `n_eff` ao longo de futuras curvas de dispersão.
