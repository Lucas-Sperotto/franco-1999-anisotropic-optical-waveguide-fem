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
- `meta/`: resumo da execução, paths resolvidos, metadados do caso e informações da montagem global;
- `results/`: artefatos numéricos e arquivos produzidos pelo solver, incluindo auditoria local do primeiro elemento, matrizes globais, autovalores e `neff.csv`.

O executável atual gera uma execução demonstrável com leitura de caso, leitura de malha mínima, construção do elemento triangular P1, interpolação local dos coeficientes `nx2`, `nz2` e `gz2`, decomposição local dos termos `M`, `F1`, `F2`, `F3`, `F4` e `F` por quadratura no triângulo de referência, montagem global mínima do caso homogêneo isotrópico, eliminação de Dirichlet em nós de fronteira e solução densa do autoproblema generalizado reduzido.
