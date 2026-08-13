# ADR-001 — Manter modelo de dados simples (sem Obra/Edição/Exemplar)

**Estado:** Aceite
**Data:** 13 de agosto de 2026
**Decisor:** Miguel Lopes

## Contexto

Numa análise externa ao projeto (revisão por ChatGPT e DeepSeek, ver
`relatorio-deepseek.md`, não versionado), foi proposta uma evolução do
modelo de dados para separar quatro conceitos hoje fundidos num único
registo `livro`:

- **Obra** — a história/conteúdo intelectual (ex: "Cem Anos de
  Solidão")
- **Edição** — uma publicação concreta dessa obra (editora, ano,
  ISBN)
- **Exemplar** — uma cópia física ou digital específica que o
  utilizador possui
- **Autor** — modelado como relação N:N em vez de campo de texto
  livre, para suportar múltiplos autores por obra

Esta separação é um padrão de modelação reconhecido (usado por
sistemas como o próprio catálogo da Open Library, cuja API já é
consumida por este projeto) e seria justificada se o utilizador
precisasse de:

1. Distinguir edições diferentes do mesmo livro (ex: capa dura de
   2015 vs. capa mole de 2020)
2. Registar o mesmo título em mais do que um formato (físico e
   digital) como posses distintas
3. Localizar fisicamente cada exemplar (estante, emprestado a
   terceiros, etc.)

## Decisão

**Não implementar a separação Obra/Edição/Exemplar nem Autor N:N
neste momento.** Mantém-se o modelo atual: um único registo `livro`
por título possuído, com autor como campo de texto simples.

A decisão baseou-se em verificação direta com o utilizador (não em
suposição): nenhum dos três cenários acima se aplica à biblioteca
pessoal real que esta aplicação gere. Não há edições duplicadas, não
há exemplares em mais do que um formato, e todos os livros físicos
estão no mesmo local.

## Consequências

**Positivas:**

- Esquema de base de dados permanece simples e fácil de raciocinar
  sobre (uma tabela, sem JOINs complexos para operações básicas)
- Esforço de engenharia redireciona-se para áreas com retorno
  imediato e verificável: cobertura de testes automatizados
  (`pytest`) e documentação de decisões (este próprio ADR)
- Evita "engenharia para o currículo" — construir complexidade que
  não serve o problema real apenas para parecer mais avançada é uma
  prática que um revisor técnico experiente tende a identificar e
  penalizar, não a valorizar

**Negativas / riscos aceites:**

- Se o âmbito do projeto mudar no futuro (ver secção seguinte), a
  migração para o modelo separado implica alterar o esquema da base
  de dados e todo o código que depende da estrutura atual de
  `livro` — não é uma alteração trivial feita depois
- Autor como texto livre não impede duplicação/inconsistência de
  nomes (ex: "Gabriel García Márquez" vs "García Márquez, Gabriel")
  entre registos diferentes

## Alternativas consideradas

**Implementar o modelo completo agora**, antecipando necessidades
futuras. Rejeitada: nenhuma das necessidades foi confirmada como
real; construir para um requisito hipotético é especulação, não
arquitetura orientada a problema.

## Nota sobre revisão futura

Foi levantada a possibilidade de, no futuro, a aplicação vir a ser
usada por mais do que uma pessoa. Esta hipótese **não** foi tratada
como requisito nesta decisão — implica alterações de âmbito muito
mais profundas do que o modelo de dados (autenticação, isolamento de
dados por utilizador, possível substituição do SQLite ficheiro-único
por uma solução com suporte a concorrência). Se e quando esse cenário
se tornar real, deve ser tratado como uma decisão de arquitetura
própria, com o seu próprio ADR — não deve influenciar decisões
tomadas hoje para um contexto de utilizador único.
