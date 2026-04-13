# AGENTS.md

## Objetivo do repositório

Este repositório tem como objetivo reproduzir, em C++, os resultados do artigo sobre análise por elementos finitos de guias de onda ópticos anisotrópicos com perfil arbitrário de índice.

A prioridade do projeto é:

1. fidelidade matemática à formulação adotada;
2. reprodutibilidade computacional;
3. validação progressiva por casos de teste;
4. organização limpa entre documentação, código, scripts e saídas.

## Papel da pasta docs

A pasta `docs/` é a base documental oficial do projeto.

Ela contém:

- a tradução técnica revisada do artigo;
- a interpretação matemática adotada;
- o resumo dos casos de teste;
- o material de apoio para implementação.

Regra principal:

- não alterar `docs/` livremente;
- não apagar conteúdo de `docs/`;
- não reescrever trechos de `docs/` por simplificação;
- só propor mudanças em `docs/` quando houver justificativa técnica clara;
- em caso de ambiguidade, preferir acrescentar observação editorial em vez de substituir conteúdo.

## Estrutura esperada do repositório

O repositório deve manter a seguinte separação lógica:

- `docs/` → documentação técnica e tradução do artigo
- `src/` → implementação em C++
- `include/` → headers e interfaces
- `scripts/` → automação com `.sh` e scripts Python
- `cases/` → arquivos de entrada dos casos de teste
- `tests/` → testes unitários e testes de sanidade
- `out/` → saídas geradas pelas execuções
- `meshes/` → arquivos de malha e insumos geométricos

Não criar estruturas paralelas desnecessárias.

## Regras de implementação

1. Trabalhar sempre em etapas pequenas, verificáveis e reversíveis.
2. Não tentar implementar todos os casos do artigo de uma vez.
3. Antes de adicionar complexidade física, consolidar a infraestrutura numérica mínima.
4. Toda alteração em `src/` deve preservar compilação ou deixar explicitado o bloqueio real.
5. Toda funcionalidade nova deve ter pelo menos um teste de sanidade, validação simples ou script de execução demonstrável.
6. Não introduzir fórmulas que não estejam sustentadas por `docs/` ou por decisão explícita documentada.
7. Em caso de ambiguidade matemática, não inventar. Registrar a dúvida e isolar o ponto.
8. Priorizar legibilidade, rastreabilidade e consistência antes de otimizações prematuras.

## Estratégia de desenvolvimento

A implementação deve seguir esta ordem geral:

1. infraestrutura do repositório;
2. contrato de entrada e saída;
3. geometria do elemento triangular linear;
4. montagem local e global;
5. problema generalizado de autovalor;
6. caso 1: guia de canal isotrópico homogêneo;
7. caso 2: guia planar difuso isotrópico;
8. caso 3: canal difuso isotrópico com perfil circular;
9. caso 4: canal difuso isotrópico Gaussian-Gaussian;
10. caso 5: guia anisotrópico APE em LiNbO3;
11. caso 6: guia anisotrópico Ti-difundido em LiNbO3.

Não pular etapas sem necessidade.

## Convenções de entrada

Os casos devem ser configurados por arquivos em `cases/`, preferencialmente em YAML.

Cada caso deve conter, de forma clara:

- identificação do caso;
- parâmetros geométricos;
- parâmetros materiais;
- parâmetros numéricos;
- malha associada;
- número de modos desejados;
- observações relevantes.

## Convenções de execução

A execução deve ser feita por scripts `.sh` em `scripts/`.

O fluxo esperado é:

1. compilar;
2. executar o caso;
3. salvar resultados em `out/`;
4. chamar scripts auxiliares de pós-processamento, quando necessário.

Evitar execuções manuais fragmentadas quando houver script correspondente.

## Convenções de saída

Toda execução deve salvar saídas dentro de `out/`, em subpastas por caso.

Exemplo:

`out/case01_homogeneous_channel/`

Cada pasta de saída deve buscar conter:

- snapshot das entradas;
- log de execução;
- autovalores;
- autovetores;
- índices efetivos;
- dados de modos;
- metadados da malha;
- figuras e gráficos, quando aplicável.

Não salvar resultados soltos na raiz do repositório.

## Regras para scripts

- scripts `.sh` são a interface principal de build e execução;
- scripts Python devem ser usados para apoio, pós-processamento e gráficos;
- evitar duplicação de lógica entre scripts;
- preferir pequenos utilitários reutilizáveis.

## Regras para testes

Os testes devem validar, progressivamente:

- geometria elementar;
- funções de forma;
- montagem básica;
- consistência de dimensões matriciais;
- resolução do problema espectral;
- comportamento mínimo esperado em cada caso.

Quando não houver teste unitário formal, pelo menos fornecer teste de sanidade reproduzível.

## Regras de estilo para o código C++

- preferir clareza a abstrações excessivas;
- usar nomes consistentes com a formulação do artigo;
- documentar blocos matematicamente sensíveis;
- separar bem geometria, materiais, montagem, solver e I/O;
- evitar acoplamento desnecessário;
- não esconder lógica importante em macros obscuras.

## Regras para modificações em arquivos existentes

Antes de editar:

- ler os arquivos relacionados;
- entender a função atual de cada módulo;
- preservar compatibilidade com a estrutura do projeto.

Ao final de cada tarefa:

- resumir o que foi feito;
- listar os arquivos alterados;
- explicar como compilar;
- explicar como executar;
- apontar limitações restantes.

## Regras de segurança intelectual do projeto

Este projeto é de reprodução numérica, não de improvisação.

Portanto:

- não “corrigir” o artigo por palpite;
- não substituir formulações por versões mais convenientes sem registro;
- não apagar ambiguidades históricas importantes;
- não mascarar dificuldades numéricas com explicações vagas.

Sempre que houver incerteza:

- registrar;
- isolar;
- tornar auditável.

## Definição de sucesso

Uma etapa só é considerada concluída quando:

- a alteração está coerente com `docs/`;
- compila ou falha por motivo claramente identificado;
- possui execução verificável;
- gera artefato reproduzível;
- deixa o repositório mais organizado, não mais confuso.
