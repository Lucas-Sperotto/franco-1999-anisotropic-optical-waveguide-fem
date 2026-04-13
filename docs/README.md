# Documentação do artigo

Esta pasta reúne a tradução técnica, a organização conceitual e a leitura estruturada do artigo que servirá de base para a reprodução computacional do problema em C++.

O objetivo desta documentação não é apenas “guardar a tradução”, mas transformar o artigo em um material de estudo e implementação. Por isso, os arquivos foram organizados em ordem lógica, acompanhando a progressão do próprio texto: apresentação do trabalho, motivação, formulação matemática, casos de validação, conclusões e referências.

Outro ponto importante é que esta documentação já passou por uma revisão manual das equações e da notação. Isso é especialmente relevante porque o PDF original possui trechos escaneados com pequenas degradações visuais, o que pode introduzir ambiguidades em índices, sobrescritos, subscritos e alguns coeficientes. Nesta pasta, o conteúdo já foi ajustado a partir de uma leitura crítica do artigo, buscando fidelidade matemática e clareza editorial.

## Propósito desta pasta

Esta pasta foi criada para cumprir várias funções ao mesmo tempo:

- servir como tradução comentada do artigo;
- preservar a estrutura lógica do texto original;
- facilitar a leitura técnica antes da implementação;
- apoiar a modelagem do código em C++;
- ajudar na preparação de tarefas objetivas para o Codex;
- registrar, de maneira rastreável, a interpretação adotada para cada equação, parâmetro e caso numérico.

Em outras palavras, esta pasta funciona como a ponte entre o artigo científico e o repositório computacional.

## Como ler esta documentação

Embora os arquivos possam ser consultados isoladamente, o ideal é seguir a ordem numérica. O encadeamento foi pensado para que a compreensão física e matemática amadureça gradualmente.

A sequência recomendada é:

1. entender o escopo do artigo;
2. compreender a motivação da formulação;
3. estudar a formulação por elementos finitos;
4. analisar os casos isotrópicos mais simples;
5. avançar para os casos difusos mais complexos;
6. chegar aos exemplos anisotrópicos em LiNbO$_3$;
7. fechar com as conclusões e referências.

Esse fluxo também será útil na hora de implementar o projeto em etapas, pois a ordem dos documentos sugere uma ordem natural de validação numérica.

## Estrutura dos arquivos

### `00_...md`

Arquivo de abertura do artigo.

Contém o título, autores, afiliações, resumo, termos de indexação e nota editorial associada ao manuscrito. Este arquivo é importante porque define, logo no início, o escopo exato do trabalho: uma formulação escalar por elementos finitos para modos $E^x$ em guias de onda ópticos anisotrópicos com perfil arbitrário de índice.

Do ponto de vista do projeto, este arquivo é útil para responder perguntas como:

- o que exatamente o artigo pretende resolver;
- qual é a natureza da formulação;
- que tipo de meio físico está sendo tratado;
- quais comparações e validações os autores prometem apresentar.

Em um repositório técnico, essa abertura também ajuda a orientar o texto do `README.md` principal da raiz do projeto.

### `01_...md`

Introdução.

Este arquivo apresenta o contexto tecnológico e científico do artigo. Ele mostra por que guias de onda ópticos difusos são importantes, por que diferentes métodos numéricos aparecem na literatura e por que a comparação entre formulações é necessária.

Aqui também aparece uma informação essencial para o planejamento do código: os autores deixam claro que este trabalho é uma extensão de uma formulação anterior, agora adaptada para três índices de refração variando continuamente nas direções transversais.

Esse detalhe tem impacto direto na implementação, porque mostra que o problema não é apenas um caso homogêneo simples. Há variação espacial do material, e isso precisa aparecer explicitamente tanto na modelagem dos coeficientes quanto na montagem das matrizes.

### `02_...md`

Formulação por elementos finitos.

Este é o núcleo matemático do artigo e, provavelmente, o arquivo mais importante desta pasta para a futura implementação em C++.

Nele aparecem:

- o tensor de permissividade relativa diagonal;
- a equação escalar de onda para os modos $E^x$;
- a passagem para o problema generalizado de autovalor;
- a decomposição da matriz global em blocos como $[F_1]$, $[F_2]$, $[F_3]$ e $[F_4]$;
- a aproximação nodal da variável de estado e dos índices de refração;
- a interpretação dos parâmetros ligados a regiões difusas ou homogêneas.

Este documento deve ser lido com calma, porque dele sairão várias decisões de projeto, por exemplo:

- como representar a malha triangular;
- como organizar as funções de forma;
- como armazenar coeficientes geométricos;
- como avaliar $n_x$, $n_z$ e suas derivadas;
- como montar cada termo da formulação;
- como estruturar o problema de autovalor para obter $n_{\mathrm{eff}}$.

Em termos práticos, este é o arquivo que mais conversa com `src/`.

### `03_...md`

Guia de onda de canal isotrópico homogêneo.

Este é um primeiro caso de teste, mais simples, usado para verificar se a formulação reproduz corretamente resultados conhecidos em um cenário menos complicado.

Esse arquivo é muito valioso do ponto de vista de desenvolvimento, porque sugere um excelente primeiro marco de validação do código. Antes de enfrentar perfis espaciais mais sofisticados, é recomendável que o solver consiga reproduzir adequadamente esse exemplo.

Ele também mostra um padrão importante do artigo: cada caso não é apenas descrito matematicamente, mas comparado com resultados da literatura. Isso indica que o repositório deve nascer já com vocação para validação, e não apenas para “rodar”.

### `04_...md`

Guia de onda planar difuso isotrópico.

Aqui já aparece um perfil de índice com dependência espacial explícita, no caso um perfil exponencial. Este arquivo marca uma transição importante entre um problema homogêneo e um problema realmente difuso.

Ele é particularmente interessante porque permite testar:

- avaliação espacial do índice;
- consistência da montagem com coeficientes variáveis;
- cálculo dos modos de menor ordem;
- comparação de curvas de dispersão.

Em uma estratégia de implementação progressiva, este caso é ideal como segunda validação.

### `05_...md`

Guia de onda de canal difuso isotrópico.

Este arquivo aprofunda o estudo de guias isotrópicos com perfis mais elaborados. Aqui aparecem a geometria do núcleo retangular, a difusão circular, expressões por partes para a quantidade $L$, além de comparações com vários métodos numéricos da literatura.

Do ponto de vista computacional, este arquivo é muito rico porque exige mais do que uma simples montagem padrão. Ele envolve:

- interpretação geométrica do domínio;
- descrição de perfis espaciais definidos por regiões;
- análise perto da condição de corte;
- comparação entre diferentes formulações.

Além disso, a presença de mais de uma figura e de comparações múltiplas sugere que o repositório deverá ter scripts de pós-processamento bem organizados, capazes de gerar gráficos consistentes e comparáveis.

### `06_...md`

Guia de onda de canal difuso anisotrópico.

Este é um dos arquivos mais importantes da pasta, pois nele aparecem os exemplos anisotrópicos que justificam o foco principal do artigo.

A seção é dividida em duas partes:

- guia APE em LiNbO$_3$;
- guia Ti-difundido em LiNbO$_3$.

Esses exemplos introduzem modelos de índice mais ricos, parâmetros físicos de difusão, relações com concentração de prótons, funções com erro (`erf`) e coeficientes ajustados experimentalmente.

Para a futura implementação, este arquivo sinaliza que o projeto precisará de uma camada de modelagem de materiais relativamente bem organizada. Não será suficiente apenas montar elementos; será necessário também modelar perfis materiais de forma limpa, rastreável e reutilizável.

Em termos de arquitetura do código, este arquivo conversa fortemente com algo como:

- `src/materials/`
- `src/fem/`
- `scripts/plot_*.py`
- `out/caseXX/...`

### `07_...md`

Conclusões.

Este arquivo fecha o artigo e ajuda a entender o que os autores consideram como principal contribuição do trabalho.

As conclusões reforçam alguns pontos centrais:

- a formulação escalar apresentou boa confiabilidade;
- a região de corte continua sendo delicada para comparação entre métodos;
- formulações escalares podem ser vantajosas em memória e tempo de CPU;
- há interesse prático em desenvolver ferramentas confiáveis para análise de dispositivos ópticos integrados.

Para o repositório, isso significa que o projeto não deve ser visto apenas como um exercício acadêmico de transcrição de equações. Há um objetivo computacional claro: criar uma ferramenta sólida, validável e eficiente.

### `08_...md`

Referências.

Este arquivo reúne as referências bibliográficas do artigo. Ele é importante por duas razões.

A primeira é histórica e técnica: permite rastrear a base teórica e numérica da formulação. A segunda é prática: aponta materiais fundamentais para aprofundar pontos específicos durante a implementação.

Por exemplo, as referências podem ajudar a investigar:

- formulações escalares e vetoriais relacionadas;
- trabalhos clássicos de FEM em guias de onda ópticos;
- literatura sobre LiNbO$_3$ e perfis difusos;
- métodos de comparação para curvas de dispersão;
- bases conceituais para futuras extensões do projeto.

Em uma etapa posterior, este arquivo também pode servir de ponto de partida para uma seção bibliográfica mais ampla no `README.md` principal da raiz do repositório.

## Relação desta pasta com o restante do repositório

Embora esta pasta seja documental, ela foi pensada para dialogar diretamente com a estrutura computacional do projeto.

De forma ideal:

- `docs/` explica o problema;
- `src/` implementa o problema;
- `scripts/` automatiza compilação, execução, pós-processamento e validação;
- `out/` armazena os resultados gerados.

Essa separação é importante porque evita misturar teoria, código-fonte, automação e resultados num mesmo lugar. Além disso, ajuda bastante quando o projeto crescer.

## Como esta documentação ajudará na implementação

Esta pasta permitirá transformar o artigo em tarefas objetivas. Por exemplo:

- extrair a formulação fraca e a forma matricial;
- identificar quais coeficientes dependem da geometria;
- definir funções para perfis isotrópicos e anisotrópicos;
- construir casos de teste progressivos;
- comparar resultados numéricos com as figuras do artigo;
- documentar hipóteses, simplificações e escolhas de implementação.

Em outras palavras, antes de codificar, esta pasta ajuda a responder corretamente à pergunta mais importante de todas: **o que exatamente deve ser implementado?**

## Sugestão de uso prático

Uma boa forma de usar esta pasta no desenvolvimento é a seguinte:

1. ler o arquivo correspondente ao caso que se deseja implementar;
2. extrair as equações, parâmetros e dados de validação;
3. transformar isso em uma tarefa objetiva para o código;
4. implementar em `src/`;
5. criar um script `.sh` em `scripts/` para compilar e executar;
6. salvar os resultados em `out/`;
7. comparar com o comportamento descrito no documento da seção correspondente.

Esse ciclo tende a deixar o projeto mais limpo, verificável e reproduzível.
