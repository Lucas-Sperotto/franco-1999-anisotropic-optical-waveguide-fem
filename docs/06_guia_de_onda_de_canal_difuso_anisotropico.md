# VI. Guia de Onda de Canal Difuso Anisotrópico

## A. Guia de onda obtido por troca protônica com recozimento

Guias de onda ópticos de LiNbO$_3$ obtidos por troca protônica com recozimento (*annealed proton-exchanged* — APE) possuem a propriedade de polarização única, porque o processo APE altera apenas o índice de refração extraordinário.

A variação do índice após o processo de troca protônica (PE) é aproximada por um índice inicial em degrau ($\Delta n_{\mathrm{PE}} = 0.12$). Subsequentemente, o processo de recozimento foi simulado por uma equação de difusão anisotrópica linear bidimensional resolvida pelo método dos elementos finitos.

A variação do índice extraordinário foi relacionada à concentração de prótons no substrato da seguinte forma [20]:

$$
n_e(C) = n_{es} + \Delta n_e \left[1 - \exp(-11C)\right],
\tag{8}
$$

onde $C$ é a concentração normalizada de prótons ($0 < C < 1$), $n_{es}$ é o índice de refração extraordinário do LiNbO$_3$ e $\Delta n_e$ é a variação máxima do índice de refração induzida pelo processo de troca protônica (PE).

A Fig. 6 mostra as curvas de dispersão para os quatro modos $E^x$ de menor ordem em um guia APE de LiNbO$_3$ com corte em $x$. Os tempos de PE e de recozimento são, respectivamente, quinze minutos a $190^\circ$C e quatro horas a $360^\circ$C.

A dispersão do índice de refração não foi considerada neste exemplo. Uma análise detalhada para esse caso foi apresentada em um trabalho anterior [9].

![Figura 6 - Curvas de dispersão para os quatro modos Ex de menor ordem em guia APE x-cut de LiNbO3.](img/fig_6.png)

**Fig. 6.** Curvas de dispersão para os quatro modos $E^x$ de menor ordem em guia de onda APE de LiNbO$_3$ com corte em $x$. Para $360^\circ$C, as constantes de difusão do recozimento são $ D_a(x\text{-cut}) = 0.92\ \mu\text{m}^2/\text{h} $, $ D_a(z\text{-cut}) = 0.77\ \mu\text{m}^2/\text{h} $, e $ \lambda_0 = 0.6328\ \mu\text{m} $.

## B. Guia de onda Ti-difundido em LiNbO$_3$

Para guias de onda de canal Ti:LiNbO$_3$, o índice de refração na região difundida segue [21]:

$$
n_{e,o}^2(x,y,\lambda) = n_{b_{e,o}}^2 + \left[ \left(n_{b_{e,o}} + \Delta n_{s_{e,o}}\right)^2 - n_{b_{e,o}}^2 \right] \exp\left(-\frac{y^2}{d_y^2}\right) f\left(\frac{2x}{W}\right) \tag{10}
$$

onde

$$
f\left(\frac{2x}{W}\right) = \frac{1}{2} \left\{
\operatorname{erf} \left[ \frac{W}{2d_x} \left( 1 + \frac{2x}{W} \right) \right] + \operatorname{erf} \left[ \frac{W}{2d_x} \left( 1 - \frac{2x}{W} \right) \right] \right\}, \tag{11}
$$

$e$ e $o$ denotam, respectivamente, os raios extraordinário e ordinário; $x$ e $y$ são as coordenadas de um ponto no substrato; $W$ é a largura inicial da faixa de Ti; $d_x$ e $d_y$ são, respectivamente, a largura e a profundidade de difusão; $n_b$ é o índice de refração do substrato; e $\Delta n_s$ representa a variação do índice superficial com o comprimento de onda.

Além disso, $\Delta n_{s_{e,o}}$ é dado em termos de $H$ (a espessura inicial da faixa de Ti) e de alguns parâmetros de ajuste [22]:

$$
\Delta n_{s_{e,o}}(\lambda) = \left[ B_0(\lambda) + B_1(\lambda)\frac{H}{d_{y_{e,o}}} \right] \left( \frac{H}{d_{y_{e,o}}} \right)^{\alpha_{e,o}}, \tag{12}
$$

com

$$
\alpha_e = 0.83,
\qquad
\alpha_o = 0.53,
$$

$$
B_{0_e}(\lambda) = 0.385 - 0.430\lambda + 0.171\lambda^2,
$$

$$
B_{1_e}(\lambda) = 9.130 + 3.850\lambda - 2.490\lambda^2,
$$

$$
B_{0_o}(\lambda) = 0.0653 - 0.0315\lambda + 0.0071\lambda^2,
$$

$$
B_{1_o}(\lambda) = 0.4780 + 0.4640\lambda - 0.3480\lambda^2.
$$

As simulações foram realizadas para um guia construído em um cristal com corte em $x$, com espessura inicial da faixa de Ti igual a $H = 100$ nm, $\lambda = 1.523\ \mu\text{m}$, $T = 1050^\circ$C e tempo de difusão $t = 8.5$ h. Usando os parâmetros de difusão obtidos de [21] e [22], foram derivados os seguintes dados de entrada:

$$
d_{xe} = 4.60\ \mu\text{m},
\qquad
d_{ye} = 4.00\ \mu\text{m},
$$

$$
d_{xo} = 6.23\ \mu\text{m},
\qquad
d_{yo} = 4.98\ \mu\text{m},
$$

$$
n_{be} = 2.2125,
\qquad
n_{bo} = 2.1383,
$$

$$
\Delta n_{se} = 0.00446,
\qquad
\Delta n_{so} = 0.01217.
$$

A Fig. 7 mostra o índice efetivo calculado para o modo $E^x_{11}$ e os tamanhos de modo $W_x$ e $W_y$ (largura total à meia altura da intensidade de campo) em função da largura inicial da faixa de Ti. O comportamento dessas curvas está em boa concordância com os resultados apresentados em [21]. Esses resultados não foram incluídos na figura porque suas curvas foram obtidas para um cristal com corte em $c$.

![Figura 7 - Índice efetivo e dimensões do modo em função da largura inicial da faixa de Ti.](img/fig_7.png)

**Fig. 7.** Índice efetivo ($n_{\mathrm{eff}}$) e tamanhos de modo $W_x$ e $W_y$ em função da largura inicial da faixa de Ti.
