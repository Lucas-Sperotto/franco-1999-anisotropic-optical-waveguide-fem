# VII. Conclusões

As conclusões do artigo devem ser lidas à luz da sequência de validação construída nas seções anteriores: parte-se de um caso homogêneo simples, avança-se para perfis isotrópicos difusos e, por fim, chega-se aos exemplos anisotrópicos em $LiNbO_3$. Esse percurso dá contexto à avaliação final da formulação escalar.

Apresentamos uma comparação entre os resultados obtidos por várias formulações propostas na literatura para o cálculo dos modos de propagação em guias de onda ópticos de importância tecnológica.

A caracterização de guias de onda próximos da região de corte é importante para o projeto de dispositivos monomodo, mas, nessa região, surgem discrepâncias entre todas as simulações. Infelizmente, existem poucas comparações na literatura entre resultados experimentais e resultados simulados.

As comparações mostraram que a formulação escalar parece ser tão confiável quanto outros métodos comumente utilizados para estudar os modos de propagação em guias de onda ópticos difusos. Essa informação é importante para o desenvolvimento de ferramentas computacionais confiáveis para a análise de dispositivos ópticos integrados complexos. As formulações escalares consomem menos memória e menos tempo de CPU do que as formulações vetoriais, permitindo a análise desses dispositivos complexos mesmo em computadores de baixo custo.

Para a futura implementação em C++, essas conclusões apontam duas prioridades simultâneas: manter a confiabilidade numérica ao longo dos casos de validação e, ao mesmo tempo, aproveitar a vantagem computacional da formulação escalar. Também reforçam que a região de corte merece atenção especial em malha, pós-processamento e comparação com referências.

---

**Navegação:** [Anterior](06_guia_de_onda_de_canal_difuso_anisotropico.md) | [Índice](README.md) | [Próximo](08_referencias.md)
