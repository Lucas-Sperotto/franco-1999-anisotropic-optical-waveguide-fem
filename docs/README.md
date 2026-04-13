# Documentação do artigo

Esta pasta reúne a tradução técnica, a organização conceitual e a leitura estruturada do artigo que servirá de base para a futura reprodução computacional do problema em C++.

O objetivo desta documentação não é apenas armazenar uma tradução do texto original, mas transformá-lo em material de estudo, implementação e validação. Por isso, os arquivos foram organizados para acompanhar a progressão do artigo e, ao mesmo tempo, facilitar sua conversão em tarefas de modelagem numérica.

No estado atual do repositório, `docs/` é a parte central do projeto. Ainda não há uma implementação em C++, então esta pasta também funciona como especificação técnica inicial do que deverá ser codificado, validado e automatizado nas próximas etapas.

## O que esta pasta entrega

- tradução técnica com preservação da estrutura do artigo;
- consolidação da notação matemática e dos principais parâmetros;
- separação clara entre formulação, casos de validação, conclusões e referências;
- apoio para transformar o artigo em um plano de implementação progressiva;
- registro editorial de trechos que merecem conferência manual no PDF original.

## Ordem recomendada de leitura

1. [00_titulo_autores_resumo_descritores.md](00_titulo_autores_resumo_descritores.md)  
   Fixar o escopo do trabalho, os autores, o resumo e os termos de indexação.
2. [01_introducao.md](01_introducao.md)  
   Entender a motivação tecnológica e o posicionamento da formulação na literatura.
3. [02_formulacao_por_elementos_finitos.md](02_formulacao_por_elementos_finitos.md)  
   Estudar a equação escalar, a discretização FEM e o problema generalizado de autovalor.
4. [03_guia_de_onda_de_canal_isotropico_homogeneo.md](03_guia_de_onda_de_canal_isotropico_homogeneo.md)  
   Ler o primeiro caso de validação, homogêneo e mais simples.
5. [04_guia_de_onda_planar_difuso_isotropico.md](04_guia_de_onda_planar_difuso_isotropico.md)  
   Introduzir índice espacialmente variável em geometria planar.
6. [05_guia_de_onda_de_canal_difuso_isotropico.md](05_guia_de_onda_de_canal_difuso_isotropico.md)  
   Avançar para os dois casos isotrópicos de canal.
7. [06_guia_de_onda_de_canal_difuso_anisotropico.md](06_guia_de_onda_de_canal_difuso_anisotropico.md)  
   Estudar os casos anisotrópicos em $LiNbO_3$.
8. [07_conclusoes.md](07_conclusoes.md)  
   Fechar a leitura com a avaliação comparativa dos autores.
9. [08_referencias.md](08_referencias.md)  
   Consultar as fontes citadas no artigo.
10. [09_resumo_dos_casos_de_teste.md](09_resumo_dos_casos_de_teste.md)  
    Usar o mapa consolidado dos casos como apoio direto para planejamento da implementação.

## Papel de cada arquivo

### Abertura e contexto

- [00_titulo_autores_resumo_descritores.md](00_titulo_autores_resumo_descritores.md) define o escopo científico do trabalho logo na entrada.
- [01_introducao.md](01_introducao.md) explica por que comparar métodos para guias difusos isotrópicos e anisotrópicos é relevante.

### Núcleo matemático

- [02_formulacao_por_elementos_finitos.md](02_formulacao_por_elementos_finitos.md) concentra a formulação escalar para modos $E^x$, a decomposição matricial e as aproximações nodais.

### Casos de validação

- [03_guia_de_onda_de_canal_isotropico_homogeneo.md](03_guia_de_onda_de_canal_isotropico_homogeneo.md) é o teste mais simples do solver.
- [04_guia_de_onda_planar_difuso_isotropico.md](04_guia_de_onda_planar_difuso_isotropico.md) introduz variação espacial explícita de índice em um caso planar.
- [05_guia_de_onda_de_canal_difuso_isotropico.md](05_guia_de_onda_de_canal_difuso_isotropico.md) reúne dois casos isotrópicos de canal, um com perfil circular e outro Gaussian-Gaussian.
- [06_guia_de_onda_de_canal_difuso_anisotropico.md](06_guia_de_onda_de_canal_difuso_anisotropico.md) apresenta os casos APE e Ti:$LiNbO_3$, que são os mais ricos do ponto de vista material.

### Fechamento e apoio

- [07_conclusoes.md](07_conclusoes.md) resume a confiabilidade da formulação e a cautela necessária perto do corte.
- [08_referencias.md](08_referencias.md) preserva a base bibliográfica citada no artigo.
- [09_resumo_dos_casos_de_teste.md](09_resumo_dos_casos_de_teste.md) reorganiza os seis casos como sequência de implementação e validação.

## Convenções editoriais e de notação

- A notação $E^x$ foi preservada como no artigo e identifica a variável modal tratada na formulação escalar.
- A relação entre constante de propagação e índice efetivo é mantida como

$$
n_{\mathrm{eff}} = \frac{\beta}{k_0}.
$$

- Os termos “guia planar”, “guia de canal”, “índice efetivo”, “constante de propagação”, “difusão” e “anisotropia” foram mantidos de forma consistente ao longo dos arquivos.
- Em prosa, foi padronizado o uso de $LiNbO_3$ e Ti:$LiNbO_3$.
- As equações em destaque foram mantidas em blocos `$$...$$` para preservar legibilidade e fidelidade ao artigo.
- As referências a figuras e equações foram preservadas no estilo do texto técnico original, com acréscimos apenas quando isso melhorou a navegação entre arquivos.

## Como esta pasta conversa com a futura implementação em C++

Mesmo antes de existir código, já é possível enxergar uma decomposição natural do projeto:

- um núcleo FEM para malha, elementos triangulares, funções de forma e montagem matricial;
- uma camada de materiais para perfis isotrópicos, APE e Ti:$LiNbO_3$;
- uma camada de resolução modal para o problema generalizado de autovalor;
- uma camada de pós-processamento para curvas de dispersão, índices efetivos e tamanhos modais;
- uma rotina de validação caso a caso, alinhada com as figuras do artigo.

Em termos de sequência de trabalho, a ordem mais segura continua sendo:

1. validar o caso homogêneo;
2. introduzir perfis isotrópicos difusos;
3. atacar os casos de canal;
4. só então avançar para anisotropia em $LiNbO_3$.

## Pontos que exigem atenção especial

Alguns trechos já estão suficientemente claros para leitura e planejamento, mas merecem conferência manual quando a implementação começar:

- o termo $[F_4]$ em [02_formulacao_por_elementos_finitos.md](02_formulacao_por_elementos_finitos.md), por ser uma parte delicada da transcrição matemática;
- a definição explícita de $f(x,y)$ no caso Gaussian-Gaussian de [05_guia_de_onda_de_canal_difuso_isotropico.md](05_guia_de_onda_de_canal_difuso_isotropico.md);
- a parametrização geométrica associada à dimensão $b$ na normalização do Caso 1;
- a diferença entre cristal com corte em $x$ e em $c$ na comparação do caso Ti:$LiNbO_3$.

Nenhum desses pontos foi apagado ou “corrigido por suposição”. Quando houve ambiguidade relevante, a documentação foi mantida e acompanhada de observação editorial discreta.

## Uso prático desta pasta

Uma forma produtiva de usar `docs/` durante o desenvolvimento é:

1. escolher um caso em [09_resumo_dos_casos_de_teste.md](09_resumo_dos_casos_de_teste.md);
2. abrir o arquivo da seção correspondente;
3. recuperar equações, parâmetros, normalizações e figura-alvo;
4. traduzir isso para um caso de entrada do código;
5. resolver o problema modal;
6. comparar o resultado com a literatura e registrar diferenças perto do corte.

Esse fluxo ajuda a manter o projeto rastreável, incremental e cientificamente verificável.

---

**Navegação:** [Próximo](00_titulo_autores_resumo_descritores.md)
