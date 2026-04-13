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

Para o sweep do Caso 2, a pasta `out/planar_diffuse_sweep/<run_label>/` passa a conter:

- `generated_cases/`: arquivos YAML temporários gerados para cada ponto do sweep;
- `points/`: uma execução completa do solver por estudo geométrico e por valor de `b`;
- `study_manifest.csv` e `point_manifest.csv`: índices rastreáveis do sweep;
- `consolidated/`: CSVs consolidados com `b`, `k0`, `k0_b`, `n_eff`, identificação modal `TE0/TE1/TE2`, disponibilidade modal e sensibilidade numérica;
- `plots/`: gráficos SVG produzidos a partir da consolidação, incluindo a curva preliminar comparável à Fig. 2 em eixos `k0 b` versus `n_eff`.
