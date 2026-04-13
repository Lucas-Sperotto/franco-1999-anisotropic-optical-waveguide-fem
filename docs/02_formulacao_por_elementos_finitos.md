# II. Formulação por Elementos Finitos

Esta seção reúne o núcleo matemático do artigo e deve ser lida como a ponte entre a física do problema e a futura implementação numérica. O objetivo aqui não é apenas registrar as equações, mas também explicitar como elas se organizam em um problema generalizado de autovalor para a determinação de $n_{\mathrm{eff}}$ e dos campos modais associados.

**Convenção importante de leitura.** Ao longo desta documentação, os subscritos em $n_x$, $n_y$ e $n_z$ referem-se às componentes principais do tensor de permissividade relativa, enquanto $x$ e $y$ também aparecem como coordenadas da seção transversal nas expressões espaciais. Essa sobreposição de símbolos foi preservada para manter aderência ao artigo, mas convém distingui-la com cuidado durante a implementação.

Para dielétricos anisotrópicos nos quais o tensor de permissividade relativa é diagonal,

$$
\bar{\varepsilon}_r =
\begin{bmatrix}
n_x^2(x,y) & 0 & 0 \\
0 & n_y^2(x,y) & 0 \\
0 & 0 & n_z^2(x,y)
\end{bmatrix},
$$

onde $n_x$, $n_y$ e $n_z$ são os índices de refração, a equação escalar de onda para modos $E^x$ ($E_y = 0$ na aproximação TE) é escrita como segue [9]:

## (1)

$$
\frac{\partial^2}{\partial x^2}\left(n_x^2 E_x\right) + n_z^2 \frac{\partial^2 E_x}{\partial y^2} + n_z^2 \frac{\partial}{\partial x}\left(\frac{1}{n_z^2}\right)\frac{\partial}{\partial x}\left(n_x^2 E_x\right) - \beta^2 n_x^2 E_x + k_0^2 n_x^2 n_z^2 E_x = 0.
$$

Aplicando o Método dos Resíduos Ponderados à equação (1), obtém-se:

## (2)

$$
[F]\{E_x\}^T = n_{\mathrm{eff}}^2 [M]\{E_x\}^T
$$

onde $n_{\mathrm{eff}} = \beta / k_0$ é o índice efetivo, e $k_0$ é o número de onda no espaço livre. As matrizes $[F]$ e $[M]$ para elementos finitos triangulares são:

Essa escrita deixa claro que a quantidade procurada no problema modal pode ser interpretada como um autovalor generalizado associado a $n_{\mathrm{eff}}^2$, enquanto o vetor nodal de $E_x$ representa a forma modal discretizada. Do ponto de vista computacional, esse detalhe é central porque a presença de termos com derivadas do índice torna a formulação, em geral, não simétrica.

## (3a)

$$
[M] = 2 A k_0^2 \int_{\zeta_1}\int_{\zeta_2} n_z^2 \{N\}^T \{N\}\, d\zeta_1\, d\zeta_2,
$$

## (3b)

$$
[F] = [F_1] - [F_2] - [F_3] + [F_4],
$$

onde:

$$
[F_1] = 2 A k_0^2 \int_{\zeta_1}\int_{\zeta_2} n_x^2 n_z^2 \{N\}^T \{N\}\, d\zeta_1\, d\zeta_2,
$$

$$
[F_2] = \sum_{i,j=1}^{3} \left(\frac{b_i b_j}{2A} \int_{\zeta_1}\int_{\zeta_2} \left( n_x^2 \frac{\partial \{N\}^T}{\partial \zeta_i}\frac{\partial \{N\}}{\partial \zeta_j} + \delta_x \frac{\partial \{N\}^T}{\partial \zeta_i} \frac{\partial n_x^2}{\partial \zeta_j} \{N\} \right) d\zeta_1 d\zeta_2\right),
$$

$$
[F_3] = \sum_{i,j=1}^{3} \left(\frac{c_i c_j}{2A} \int_{\zeta_1}\int_{\zeta_2} \left( n_z^2 \frac{\partial \{N\}^T}{\partial  \zeta_i}\frac{\partial \{N\}}{\partial \zeta_j} + \delta_z \{N\}^T \frac{\partial n_z^2}{\partial \zeta_i} \frac{\partial \{N\}}{\partial \zeta_j} \right) d\zeta_1 d\zeta_2\right),
$$

$$
[F_4] = \sum_{i,j=1}^{3} \left(\frac{b_i b_j}{2A} \int_{\zeta_1}\int_{\zeta_2} \left( \delta_z n_z^2 \frac{\partial g_z^2}{\partial \zeta_i} \right) \left( \delta_x \frac{\partial n_x^2}{\partial \zeta_j} \{N\}^T \{N\} \right) d\zeta_1 d\zeta_2\right)
$$

$$
\qquad\qquad + \sum_{i,j=1}^{3} \left(\frac{b_i b_j}{2A} \int_{\zeta_1}\int_{\zeta_2}
\left( \delta_z n_z^2 \frac{\partial g_z^2}{\partial \zeta_i} \right)
\left( n_x^2 \{N\}^T \frac{\partial \{N\}}{\partial \zeta_j} \right) d\zeta_1 d\zeta_2\right).
$$

$A$ é a área do triângulo, $\{N\}$ é um vetor linha que representa um conjunto completo de funções de base, $\{\ \}^T$ denota uma matriz transposta, $\zeta_i$ são as coordenadas homogêneas independentes, e $b_i$ e $c_i$ são os coeficientes de transformação de coordenadas do sistema homogêneo.

Excetuando-se os termos que contêm as derivadas parciais do índice de refração, esta é a mesma abordagem utilizada por Koshiba para guias de onda planares anisotrópicos [14] e para guias de onda de canal isotrópicos [6]. Em $[F_2]$, $[F_3]$ e $[F_4]$, os parâmetros $\delta_x$ e $\delta_z$ assumem valor 1 para índice difuso nas direções $x$ e $z$, respectivamente, ou zero para índice constante. Em regiões anisotrópicas homogêneas, as matrizes em (3) reduzem-se às matrizes apresentadas em [16], e para regiões homogêneas isotrópicas às matrizes apresentadas em [17]. As matrizes $[F_2]$, $[F_3]$ e $[F_4]$ são esparsas e não simétricas devido à presença de termos com $dn^2/d\zeta$.

Em termos práticos, isso significa que a futura implementação em C++ não deve assumir, sem verificação, uma estrutura simétrica para a matriz global. Também significa que a modelagem do perfil material precisa fornecer não apenas os valores de $n_x^2$ e $n_z^2$, mas também suas derivadas espaciais nas regiões difusas relevantes.

A variável de estado $E_x$ e os índices de refração são modelados usando a aproximação nodal:

## (4)

$$
E_x = \{N\}\{E_x\}^T,
$$

e

## (5)

$$
n_k^2 = \{N\}\{n_k^2\}^T, \qquad k = x, z ,
$$

e

## (6)

$$
g_z^2 = \frac{1}{n_z^2} = \{N\}\{g_z^2\}^T.
$$

Todas as integrais em (3) foram previamente calculadas por integração analítica, utilizando a mesma abordagem descrita em [18].

Vale observar que, embora o tensor completo contenha também $n_y$, a formulação escalar para modos $E^x$ explicitada nesta seção passa a depender diretamente apenas das quantidades que aparecem em (1) e na discretização subsequente, em particular $n_x$, $n_z$ e $g_z^2 = 1/n_z^2$. Esse ponto ajuda a explicar por que as aproximações nodais em (5) e (6) são escritas apenas para as grandezas que entram explicitamente nas matrizes.

## Observações para implementação

- A malha triangular, as funções de forma e os coeficientes geométricos $A$, $b_i$ e $c_i$ formam o núcleo geométrico da discretização.
- O modelo de material precisa fornecer valores nodais e, de modo consistente, derivadas espaciais dos perfis relevantes nas regiões difusas.
- A presença de termos não simétricos sugere o uso de um resolvedor de autovalor generalizado compatível com matrizes esparsas não simétricas.
- A formulação desta seção deve ser lida em conjunto com os casos de validação das seções [03](03_guia_de_onda_de_canal_isotropico_homogeneo.md) a [06](06_guia_de_onda_de_canal_difuso_anisotropico.md), pois é neles que os coeficientes materiais assumem formas concretas.

> Observação editorial: a expressão de $[F_4]$ foi preservada exatamente como na versão documental já consolidada no repositório. Como esse é um dos trechos mais suscetíveis a ambiguidades tipográficas em documentos escaneados, vale conferir novamente esse termo no PDF original durante a implementação, sobretudo a combinação entre $g_z^2 = 1/n_z^2$, $n_x^2$ e as derivadas em coordenadas homogêneas.

---

**Navegação:** [Anterior](01_introducao.md) | [Índice](README.md) | [Próximo](03_guia_de_onda_de_canal_isotropico_homogeneo.md)
