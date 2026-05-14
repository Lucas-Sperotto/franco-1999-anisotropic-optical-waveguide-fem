# Auditoria Final Gemini

**Data:** 2026-05-14
**Auditor:** Gemini Code Assist
**Objetivo:** Auditoria final de coerência do repositório antes do commit de fechamento da fase atual de reprodução.

## 1. Veredito

O projeto está **quase pronto para commit**.

A estrutura está exemplar, os testes passam, o `README.md` é claro e o relatório `RESULTADOS_REPRODUCAO.md` é um documento de altíssima qualidade, que diferencia de forma transparente o que foi validado, o que é parcial e o que está pendente.

O único problema **bloqueante** é uma inconsistência crítica entre a documentação de suporte (`docs/03_...`) e o relatório final (`RESULTADOS_REPRODUCAO.md`), que pode induzir a erro um futuro revisor. Após a correção deste ponto, o projeto pode ser considerado fechado nesta fase.

## 2. Problemas bloqueantes

1.  **Documentação do Caso 1 desatualizada:** O arquivo `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md` ainda exibe uma tabela de comparação com valores de `B_calc` negativos. Estes são artefatos de uma versão antiga do solver (pré-correção do Jacobi) e contradizem frontalmente os resultados atuais e corretos apresentados no `RESULTADOS_REPRODUCAO.md`. Um leitor que acesse apenas a pasta `docs/` concluirá, incorretamente, que o Caso 1 está quebrado.

## 3. Problemas não bloqueantes

1.  **`TODO.md` com tarefa concluída:** A tarefa `T-001 — Criar comando reprodutível de testes` está marcada como pendente `[ ]`, mas os arquivos `scripts/test.sh` e `README.md` já foram criados e atualizados, resolvendo o problema do `ctest`. A tarefa deve ser marcada como concluída `[x]`.
2.  **Pequeno erro de digitação no relatório:** Em `RESULTADOS_REPRODUCAO.md`, o caminho para o CSV do Caso 3 é citado como `out/case03_...`, mas o script `run_case.sh` gera a saída em `out/channel_diffused_isotropic_case/...`. É uma pequena inconsistência de nomenclatura.

## 4. Conferência dos arquivos citados

| Arquivo citado em `RESULTADOS_REPRODUCAO.md` | Existe? | Observação |
|---|---|---|
| `build/test_output/case1_sweep/consolidated/reference_comparison.csv` | Sim (inferido) | Gerado pelo pipeline de CTest/smoke do Caso 1. |
| `build/test_output/case1_sweep/plots/fig1_like_reference.svg` | Sim (inferido) | Gerado pelo pipeline de CTest/smoke do Caso 1. |
| `out/planar_diffuse_sweep/case2_exact_refined/consolidated/fem_vs_exact_comparison.csv` | Sim (inferido) | Gerado pelo pipeline de execução do Caso 2. |
| `out/planar_diffuse_sweep/case2_exact_refined/plots/fig2_like_reference.svg` | Sim (inferido) | Gerado pelo pipeline de execução do Caso 2. |
| `out/case03_channel_diffused_isotropic/results/neff.csv` | Sim (inferido) | O caminho real é `out/channel_diffused_isotropic_case/...`. Corrigido. |

## 5. Conferência dos casos

| Figura | Status no relatório | Evidência encontrada | Coerente? |
|---|---|---|---|
| Fig. 1 | **PARTIAL / WARN** | Tabela com desvio de +43.5% em V=1.2 e discussão explícita da hipótese da geometria assimétrica. | Sim |
| Fig. 2 | **PASS** | Tabela com erro máximo de 0.0017% vs. solução exata em 26 pontos. | Sim |
| Fig. 4 | **PARTIAL** | Resultado de ponto único, menção à ausência de sweep e à limitação do termo F4. | Sim |
| Fig. 5 | **MISSING** | Explicação sobre a dependência da pesquisa bibliográfica pela fórmula de `f(x,y)`. | Sim |
| Fig. 6 | **MISSING** | Explicação sobre a necessidade de implementar o perfil APE. | Sim |
| Fig. 7 | **MISSING** | Explicação sobre a necessidade de implementar o perfil Ti:LiNbO3. | Sim |

## 6. Mensagem de commit sugerida

```
feat: Add final reproduction report and align documentation

This commit introduces the final reproduction report, `RESULTADOS_REPRODUCAO.md`, which consolidates the status of all validation cases from the Franco et al. (1999) paper.

- Adds `RESULTADOS_REPRODUCAO.md` with detailed analysis for each case, clearly distinguishing between validated (Case 2), partially validated (Cases 1, 3), and missing cases (4, 5, 6).
- Updates `docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md` to replace the obsolete comparison table (with pre-correction negative results) with the current, correct data from the final report, resolving a major documentation inconsistency.
- Marks `T-001` in `TODO.md` as complete, as the `scripts/test.sh` wrapper for CTest is already implemented.
- Fixes a minor path inconsistency in the `RESULTADOS_REPRODUCAO.md` for the Case 3 output file.
```

---

A seguir, apresento os diffs para corrigir os problemas identificados.

```diff
--- a/docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md
++++ b/docs/03_guia_de_onda_de_canal_isotropico_homogeneo.md
@@ -78,40 +78,30 @@
 - ../out/case1_homogeneous_channel/reference_run_v2/plots/fig1_like_reference.svg
 - ../out/case1_homogeneous_channel/reference_run_v3/plots/fig1_like_reference.svg
 
-## Comparação preliminar com pontos aproximados da Fig. 1
+## Comparação com pontos aproximados da Fig. 1
 
-Os valores abaixo são os pontos visuais aproximados da figura fornecidos para auditoria preliminar. A comparação consolidada está em:
+A tabela abaixo reflete o estado atual da reprodução, conforme documentado em `RESULTADOS_REPRODUCAO.md`. Os valores de `B_ref` são extraídos visualmente da Fig. 1 do artigo.
 
- - ../out/case1_homogeneous_channel/reference_run_v2/consolidated/reference_comparison.csv
- - ../out/case1_homogeneous_channel/reference_run_v3/consolidated/reference_comparison.csv
+| V (freq. norm.) | B_ref (visual) | B_calc | Erro relativo (%) |
+|---:|---:|---:|---:|
+| 1.2 | 0.350 | 0.502 | +43.5% |
+| 2.0 | 0.675 | 0.735 | −8.9% |
+| 4.0 | 0.910 | 0.910 | +0.05% |
 
-Nesta tabela, o erro relativo percentual assinado foi calculado por:
+**Observação crítica:** A configuração atual usa `cover_index = 1.0` (cobertura de ar), criando um guia assimétrico de superfície. O artigo provavelmente usa um guia enterrado (*buried*) com n_cover = n_substrate = 1.43. Isso explica o desvio sistemático para baixas frequências normalizadas (modo menos confinado, mais afetado pela geometria), enquanto em alta frequência (V=4.0) o erro é desprezível (modo bem confinado, insensível à fronteira superior). A resolução desta hipótese é a tarefa T-004 do `TODO.md`.
 
-$$
- \frac{B_{\mathrm{ref\_aprox}} - B_{\mathrm{calc}}}{B_{\mathrm{ref\_aprox}}}\times 100.
-$$
-
-| frequência normalizada | $B_{\mathrm{ref\_aprox}}$ | $B_{\mathrm{calc}}$ | erro relativo (\%) |
-|---:|---:|---:|---:|
-| 0.8 | 0.050000 | -0.201638 | 503.276000 |
-| 1.0 | 0.200000 | -0.129040 | 164.520000 |
-| 1.2 | 0.350000 | -0.089614 | 125.604000 |
-| 1.4 | 0.475000 | -0.065834 | 113.859789 |
-| 1.6 | 0.500000 | -0.050415 | 110.083000 |
-| 1.8 | 0.625000 | -0.039827 | 106.372320 |
-| 2.0 | 0.675000 | -0.032255 | 104.778519 |
-| 2.2 | 0.725000 | -0.026658 | 103.676966 |
-| 2.4 | 0.760000 | 0.102629 | 86.496184 |
-| 2.6 | 0.800000 | 0.224147 | 71.981625 |
-| 2.8 | 0.825000 | 0.322097 | 60.957939 |
-| 3.0 | 0.840000 | 0.402201 | 52.118929 |
-| 3.2 | 0.860000 | 0.468571 | 45.515000 |
-| 3.4 | 0.875000 | 0.531962 | 39.204343 |
-| 3.6 | 0.890000 | 0.578884 | 34.956854 |
-| 3.8 | 0.900000 | 0.618984 | 31.224000 |
-| 4.0 | 0.910000 | 0.653531 | 28.183407 |
 
 ## Conclusão desta rodada do Caso 1
 
- - A trilha de reprodução do Caso 1 está completa e auditável no repositório.
- - A tendência global da curva FEM é monotônica com a frequência normalizada.
- - A concordância com os pontos visuais aproximados da figura ainda está ruim, especialmente na região de baixa frequência.
- - O resultado deve ser tratado como preliminar até fechar melhor a interpretação de normalização da figura original e a convergência numérica perto do corte.
+- A trilha de reprodução do Caso 1 está completa e auditável.
+- A curva de dispersão gerada é qualitativamente correta, mas apresenta um desvio quantitativo significativo em baixas frequências.
+- A hipótese principal para o desvio é a configuração de geometria assimétrica (guia de superfície) usada no `case.yaml`, em contraste com a provável geometria simétrica (guia enterrado) da referência.
+- O caso é considerado **parcialmente validado** e aguarda a resolução da pendência de geometria (T-004).
 
 Este caso corresponde ao **Caso 1** resumido em 09_resumo_dos_casos_de_teste.md e prepara a transição para o primeiro exemplo com índice espacialmente variável em 04_guia_de_onda_planar_difuso_isotropico.md.
 
---

**Navegação:** Anterior | Índice | Próximo
```

```diff
--- a/TODO.md
++++ b/TODO.md
@@ -13,7 +13,7 @@
 
 ### Fase A - Correções de build e testes
 
- - [ ] T-001 — Criar comando reprodutível de testes
+- [x] T-001 — Criar comando reprodutível de testes
   - Responsável: Codex
   - Arquivos: `scripts/test.sh`, `README.md`, `tests/README.md`
   - Critério de aceite: `./scripts/test.sh` executa `/usr/bin/ctest --test-dir build --output-on-failure` e evita o wrapper Python quebrado em `/home/sperotto/.local/bin/ctest`.
```

```diff
--- a/RESULTADOS_REPRODUCAO.md
++++ b/RESULTADOS_REPRODUCAO.md
@@ -128,7 +128,7 @@
   scripts/run_case.sh cases/channel_diffused_isotropic_case.yaml audit_case3
 ```
 
-**CSV gerado (ponto único):** `out/case03_channel_diffused_isotropic/results/neff.csv`
+**CSV gerado (ponto único):** `out/channel_diffused_isotropic_case/audit_case3/results/neff.csv`
 
 **Resultado do ponto único:**
 
```

