# Finite Element Analysis of Anisotropic Optical Waveguide with Arbitrary Index Profile

## Título em português

### Análise por Elementos Finitos de Guia de Onda Óptico Anisotrópico com Perfil de Índice Arbitrário

## Autores

- Marcos A. R. Franco
- Angelo Passaro
- José R. Cardoso
- José M. Machado

## Afiliações

**Marcos A. R. Franco, Angelo Passaro**  
Centro Técnico Aeroespacial - CTA/IEAv  
Rod. Tamoios, km 5,3 - CEP: 12228-840  
São José dos Campos, SP, Brasil

**José R. Cardoso**  
LMAG - PEA - EPUSP  
Av. Prof. Luciano Gualberto, Trav. 3, nº 158 - CEP: 05508-900  
São Paulo, SP, Brasil

**José M. Machado**  
Departamento de Ciências da Computação e Estatística - IBILCE - UNESP  
CP 136 - CEP: 15054-000  
São José do Rio Preto, SP, Brasil

## Resumo

Este trabalho apresenta a aplicação de uma formulação escalar de elementos finitos para modos $E^x$ (do tipo TE) em guias de onda planares e de canal anisotrópicos com tensor de permissividade diagonal, difundidos em ambas as direções transversais. Essa formulação estendida considera explicitamente tanto as variações do índice de refração quanto suas derivadas espaciais no interior de cada elemento finito. São apresentadas curvas de dispersão para modos $E^x$ em guias de onda planares e de canal, e os resultados são comparados com soluções obtidas por outras formulações.

Como texto de abertura da pasta `docs`, este resumo também antecipa os três eixos que estruturam toda a documentação subsequente: a formulação matemática por elementos finitos, a validação progressiva em casos isotrópicos e a extensão para guias anisotrópicos tecnologicamente relevantes. Em particular, a relação entre constante de propagação $\beta$ e índice efetivo $n_{\mathrm{eff}}$ é retomada em detalhe em [02_formulacao_por_elementos_finitos.md](02_formulacao_por_elementos_finitos.md), enquanto os seis casos de validação são consolidados em [09_resumo_dos_casos_de_teste.md](09_resumo_dos_casos_de_teste.md).

## Termos de indexação

- Método dos elementos finitos
- Guias de onda com carregamento não homogêneo
- Guias de onda ópticos em faixa
- Meios anisotrópicos

## Observações de tradução

- O símbolo $E^x$ foi preservado como no artigo original.
- O termo **TE-like** foi traduzido como **do tipo TE**.
- Ao longo desta documentação, preserva-se a distinção entre **índice efetivo** $n_{\mathrm{eff}}$, **constante de propagação** $\beta$ e **modos** $E^x$, para evitar confusão entre grandezas físicas, autovalores normalizados e rótulos modais.
- O termo **Index terms** foi traduzido como **Termos de indexação**, mas também poderia ser representado como **Palavras-chave**, dependendo do padrão adotado no repositório.

## Nota editorial

Manuscrito recebido em 3 de junho de 1998.
M. A. R. Franco, fax: +55 12 344-1177, <marcos@ieav.cta.br>.
Este trabalho foi apoiado em parte pela FAPESP — Fundação de Amparo à Pesquisa do Estado de São Paulo, processo nº 95/06608-0.

## Observação editorial adicional

Este arquivo foi mantido como uma abertura fiel ao artigo, mas com acréscimos mínimos de orientação para leitura técnica. Seu papel principal é fixar o escopo exato do problema estudado antes da passagem para a introdução, a formulação e os casos de teste.

---

**Navegação:** [Anterior](README.md) | [Índice](README.md) | [Próximo](01_introducao.md)
