# Malhas

Esta pasta guarda malhas e insumos geométricos associados aos casos.

Neste estágio, os arquivos [placeholder_triangle.mesh](placeholder_triangle.mesh), [unit_square_center.mesh](unit_square_center.mesh) e [planar_strip_3x9.mesh](planar_strip_3x9.mesh) usam um formato mínimo orientado a teste:

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
