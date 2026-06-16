# franco-1999-anisotropic-optical-waveguide-fem
Repositório em C++ para reproduzir o artigo “Finite Element Analysis of Anisotropic Optical Waveguide with Arbitrary Index Profile”, implementando a formulação escalar por elementos finitos para guias de onda ópticos anisotrópicos, com casos de validação, documentação teórica e foco em reprodutibilidade.

## Estado atual

| Figura | Caso | Estado |
| --- | --- | --- |
| Fig. 1 | Canal homogêneo isotrópico | Parcial: CSV/figura existem; discrepância residual documentada contra referência visual Marcatili/EIM |
| Fig. 2 | Planar difuso isotrópico | PASS: comparação analítica com erro máximo abaixo de 0.002% |
| Fig. 4 | Canal difuso circular isotrópico | Parcial: sweep/figura existem; `delta_x/delta_z` seguem desativados neste perfil até auditoria específica |
| Fig. 5 | Canal Gaussian-Gaussian isotrópico | Parcial: sweep, CSV e SVG existem; falta comparação quantitativa com referência digitizada |
| Fig. 6 | APE LiNbO3 | Parcial: sweep de 4 modos, CSV e SVG existem; concentração ainda é proxy Gaussian derivada das constantes de difusão |
| Fig. 7 | Ti:LiNbO3 | Parcial: sweep em `W`, `W_x/W_y`, CSV e SVG existem; tamanhos de modo ainda são extração FWHM sensível à malha |

## Build e testes

```bash
./scripts/build.sh
./scripts/test.sh
```

O script de testes chama `/usr/bin/ctest --test-dir build --output-on-failure` diretamente. Isso evita o wrapper `ctest` do ambiente local em `~/.local/bin`, que pode falhar antes de executar a suíte. A suíte atual expõe 41 testes CTest.

## Reprodução

Fluxo orquestrado dos casos implementados:

```bash
bash scripts/run_all.sh
python3 scripts/plot_all.py
```

Verificação rápida, sem sobrescrever as pastas finais:

```bash
bash scripts/run_all.sh --smoke
python3 scripts/plot_all.py --smoke
```

Execução pontual de um YAML:

```bash
bash scripts/run_case.sh cases/case4_gaussian_gaussian_channel.yaml audit_case4
bash scripts/run_case.sh cases/case5_ape_linbo3.yaml audit_case5
bash scripts/run_case.sh cases/case6_ti_linbo3.yaml audit_case6
```

## Artefatos principais

- `out/case1_homogeneous_channel/final_run/`
- `out/planar_diffuse_sweep/final_run/`
- `out/case3_channel_diffused_isotropic/final_run/`
- `out/case4_gaussian_gaussian/final_run/`
- `out/case5_ape_linbo3/final_run/`
- `out/case6_ti_linbo3/final_run/`

O manifesto `out/reproduction_artifacts.csv` é gerado por `scripts/plot_all.py`.
