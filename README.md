# TechChallengeF1 - Análise de E-commerce

## Membros / Autores

Grupo:

André Vieira de Souza - RM370784
Emanoel Dlugokenski - RM371337
Livia Alves de Oliveira - RM370348
Luís Felipe Soares - RM372528
Marcelo Henrique Mourão Abbade - RM373613

## Introdução

Projeto desenvolvido para o Tech Challenge da Pós-Graduação em Data Analytics FIAP.

O objetivo deste trabalho é transformar dados transacionais de e-commerce em insights estratégicos para investidores e acionistas, utilizando o dataset público Brazilian E-Commerce Public Dataset by Olist.

## 🎯 Problema de Negócio

Empresas de e-commerce geram grandes volumes de dados, mas muitas organizações ainda têm dificuldade em transformar esses dados em decisões estratégicas.

Neste projeto buscamos responder perguntas como:

- O marketplace está crescendo de forma sustentável?
- Quais categorias e regiões geram mais receita?
- A logística impacta a satisfação do cliente?
- Quais vendedores apresentam melhor desempenho?

O objetivo final é gerar recomendações estratégicas baseadas em dados.

## 📊 Principais Análises

### Crescimento do Marketplace

- evolução mensal de pedidos
- evolução da receita
- ticket médio

### Performance de Produtos

- categorias mais vendidas
- produtos com maior faturamento

### Logística

- tempo médio de entrega
- tempo entre compra e aprovação
- impacto do atraso nas avaliações

### Pagamentos

- meios de pagamento mais utilizados
- análise de parcelamento

### Satisfação do Cliente

- distribuição das avaliações
- correlação entre tempo de entrega e review score

## 🎯 Objetivo do Projeto

Construir uma análise exploratória e estratégica do mercado de e-commerce brasileiro com foco em:

- 📈 Crescimento de receita
- 🚚 Eficiência logística
- 💳 Comportamento de pagamento
- ⭐ Satisfação do cliente

A partir dessas análises, o projeto busca gerar recomendações de negócio baseadas em dados, apoiando decisões estratégicas para investimento no setor.

## 📦 Dataset

O projeto utiliza o dataset público: Brazilian E-Commerce Public Dataset by Olist

Ele contém aproximadamente:

- 100 mil pedidos
- período entre 2016 e 2018
- dados reais anonimizados de marketplaces brasileiros.

Principais dimensões analisadas:

- Clientes
- Pedidos
- Produtos
- Vendedores
- Pagamentos
- Avaliações
- Geolocalização

## 🗂 Estrutura dos Dados

Principais tabelas do dataset:

| Tabela               | Descrição                         |
| -------------------- | --------------------------------- |
| customers            | Informações dos clientes          |
| orders               | Status e datas dos pedidos        |
| order_items          | Produtos comprados em cada pedido |
| payments             | Informações de pagamento          |
| order_reviews        | Avaliações dos clientes           |
| products             | Informações dos produtos          |
| sellers              | Informações dos vendedores        |
| geolocation          | Dados geográficos por CEP         |
| category_translation | Tradução das categorias           |

## 🔎 Perguntas de Negócio

O projeto explora algumas perguntas estratégicas:

### 📈 Crescimento e Receita

- Como evoluíram os pedidos ao longo do tempo?
- Qual o ticket médio das compras?
- Quais categorias e regiões geram mais receita?

### 🚚 Logística

- Qual o tempo médio entre compra e entrega?
- Atrasos impactam as avaliações dos clientes?

### 💳 Pagamentos

- Quais meios de pagamento são mais utilizados?
- Como os clientes parcelam suas compras?

### ⭐ Satisfação do Cliente

- Qual a distribuição das avaliações?
- O tempo de entrega influencia a satisfação?

### 🚀 Oportunidades

- Quais sellers apresentam melhor desempenho?
- Onde existem oportunidades de melhoria logística?

## 🧠 Metodologia de Análise

O projeto segue as etapas:

- 1️⃣ Exploração e entendimento dos dados
- 2️⃣ Tratamento e limpeza dos dados
- 3️⃣ Análise exploratória (EDA)
- 4️⃣ Construção de métricas de negócio
- 5️⃣ Visualização e storytelling dos insights
- 6️⃣ Geração de recomendações estratégicas

## 🛠 Tecnologias Utilizadas

- Python
- Pandas
- Power BI
- Git / GitHub

## 📂 Estrutura do Repositório

```
.
├── Data
│   ├── raw
│   └── processed
│
├── Notebooks
│   └── analise_exploratoria.ipynb
│
├── PowerBI
│   └── dashboard_powerbi.pbix
│
├── Doc
│   └── apresentacao.pdf
│
└── README.md
```

## 📊 Resultados Esperados

O projeto busca gerar insights como:

- identificação de categorias e produtos mais rentáveis
- análise de performance logística
- identificação de drivers de satisfação do cliente
- oportunidades de crescimento e otimização

## 📑 Entregáveis

Este repositório faz parte do Tech Challenge da Fase 1 e inclui:

- 📁 Código utilizado nas análises
- 📊 Visualizações e dashboards
- 📄 Apresentação executiva
- 🎥 Vídeo de apresentação do projeto

# 📌 Observações

Este projeto tem caráter educacional, utilizando dados públicos disponibilizados pela Olist para fins de aprendizado em análise de dados e tomada de decisão baseada em dados.