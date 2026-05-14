# Patch Codex — Alinhamento Pre-Commit

## 1. Tarefa implementada

Alinhamento documental pre-commit apontado por `ai_logs/2026-05-14_gemini_auditoria_final_pre_commit.md`.

## 2. Arquivos modificados

- `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md`
- `RESULTADOS_REPRODUCAO.md`

## 3. Decisões técnicas

- A tabela antiga do Caso 1, com `B_calc` negativos de uma rodada obsoleta, foi substituida pelos tres pontos atuais ja usados no relatorio final.
- O Caso 1 continua marcado como parcialmente validado. A hipotese de guia de superficie versus guia enterrado permanece pendente em T-004.
- O caminho do CSV pontual do Caso 3 foi corrigido para o diretorio realmente gerado por `scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml audit_case3`.

## 4. Comandos executados

Executados apos o patch:

```bash
cmake -S . -B build
cmake --build build -j
./scripts/test.sh
```

## 5. Resultados

- `cmake -S . -B build`: passou.
- `cmake --build build -j`: passou.
- `./scripts/test.sh`: passou.

```text
100% tests passed, 0 tests failed out of 17
```

## 6. Pendencias

- T-004 permanece aberta: confirmar a geometria buried/surface do Caso 1 antes de qualquer ajuste numerico.
- Fig. 1 continua com status parcial.

## 7. Proxima tarefa recomendada

T-002 — adicionar CTest smoke dedicado ao Caso 3.
