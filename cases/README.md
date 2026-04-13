# Casos

Esta pasta guarda os arquivos de entrada dos casos do projeto.

Convenção inicial:

- um arquivo YAML por caso;
- `schema_version` explícito no topo do arquivo;
- chaves mínimas: `case`, `mesh`, `solver` e `output`;
- caminhos de malha podem ser relativos ao próprio arquivo YAML;
- os nomes dos arquivos devem ser estáveis e legíveis.

O arquivo [smoke_case.yaml](smoke_case.yaml) é um caso de fumaça de infraestrutura. Ele existe para demonstrar build, leitura de entrada e geração de saídas, sem ainda implementar a formulação numérica do artigo.
