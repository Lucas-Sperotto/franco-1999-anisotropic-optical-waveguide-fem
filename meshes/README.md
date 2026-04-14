# Malhas

Esta pasta guarda malhas e insumos geométricos associados aos casos.

Neste estágio, os arquivos [placeholder_triangle.mesh](placeholder_triangle.mesh), [unit_square_center.mesh](unit_square_center.mesh), [planar_strip_3x9.mesh](planar_strip_3x9.mesh), [planar_strip_y4_coarse.mesh](planar_strip_y4_coarse.mesh), [planar_strip_y4_fine.mesh](planar_strip_y4_fine.mesh), [planar_strip_y6_coarse.mesh](planar_strip_y6_coarse.mesh), [planar_strip_y6_fine.mesh](planar_strip_y6_fine.mesh), [planar_d10_a2b_coarse.mesh](planar_d10_a2b_coarse.mesh) e [planar_d10_a2b_refined.mesh](planar_d10_a2b_refined.mesh) usam um formato mínimo orientado a teste:

- `format <nome_do_formato>`
- `dimension <dimensão>`
- `node <id> <x> <y>`
- `triangle <id> <n1> <n2> <n3>`

Esse formato já é suficiente para validar:

- leitura de malha;
- integridade de conectividade;
- construção da geometria do triângulo linear P1;
- cálculo de área, orientação e gradientes das funções de forma;
- detecção de nós de fronteira para Dirichlet;
- montagem global mínima em malhas triangulares P1;
- discretização simples de perfis materiais dependentes de `y`, como o primeiro caso planar difuso isotrópico.

As malhas estruturadas do estudo de sensibilidade do Caso 2 podem ser regeneradas por `scripts/generate_planar_strip_mesh.py`, o que mantém reproduzível a combinação entre refinamento vertical, refinamento local em torno da interface difusa e truncamento de domínio. Na configuração atual do Caso 2, o domínio computacional é `10 x 10`, com `d = 1`, refinamento concentrado perto de `y = 0` e nas primeiras profundidades de difusão, e apenas duas colunas em `x` para representar a faixa planar. A solução global do caso ativa uma redução `x`-invariante, de modo que a malha em `x` funcione como suporte geométrico da integração sem introduzir famílias artificiais de modos laterais.

Para o **Caso 1**, as malhas [channel_a2b_b1_smoke.mesh](channel_a2b_b1_smoke.mesh), [channel_a2b_b1_reference.mesh](channel_a2b_b1_reference.mesh) e [channel_a2b_b1_farfield.mesh](channel_a2b_b1_farfield.mesh) também são estruturadas e alinhadas às interfaces do núcleo retangular homogêneo. A hipótese geométrica adotada nesta etapa é `a = 2b`, com `b = 1`, `a = 2`, núcleo em `|x| <= 1` e `0 <= y <= 1`, cobertura acima da superfície `y = 0` e substrato nas demais regiões. O refinamento é concentrado dentro do núcleo e no seu entorno imediato, enquanto a malha `farfield` amplia o truncamento para estudar com mais honestidade os pontos próximos ao corte, onde o campo se espalha mais pelo revestimento e pelo substrato.
