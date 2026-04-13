# III. Guia de Onda de Canal Isotrópico Homogêneo

Esta seção apresenta o primeiro caso de validação do artigo e deve ser lida como o teste inicial da formulação em um cenário geometricamente simples e materialmente homogêneo. O interesse desse caso está menos na complexidade física e mais na sua utilidade como referência básica para verificar a montagem do problema modal.

O guia de onda retangular homogêneo foi simulado e os resultados para o modo fundamental $E^x$ foram comparados com outros métodos numéricos (Fig. 1). Este exemplo simples foi utilizado para testar a formulação para guias de onda homogêneos. A Fig. 1 mostra a boa concordância com o método vetorial da equação integral (VIE) e com o método do índice efetivo (EIM) [7]. O método de Marcatili [19] obtém uma constante de propagação menor nas proximidades do corte.

Essa comparação é didaticamente importante porque já introduz um padrão que será repetido ao longo do artigo: o valor da formulação não é avaliado apenas pela obtenção de um modo propagante, mas pela sua capacidade de reproduzir curvas de dispersão compatíveis com resultados consolidados na literatura.

![Figura 1 - Curvas de dispersão para guia de onda de canal isotrópico homogêneo.](img/fig_1.png)

**Fig. 1.** Curvas de dispersão para guia de onda de canal isotrópico homogêneo. A frequência normalizada é

$$
\left(\frac{k_0 b}{\pi}\right)\left(n_3^2 - n_2^2\right)^{1/2}
$$

e a constante de propagação normalizada é

$$
\frac{n_{\mathrm{eff}}^2 - n_2^2}{n_3^2 - n_2^2}.
$$

Os índices de refração são $n_1 = 1.0$, $n_2 = 1.43$ e $n_3 = 1.50$.

Do ponto de vista da futura implementação em C++, este caso deve ser tratado como o primeiro marco de validação: se a extração do modo fundamental, a normalização da curva e a comparação com a literatura falharem aqui, os casos difusos e anisotrópicos posteriores tenderão a mascarar problemas mais básicos de modelagem ou montagem.

> Observação editorial: a legenda usa $b$ como dimensão de referência na frequência normalizada. Como a geometria detalhada não é reescrita textualmente nesta seção, vale conferir diretamente a figura original do artigo ao parametrizar esse caso numérico.

Este caso corresponde ao **Caso 1** resumido em [09_resumo_dos_casos_de_teste.md](09_resumo_dos_casos_de_teste.md) e prepara a transição para o primeiro exemplo com índice espacialmente variável em [04_guia_de_onda_planar_difuso_isotropico.md](04_guia_de_onda_planar_difuso_isotropico.md).

---

**Navegação:** [Anterior](02_formulacao_por_elementos_finitos.md) | [Índice](README.md) | [Próximo](04_guia_de_onda_planar_difuso_isotropico.md)
