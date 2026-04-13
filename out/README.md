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
- `results/`: artefatos numéricos e arquivos produzidos pelo solver, incluindo auditoria local do primeiro elemento, parâmetros do perfil material, campos nodais de coeficientes, matrizes globais resumidas, autovalores, `neff.csv` e pontos para curva de dispersão.

O executável atual gera execuções demonstráveis para o caso homogêneo isotrópico constante e para o primeiro caso global com perfil planar difuso isotrópico. Em ambos, o fluxo cobre leitura de caso, leitura de malha, interpolação local dos coeficientes `nx2`, `nz2` e `gz2`, decomposição local dos termos `M`, `F1`, `F2`, `F3`, `F4` e `F`, montagem global densa, eliminação de Dirichlet em nós de fronteira e solução do autoproblema generalizado reduzido.
