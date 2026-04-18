# Resumo dos Exemplos e Casos de Teste do Artigo

Este arquivo sintetiza, em linguagem operacional, os seis casos de validação usados no artigo. O objetivo é concentrar em um único lugar o que cada caso testa, quais entradas precisam ser modeladas, quais saídas devem ser extraídas e por que a comparação com a literatura é importante.

Em vez de substituir as seções [03](03_guia_de_onda_de_canal_isotropico_homogeneo.md) a [06](06_guia_de_onda_de_canal_difuso_anisotropico.md), este resumo deve ser lido como um mapa de implementação e validação. Ele organiza o material para o momento em que o projeto passar da leitura técnica para a codificação em C++.

## Como usar este resumo

- Use este arquivo para decidir a ordem de implementação e a meta de validação de cada etapa.
- Use os arquivos [03](03_guia_de_onda_de_canal_isotropico_homogeneo.md) a [06](06_guia_de_onda_de_canal_difuso_anisotropico.md) para recuperar detalhes físicos, parâmetros e figuras.
- Use [02_formulacao_por_elementos_finitos.md](02_formulacao_por_elementos_finitos.md) sempre que surgir dúvida sobre a forma matricial, a notação ou o significado dos termos do problema de autovalor.
- Preserve a distinção entre constante de propagação $\beta$, índice efetivo $n_{\mathrm{eff}} = \beta/k_0$ e grandezas normalizadas definidas especificamente em cada figura.

## Mapa rápido dos seis casos

| Caso | Documento principal | Figuras | Tipo de meio | Objetivo principal |
| --- | --- | --- | --- | --- |
| 1 | [03](03_guia_de_onda_de_canal_isotropico_homogeneo.md) | Fig. 1 | Isotrópico homogêneo | Validar o núcleo do solver em um caso simples |
| 2 | [04](04_guia_de_onda_planar_difuso_isotropico.md) | Fig. 2 | Isotrópico planar difuso | Introduzir índice espacialmente variável |
| 3 | [05](05_guia_de_onda_de_canal_difuso_isotropico.md) | Figs. 3 e 4 | Isotrópico de canal com perfil circular | Testar perfil geométrico por partes e sensibilidade ao corte |
| 4 | [05](05_guia_de_onda_de_canal_difuso_isotropico.md) | Fig. 5 | Isotrópico de canal com perfil Gaussian-Gaussian | Comparar a formulação com vários métodos próximos ao corte |
| 5 | [06](06_guia_de_onda_de_canal_difuso_anisotropico.md) | Fig. 6 | Anisotrópico APE em $LiNbO_3$ | Introduzir anisotropia ligada ao processo APE |
| 6 | [06](06_guia_de_onda_de_canal_difuso_anisotropico.md) | Fig. 7 | Anisotrópico Ti:$LiNbO_3$ | Validar o caso materialmente mais rico do artigo |

## Caso 1: guia de onda de canal isotrópico homogêneo

Corresponde à seção [03](03_guia_de_onda_de_canal_isotropico_homogeneo.md) e à Fig. 1.

**Problema físico.** Guia retangular homogêneo com comparação do modo fundamental $E^x$ contra métodos numéricos clássicos.

**Entradas principais.**

- índices de refração $n_1 = 1.0$, $n_2 = 1.43$ e $n_3 = 1.50$;
- geometria retangular;
- varredura da frequência normalizada

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_3^2 - n_2^2\right)^{1/2};
$$

- cálculo da constante de propagação normalizada

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_3^2 - n_2^2}.
$$

**Domínio e contorno usados na reprodução atual.**

- domínio de referência para comparação com a Fig. 1: `x in [-10, 10]` e `y in [-6, 14]`;
- domínio de controle adicional (sensibilidade ao truncamento): `x in [-5, 5]` e `y in [-3, 7]`;
- condição de contorno usada no solver: `boundary.condition: dirichlet_zero_on_boundary_nodes`, isto é, Dirichlet homogênea em toda a fronteira externa da malha.

**Saídas esperadas.**

- curva de dispersão do modo fundamental $E^x$;
- comparação com VIE, EIM e método de Marcatili;
- comportamento coerente fora e perto da região de corte.

**Papel na validação.** Este é o teste de consistência inicial. Ele deve validar montagem matricial, extração modal e normalização de resultados antes de qualquer perfil difuso.

**Observação editorial.** As referências [7] e [19] usam variações de notação para índices e eixos. Na implementação atual do repositório, a convenção adotada no Caso 1 permanece $n_1 = 1.0$, $n_2 = 1.43$, $n_3 = 1.50$, com hipótese geométrica inicial `a = 2b` e `b = 1`.

## Caso 2: guia de onda planar difuso isotrópico

Corresponde à seção [04](04_guia_de_onda_planar_difuso_isotropico.md) e à Fig. 2.

**Problema físico.** Guia planar isotrópico com perfil exponencial de índice, usado para testar a formulação quando o meio deixa de ser homogêneo.

**Entradas principais.**

- geometria planar;
- profundidade de difusão $d$;
- cobertura homogênea para $y < 0$;
- perfil exponencial no substrato para $y \ge 0$;
- solução de referência analítica TE de [19];
- parâmetro de varredura no eixo horizontal dado por $k_0 d$.

$$
n(y) = n_s + \Delta n \exp\left(-\frac{y}{d}\right), \qquad y \ge 0.
$$

- cálculo dos três modos $E^x$ de menor ordem.

**Domínio e contorno usados na reprodução atual.**

- domínio numérico da malha planar de referência: `x in [-5, 5]` e `y in [-2, 8]` (total `10 x 10`);
- condição de contorno usada no solver: `boundary.condition: dirichlet_zero_on_y_extrema`, com Dirichlet homogênea nos níveis `y_min` e `y_max`;
- redução planar ativa: `solver.planar_x_invariant_reduction: true`, mantendo um único grau de liberdade por nível de profundidade e removendo dependência lateral artificial em `x` no benchmark planar.

**Saídas esperadas.**

- índices efetivos dos três modos de menor ordem;
- curvas de dispersão;
- comparação com solução exata de referência.

**Papel na validação.** Este é o primeiro caso em que a discretização precisa lidar com coeficientes materiais variáveis no domínio, mas ainda sem a complexidade geométrica completa dos guias de canal.

## Caso 3: guia de onda de canal difuso isotrópico com perfil circular

Corresponde à primeira metade da seção [05](05_guia_de_onda_de_canal_difuso_isotropico.md), à Fig. 3 e à Fig. 4.

**Problema físico.** Guia de canal com núcleo retangular e difusão circular descrita por uma lei geométrica por partes.

**Entradas principais.**

- largura $a$ e altura $b$ do núcleo retangular;
- índices $n_2 = 1.44$, $n_{3m} = 1.5$ e $n_1 = 1.0$;
- perfil

$$
n_3 = n_2 + \frac{n_2 - n_{3m}}{L^2}\left(x^2 + y^2 - L^2\right);
$$

- definição geométrica de $L$:

$$
L = \sqrt{b^2 + x^2}, \qquad \text{se } |y| \geq |x|,
$$

$$
L = \sqrt{\left(\frac{a}{2}\right)^2 + y^2}, \qquad \text{caso contrário;}
$$

- malha de referência com 5680 triângulos lineares de primeira ordem e 2800 nós.

**Saídas esperadas.**

- curva de dispersão do modo $E^x_{11}$;
- frequência normalizada

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_{3av}^2 - n_2^2\right)^{1/2};
$$

- constante de propagação normalizada

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_{3av}^2 - n_2^2},
$$

com $n_{3av} = 1.47$;

- comparação com VIE, VFEM e SFEM.

**Papel na validação.** Este caso combina geometria de canal, perfil por partes e refinamento de malha, sendo um bom teste de robustez antes dos casos anisotrópicos.

**Observação editorial.** As expressões do perfil permitem uma checagem útil antes da solução modal: no centro do guia deve-se recuperar o valor máximo $n_{3m}$ e, na fronteira do núcleo, o valor do substrato $n_2$.

## Caso 4: guia de onda de canal difuso isotrópico com perfil Gaussian-Gaussian

Corresponde à segunda metade da seção [05](05_guia_de_onda_de_canal_difuso_isotropico.md) e à Fig. 5.

**Problema físico.** Guia de canal isotrópico difuso com perfil Gaussian-Gaussian, analisado especialmente na vizinhança do corte.

**Entradas principais.**

- relação geométrica $a/b = 1$;
- perfil

$$
n_3 = n_2 \left(1 + 0.05\, f(x,y)\right);
$$

- parâmetros

$$
n_1 = 1.0, \qquad n_2 = (2.1)^{1/2}, \qquad n_{3m} = 1.05\,n_2;
$$

- frequência normalizada

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_{3m}^2 - n_2^2\right)^{1/2}.
$$

**Saídas esperadas.**

- curva de dispersão do modo $E^x_{11}$;
- constante de propagação normalizada

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_{3m}^2 - n_2^2};
$$

- comparação com VM, Vector FE, VFD, Extended VFD e Var. FD.

**Papel na validação.** Este é um dos melhores casos para testar qualidade numérica perto do corte e capacidade de comparação com múltiplas referências.

**Observação editorial.** A função $f(x,y)$ não foi explicitada analiticamente no texto consolidado do artigo nesta pasta. Para implementar esse caso com exatidão, será necessário recuperar essa definição diretamente da referência [12] ou do PDF original.

## Caso 5: guia de onda anisotrópico APE em $LiNbO_3$

Corresponde à subseção A de [06](06_guia_de_onda_de_canal_difuso_anisotropico.md) e à Fig. 6.

**Problema físico.** Guia APE em $LiNbO_3$, no qual a troca protônica com recozimento altera apenas o índice extraordinário.

**Entradas principais.**

- material $LiNbO_3$;
- índice inicial em degrau com $\Delta n_{\mathrm{PE}} = 0.12$;
- relação entre concentração de prótons e índice extraordinário:

$$
n_e(C) = n_{es} + \Delta n_e \left[1 - \exp(-11C)\right];
$$

- condições do processo: quinze minutos de PE a $190^\circ$C e quatro horas de recozimento a $360^\circ$C;
- parâmetros

$$
D_a(x\text{-cut}) = 0.92\ \mu\text{m}^2/\text{h}, \qquad D_a(z\text{-cut}) = 0.77\ \mu\text{m}^2/\text{h},
$$

$$
\lambda_0 = 0.6328\ \mu\text{m}.
$$

**Saídas esperadas.**

- curvas de dispersão para os quatro modos $E^x$ de menor ordem;
- comparação qualitativa com a literatura;
- comportamento coerente com o caso APE estudado anteriormente em [9].

**Papel na validação.** Este é o primeiro caso em que a anisotropia do meio passa a ser parte central do problema físico e não apenas da forma geral da formulação.

**Observação editorial.** O artigo informa explicitamente que a dispersão do índice de refração não foi considerada neste exemplo. Essa simplificação deve ser preservada ao reproduzir o caso.

## Caso 6: guia de onda anisotrópico Ti-difundido em $LiNbO_3$

Corresponde à subseção B de [06](06_guia_de_onda_de_canal_difuso_anisotropico.md) e à Fig. 7.

**Problema físico.** Guia Ti:$LiNbO_3$ com perfil espacial complexo, dependência de comprimento de onda e parâmetros distintos para os ramos extraordinário e ordinário.

**Entradas principais.**

- expressão do índice difundido:

$$
n_{e,o}^2(x,y,\lambda) = n_{b_{e,o}}^2 + \left[ \left(n_{b_{e,o}} + \Delta n_{s_{e,o}}\right)^2 - n_{b_{e,o}}^2 \right] \exp\left(-\frac{y^2}{d_y^2}\right) f\left(\frac{2x}{W}\right);
$$

- função auxiliar:

$$
f\left(\frac{2x}{W}\right) = \frac{1}{2} \left\{
\operatorname{erf} \left[ \frac{W}{2d_x} \left( 1 + \frac{2x}{W} \right) \right]
+ \operatorname{erf} \left[ \frac{W}{2d_x} \left( 1 - \frac{2x}{W} \right) \right] \right\};
$$

- modelo para $\Delta n_{s_{e,o}}(\lambda)$:

$$
\Delta n_{s_{e,o}}(\lambda) = \left[ B_0(\lambda) + B_1(\lambda)\frac{H}{d_{y_{e,o}}} \right] \left( \frac{H}{d_{y_{e,o}}} \right)^{\alpha_{e,o}};
$$

- parâmetros:

$$
H = 100\ \text{nm}, \qquad \lambda = 1.523\ \mu\text{m}, \qquad T = 1050^\circ\text{C}, \qquad t = 8.5\ \text{h};
$$

$$
d_{xe} = 4.60\ \mu\text{m}, \quad d_{ye} = 4.00\ \mu\text{m}, \quad d_{xo} = 6.23\ \mu\text{m}, \quad d_{yo} = 4.98\ \mu\text{m};
$$

$$
n_{be} = 2.2125, \quad n_{bo} = 2.1383, \quad \Delta n_{se} = 0.00446, \quad \Delta n_{so} = 0.01217.
$$

**Saídas esperadas.**

- índice efetivo do modo $E^x_{11}$;
- tamanhos de modo $W_x$ e $W_y$;
- curvas dessas grandezas em função da largura inicial da faixa de Ti.

**Papel na validação.** Este é o caso mais completo do artigo e o mais exigente em termos de modelagem material. Ele é um bom candidato para ser o último marco antes de considerar a reprodução do trabalho como numericamente madura.

**Observação editorial.** As curvas de referência citadas em [21] foram obtidas para cristal com corte em $c$, enquanto este caso foi simulado para cristal com corte em $x$. O artigo ainda assim reporta boa concordância qualitativa, e essa diferença de contexto deve ser mantida em mente ao comparar resultados.

## Consistência global entre os casos

- Todos os casos validam a mesma formulação modal, mas cada figura usa sua própria grandeza normalizada. Não convém assumir uma normalização única para o projeto inteiro sem olhar a figura correspondente.
- A relação fundamental entre autovalor e física propagante permanece a mesma em toda a pasta: $n_{\mathrm{eff}} = \beta/k_0$.
- A progressão dos casos é deliberada: homogêneo, depois difuso isotrópico, depois canal difuso mais rico, e por fim anisotropia em $LiNbO_3$.
- A vizinhança do corte é o ponto mais delicado das comparações numéricas e reaparece como advertência tanto nos casos isotrópicos quanto nas conclusões.
- A passagem para os casos anisotrópicos exige separar claramente a formulação FEM da modelagem específica de materiais e processos de difusão.

## Ordem recomendada de implementação em C++

1. Implementar a montagem básica do problema generalizado de autovalor e validar o Caso 1.
2. Introduzir avaliação espacial de índice e validar o Caso 2.
3. Implementar perfis de canal definidos geometricamente e validar o Caso 3.
4. Refinar o tratamento numérico perto do corte e validar o Caso 4.
5. Adicionar a modelagem APE em $LiNbO_3$ e validar o Caso 5.
6. Implementar a modelagem Ti:$LiNbO_3$ com parâmetros extraordinários e ordinários separados e validar o Caso 6.

## Saídas mínimas que o repositório futuro deve produzir

- autovalores e índices efetivos por caso;
- perfis modais relevantes;
- arquivos de parâmetros de entrada;
- gráficos comparáveis às figuras do artigo;
- registros de malha, solver e pós-processamento;
- estrutura de saída que permita rastrear claramente qual caso foi executado e com quais dados.

## Pontos que merecem conferência manual no momento da codificação

- o termo $[F_4]$ da formulação em [02](02_formulacao_por_elementos_finitos.md), por ser uma região sensível a ambiguidades tipográficas em documentos escaneados;
- a definição explícita de $f(x,y)$ no Caso 4, que não aparece completa no texto consolidado desta pasta;
- a parametrização geométrica associada à dimensão $b$ no Caso 1, que depende da leitura da figura original.

---

**Navegação:** [Anterior](08_referencias.md) | [Índice](README.md)
