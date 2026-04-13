# Casos

Esta pasta guarda os arquivos de entrada dos casos do projeto.

Convenção inicial:

- um arquivo YAML por caso;
- `schema_version` explícito no topo do arquivo;
- chaves mínimas: `case`, `mesh`, `material`, `boundary`, `solver` e `output`;
- caminhos de malha podem ser relativos ao próprio arquivo YAML;
- os nomes dos arquivos devem ser estáveis e legíveis.

O arquivo [smoke_case.yaml](smoke_case.yaml) é um caso de fumaça de infraestrutura. Nesta etapa ele já demonstra leitura de entrada, montagem global mínima do caso homogêneo isotrópico constante, aplicação explícita de Dirichlet na fronteira e geração dos artefatos principais do autoproblema reduzido.
