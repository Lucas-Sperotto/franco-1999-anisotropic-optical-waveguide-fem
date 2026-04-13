# IV. Guia de Onda Planar Difuso Isotrópico

Esta seção introduz o primeiro caso em que o índice de refração varia explicitamente no espaço, mantendo ainda uma geometria mais simples do que a dos guias de canal. Por isso, ela funciona como uma transição natural entre o teste homogêneo da seção anterior e os exemplos bidimensionais mais ricos das seções seguintes.

Um guia de onda óptico planar com perfil exponencial de índice foi utilizado para verificar a validade da presente formulação. A Fig. 2 mostra o índice efetivo para os três modos $E^x$ de menor ordem. Os resultados concordam tanto com as soluções exatas quanto com as soluções numéricas, fornecidas em [6] e representadas pelos pontos.

O valor didático desse caso está no fato de que ele separa, tanto quanto possível, dois tipos de dificuldade: por um lado, introduz a dependência espacial do material; por outro, evita ainda a complexidade geométrica adicional dos guias de canal. Isso o torna especialmente útil como segundo passo de validação numérica.

![Figura 2 - Curvas de dispersão para guia de onda óptico planar difuso isotrópico.](img/fig_2.png)

**Fig. 2.** Curvas de dispersão para guia de onda óptico planar difuso isotrópico, onde $b$ é a profundidade de difusão e

$$
n(y) = 2.20 + 0.01 \exp\left(-\frac{|y|}{b}\right).
$$

O perfil acima é par em relação a $y = 0$ e decai exponencialmente à medida que se afasta da região difundida. Em termos de implementação, isso significa que este caso já exige avaliação espacial consistente do índice, cálculo modal para mais de um autovalor relevante e geração de curvas de dispersão comparáveis com soluções de referência.

Este caso corresponde ao **Caso 2** resumido em [09_resumo_dos_casos_de_teste.md](09_resumo_dos_casos_de_teste.md) e prepara o avanço para os guias de canal difusos tratados em [05_guia_de_onda_de_canal_difuso_isotropico.md](05_guia_de_onda_de_canal_difuso_isotropico.md).

---

**Navegação:** [Anterior](03_guia_de_onda_de_canal_isotropico_homogeneo.md) | [Índice](README.md) | [Próximo](05_guia_de_onda_de_canal_difuso_isotropico.md)
