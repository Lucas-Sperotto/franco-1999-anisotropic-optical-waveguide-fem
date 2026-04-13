# Resumo dos Exemplos e Casos de Teste do Artigo

Este arquivo reúne, de forma organizada e didática, todos os exemplos numéricos e casos de teste apresentados no artigo. O objetivo é transformar a leitura do texto em uma referência prática para implementação, validação e automação no repositório.

Aqui, cada caso é descrito com foco em quatro perguntas fundamentais:

1. qual problema físico está sendo analisado;
2. quais são as entradas necessárias;
3. quais são as saídas esperadas;
4. qual papel o caso desempenha na validação da formulação.

Este documento deve ser lido como um guia de apoio para o desenvolvimento do código em C++, para a preparação dos scripts `.sh` e `.py`, e para a organização das pastas de saída em `out/`.

## Visão geral dos casos

O artigo trabalha com seis casos principais de validação:

1. guia de onda de canal isotrópico homogêneo;
2. guia de onda planar difuso isotrópico;
3. guia de onda de canal difuso isotrópico com perfil circular;
4. guia de onda de canal difuso isotrópico com perfil Gaussian-Gaussian;
5. guia de onda anisotrópico APE em LiNbO$_3$;
6. guia de onda anisotrópico Ti-difundido em LiNbO$_3$.

A sequência desses casos não é aleatória. Ela representa um caminho natural de aumento de complexidade:

- primeiro, um caso homogêneo simples;
- depois, um caso planar com índice variável;
- em seguida, canais isotrópicos difusos mais sofisticados;
- por fim, os casos anisotrópicos em material óptico de interesse tecnológico.

Essa ordem é uma excelente referência para a implementação progressiva do repositório.

---

## Caso 1 — Guia de Onda de Canal Isotrópico Homogêneo

### Objetivo do caso

Este é o caso mais simples entre os exemplos apresentados. Ele é usado para verificar se a formulação reproduz corretamente o comportamento de um guia retangular homogêneo.

Do ponto de vista numérico, este exemplo é importante porque permite validar o núcleo do solver antes de introduzir perfis espaciais difusos ou anisotropia.

### Entradas

As entradas essenciais deste caso são:

- geometria da seção transversal retangular;
- índices de refração das regiões do problema;
- definição do modo a ser analisado;
- faixa de frequência normalizada ou de número de onda a ser varrida.

Os índices informados no artigo são:

$$
n_1 = 1.0, \qquad n_2 = 1.43, \qquad n_3 = 1.50.
$$

A frequência normalizada é dada por:

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_3^2 - n_2^2\right)^{1/2}.
$$

### Saídas esperadas

As saídas principais são:

- curva de dispersão do modo fundamental $E^x$;
- índice efetivo ou constante de propagação normalizada;
- comparação com resultados de referência.

A constante de propagação normalizada usada no artigo é:

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_3^2 - n_2^2}.
$$

### Interpretação

Este caso deve ser entendido como um teste de consistência inicial. Se o código não reproduzir esse exemplo, não faz sentido avançar para os casos mais complexos.

### Papel na validação

Este caso valida:

- montagem básica do problema de autovalor;
- tratamento geométrico da seção retangular;
- extração do modo fundamental;
- comparação com métodos conhecidos da literatura.

---

## Caso 2 — Guia de Onda Planar Difuso Isotrópico

### Objetivo do caso

Este caso introduz uma variação espacial explícita do índice de refração em uma geometria planar. Ele serve para verificar se a formulação continua correta quando o material deixa de ser homogêneo.

### Entradas

As entradas centrais são:

- geometria planar;
- perfil exponencial do índice;
- profundidade de difusão;
- faixa de varredura do parâmetro normalizado.

O perfil de índice é:

$$
n(y) = 2.20 + 0.01 \exp\left(-\frac{|y|}{b}\right),
$$

onde $b$ é a profundidade de difusão.

### Saídas esperadas

As saídas são:

- os índices efetivos dos três modos $E^x$ de menor ordem;
- as curvas de dispersão associadas a esses modos;
- a comparação com soluções exatas e numéricas de referência.

### Interpretação

Este caso testa a capacidade do código de lidar com coeficientes materiais variáveis no domínio.

### Papel na validação

Este caso valida:

- avaliação espacial do índice de refração;
- consistência da formulação em meio isotrópico difuso;
- cálculo de múltiplos modos;
- capacidade de gerar curvas comparáveis às do artigo.

---

## Caso 3 — Guia de Onda de Canal Difuso Isotrópico com Perfil Circular

### Objetivo do caso

Este exemplo trata de um guia de onda com núcleo retangular no qual a difusão circular foi realizada apenas dentro do núcleo. É um caso mais rico geometricamente do que o planar e introduz uma descrição de perfil que depende da posição no domínio.

### Entradas

As entradas deste caso incluem:

- largura $a$ e altura $b$ da seção transversal retangular;
- índices do substrato, do ar e do máximo no núcleo;
- definição do perfil de índice;
- malha refinada para representar corretamente os modos próximos ao corte.

O artigo informa:

$$
n_2 = 1.44, \qquad n_{3m} = 1.5, \qquad n_1 = 1.0.
$$

O índice para a difusão circular é dado por:

$$
n_3 = n_2 + \frac{n_2 - n_{3m}}{L^2}\left(x^2 + y^2 - L^2\right),
$$

em que $L$ depende da posição de $P(x,y)$.

Se $|y| \geq |x|$, então:

$$
L = \sqrt{b^2 + x^2}.
$$

Caso contrário,

$$
L = \sqrt{\left(\frac{a}{2}\right)^2 + y^2}.
$$

O artigo também informa uma discretização de referência:

- 5680 triângulos lineares de primeira ordem;
- 2800 nós.

### Saídas esperadas

As saídas principais são:

- curva de dispersão para o modo $E^x_{11}$;
- constante de propagação normalizada;
- comparação com resultados obtidos por VIE, VFEM e SFEM.

A frequência normalizada é:

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_{3av}^2 - n_2^2\right)^{1/2},
$$

e a constante de propagação normalizada é:

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_{3av}^2 - n_2^2},
$$

com

$$
n_{3av} = 1.47.
$$

### Interpretação

Este é um caso importante para testar simultaneamente geometria, perfil espacial de material e comparação entre métodos.

### Papel na validação

Este caso valida:

- representação numérica de perfis definidos por expressões geométricas;
- influência do refinamento de malha;
- comportamento do solver fora e perto da região de corte;
- robustez da implementação em um caso 2D mais realista.

---

## Caso 4 — Guia de Onda de Canal Difuso Isotrópico com Perfil Gaussian-Gaussian

### Objetivo do caso

Este caso amplia o cenário do caso anterior ao adotar um perfil do tipo Gaussian-Gaussian, bastante usado em modelagem de difusão em guias ópticos.

### Entradas

As entradas incluem:

- geometria do canal;
- relação geométrica entre as dimensões;
- perfil Gaussian-Gaussian;
- índices do problema;
- faixa de frequência normalizada.

O artigo usa:

$$
n_3 = n_2 \left(1 + 0.05\,f(x,y)\right), \qquad \frac{a}{b} = 1,
$$

com

$$
n_1 = 1.0, \qquad n_2 = (2.1)^{1/2}, \qquad n_{3m} = 1.05\,n_2.
$$

A frequência normalizada é:

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_{3m}^2 - n_2^2\right)^{1/2}.
$$

### Saídas esperadas

As saídas esperadas são:

- curva de dispersão do modo $E^x_{11}$;
- constante de propagação normalizada;
- comparação com VM, Vector FE, VFD, Extended VFD e Var. FD.

A constante de propagação normalizada é:

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_{3m}^2 - n_2^2}.
$$

### Interpretação

Esse caso é especialmente útil para avaliar a qualidade numérica da formulação perto do corte, onde as diferenças entre métodos se tornam mais sensíveis.

### Papel na validação

Este caso valida:

- implementação de um perfil difuso mais elaborado;
- extração de resultados comparáveis a várias formulações da literatura;
- comportamento do código em uma região numericamente sensível.

---

## Caso 5 — Guia de Onda Anisotrópico APE em $LiNbO_3$

### Objetivo do caso

Este exemplo introduz anisotropia física de interesse tecnológico. O problema agora não é apenas um guia com índice variável, mas um material anisotrópico em que o processo APE altera apenas o índice extraordinário.

### Entradas

As entradas importantes são:

- material LiNbO$_3$;
- modelo de concentração de prótons;
- relação entre concentração e índice extraordinário;
- tempos e temperaturas do processo de troca protônica e recozimento;
- constantes de difusão anisotrópica;
- comprimento de onda de operação.

O modelo usado no artigo é:

$$
n_e(C) = n_{es} + \Delta n_e\left[1 - \exp(-11\,C)\right].
$$

As condições informadas são:

- PE por quinze minutos a $190^\circ$C;
- recozimento por quatro horas a $360^\circ$C.

As constantes dadas são:

$$
D_a(x\text{-cut}) = 0.92\ \mu\text{m}^2/\text{h},
$$

$$
D_a(z\text{-cut}) = 0.77\ \mu\text{m}^2/\text{h},
$$

e

$$
\lambda_0 = 0.6328\ \mu\text{m}.
$$

### Saídas esperadas

As saídas são:

- curvas de dispersão para os quatro modos $E^x$ de menor ordem;
- índice efetivo em função do número de onda;
- validação qualitativa do comportamento modal em guia APE anisotrópico.

### Interpretação

Este é o primeiro caso em que a anisotropia do meio se torna parte central da física do problema.

### Papel na validação

Este caso valida:

- tratamento anisotrópico do material;
- uso de perfis derivados de um processo físico de difusão;
- cálculo de múltiplos modos em meio anisotrópico.

---

## Caso 6 — Guia de Onda Anisotrópico Ti-difundido em $LiNbO_3$

### Objetivo do caso

Este é um dos casos mais completos do artigo. Ele combina anisotropia, perfil espacial complexo e parâmetros materiais ajustados experimentalmente.

### Entradas

As entradas deste caso são mais numerosas e exigem uma modelagem de material bem organizada.

O índice na região difundida é dado por:

$$
n_{e,o}^2(x,y,\lambda) = n_{b_{e,o}}^2 + \left[ \left(n_{b_{e,o}} + \Delta n_{s_{e,o}}\right)^2 - n_{b_{e,o}}^2 \right] \exp\left(-\frac{y^2}{d_y^2}\right) f\left(\frac{2x}{W}\right)
$$

A função auxiliar é:

$$
f\left(\frac{2x}{W}\right) = \frac{1}{2} \left\{
\operatorname{erf} \left[ \frac{W}{2d_x} \left( 1 + \frac{2x}{W} \right) \right] + \operatorname{erf} \left[ \frac{W}{2d_x} \left( 1 - \frac{2x}{W} \right) \right] \right\},
$$

Além disso, a variação do índice superficial é modelada por:

$$
\Delta n_{s_{e,o}}(\lambda) = \left[ B_0(\lambda) + B_1(\lambda)\frac{H}{d_{y_{e,o}}} \right] \left( \frac{H}{d_{y_{e,o}}} \right)^{\alpha_{e,o}},
$$

Os parâmetros informados pelo artigo incluem:

$$
H = 100\ \text{nm},
\qquad
\lambda = 1.523\ \mu\text{m},
\qquad
T = 1050^\circ\text{C},
\qquad
t = 8.5\ \text{h}.
$$

E também:

$$
d_{xe} = 4.60\ \mu\text{m}, \qquad d_{ye} = 4.00\ \mu\text{m},
$$

$$
d_{xo} = 6.23\ \mu\text{m}, \qquad d_{yo} = 4.98\ \mu\text{m},
$$

$$
n_{be} = 2.2125, \qquad n_{bo} = 2.1383,
$$

$$
\Delta n_{se} = 0.00446, \qquad \Delta n_{so} = 0.01217.
$$

### Saídas esperadas

As saídas principais são:

- índice efetivo do modo $E^x_{11}$;
- tamanhos de modo $W_x$ e $W_y$;
- curvas dessas grandezas em função da largura inicial da faixa de Ti.

### Interpretação

Este caso é especialmente relevante porque se aproxima mais de uma aplicação real de engenharia óptica do que os exemplos mais simples.

### Papel na validação

Este caso valida:

- modelagem anisotrópica mais completa;
- uso de funções erro e parâmetros ajustados;
- cálculo do índice efetivo e de dimensões do modo;
- capacidade do código de lidar com um caso materialmente rico e numericamente mais exigente.

---

## Resumo das entradas por categoria

Uma forma útil de organizar a futura implementação é separar as entradas por grupos.

### Entradas geométricas

São os dados associados ao domínio e à seção transversal:

- largura do núcleo;
- altura do núcleo;
- profundidade de difusão;
- geometria planar ou de canal;
- largura inicial da faixa de Ti;
- relações geométricas como $a/b$.

### Entradas materiais

São os dados ligados aos índices e à física do meio:

- índices de refração das regiões;
- perfis isotrópicos difusos;
- índices ordinário e extraordinário;
- parâmetros de difusão;
- concentração de prótons;
- coeficientes ajustados experimentalmente.

### Entradas numéricas

São os dados usados para controlar a solução computacional:

- malha;
- número de nós e elementos;
- refinamento local;
- faixa de varredura do parâmetro espectral;
- número de modos desejados;
- tolerâncias do solver.

### Entradas de validação

São os dados necessários para comparar o resultado do código com o artigo:

- grandeza a ser plotada;
- forma de normalização adotada;
- modos a serem comparados;
- figura-alvo do artigo.

---

## Resumo das saídas por categoria

Também é importante separar bem o que o código deverá produzir.

### Saídas espectrais

São os resultados ligados ao problema de autovalor:

- autovalores;
- índices efetivos;
- constantes de propagação;
- curvas de dispersão.

### Saídas modais

São os dados associados ao campo calculado:

- modo fundamental;
- modos de ordem superior;
- perfis de campo;
- dimensões modais como $W_x$ e $W_y$.

### Saídas de validação

São os produtos usados para comparação com o artigo:

- gráficos reproduzindo as figuras;
- tabelas comparativas;
- erro relativo ou desvio percentual;
- observações qualitativas sobre concordância perto do corte.

### Saídas de rastreabilidade

São os arquivos necessários para reprodutibilidade:

- arquivos `.csv` com resultados;
- arquivos `.json` ou `.yaml` com parâmetros usados;
- logs de execução;
- figuras salvas automaticamente em `out/`.

---

## Como este documento deve orientar o repositório

Este resumo pode ser usado como referência para estruturar a automação do projeto.

Uma organização coerente seria:

- um arquivo de entrada por caso;
- um script `.sh` para cada execução;
- um diretório `out/` separado por caso;
- um script Python para plotar e comparar com a figura correspondente do artigo.

Por exemplo, uma futura convenção razoável poderia ser:

```text
out/
├── case01_homogeneous_channel/
├── case02_planar_diffused/
├── case03_circular_channel/
├── case04_gaussian_channel/
├── case05_ape_linbo3/
└── case06_ti_linbo3/
````

Dentro de cada pasta, seria ideal salvar:

- parâmetros de entrada;
- resultados numéricos;
- curvas geradas;
- log de execução;
- figura final comparável ao artigo.

---

## Ordem recomendada de implementação

Este documento também sugere uma ordem prática para o desenvolvimento em C++:

1. Caso 1 — validar o núcleo do solver.
2. Caso 2 — introduzir coeficientes espaciais variáveis.
3. Caso 3 — tratar geometrias e perfis de canal mais complexos.
4. Caso 4 — refinar a robustez perto do corte.
5. Caso 5 — introduzir anisotropia APE.
6. Caso 6 — implementar o caso Ti:LiNbO$_3$ completo.

Essa progressão reduz o risco de tentar implementar um caso muito rico antes que a base esteja consolidada.

---

## Observação final

Os casos de teste do artigo não devem ser vistos apenas como exemplos ilustrativos. Eles formam, na prática, uma sequência de validação científica para o repositório.

Se o projeto conseguir reproduzir esses seis cenários com boa consistência, ele deixará de ser apenas uma implementação inspirada no artigo e passará a ser, de fato, uma reprodução numérica séria e verificável.

Por isso, este arquivo deve ser usado como referência direta no planejamento de:

- arquivos de entrada;
- scripts de compilação e execução;
- organização da pasta `out/`;
- critérios de validação;
- mensagens e tarefas futuras para o Codex.
