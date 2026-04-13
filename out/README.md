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
- `results/`: artefatos numéricos e arquivos produzidos pelo solver, incluindo auditoria local do primeiro elemento.

O executável mínimo atual gera uma execução demonstrável com leitura de caso, leitura de malha mínima, construção do elemento triangular P1 e montagem local básica homogênea isotrópica. A montagem global e o autoproblema ainda não foram implementados.
