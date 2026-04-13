# Convenção Inicial de Saídas

Toda execução deve salvar artefatos dentro de `out/`, separados por caso e por execução.

Estrutura inicial:

```text
out/
└── <case_name>/
    └── <run_label>/
        ├── inputs/
        ├── logs/
        ├── meta/
        └── results/
```

Convenção adotada nesta fase:

- `inputs/`: snapshot do arquivo de entrada usado na execução;
- `logs/`: stdout/stderr e logs auxiliares de execução;
- `meta/`: resumo da execução, paths resolvidos, metadados e avisos de modo stub;
- `results/`: artefatos numéricos e arquivos produzidos pelo solver.

O executável mínimo atual gera uma execução demonstrável de infraestrutura com leitura de caso, leitura de malha mínima e avaliação geométrica local, sem ainda implementar a formulação global de elementos finitos do artigo.
