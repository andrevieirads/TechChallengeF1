# 📂 Data

Esta pasta contém os dados utilizados no projeto **TechChallengeF1 — Análise de E-commerce Olist**.

---

## Estrutura

```
Data/
├── raw/                        ← CSVs originais do Kaggle (não modificados)
│   ├── olist_customers_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   └── product_category_name_translation.csv
│
├── processed/                  ← Dados limpos gerados pelo pipeline Python
│   ├── orders_clean.csv
│   ├── orders_canceled.csv
│   ├── order_items_clean.csv
│   ├── payments_clean.csv
│   ├── reviews_clean.csv
│   ├── products_clean.csv
│   ├── customers_clean.csv
│   ├── sellers_clean.csv
│   ├── geolocation_clean.csv
│   ├── category_translation_clean.csv
│   ├── master_orders.csv       ← Tabela analítica mestre (input do Power BI)
│   ├── master_orders.parquet
│   ├── master_columns.txt      ← Dicionário de colunas do master
│   └── cleaning_log.txt        ← Log completo das decisões de limpeza
│
├── audit/                      ← Relatórios de qualidade dos dados brutos
│   ├── auditoria_inicial.txt
│   └── auditoria_inicial.csv
│
└── metrics/                    ← Métricas agregadas exportadas para o Power BI
    ├── evolucao_mensal.csv
    ├── crescimento_anual.csv
    ├── top_categorias_receita.csv
    ├── top_categorias_volume.csv
    ├── logistica_por_estado.csv
    ├── atraso_vs_review.csv
    ├── meios_pagamento.csv
    ├── parcelamento.csv
    ├── distribuicao_review.csv
    ├── review_por_categoria.csv
    ├── seller_performance.csv
    └── kpis_executivos.csv
```

> ⚠️ **Os arquivos da pasta `raw/` não estão versionados no repositório** por conta do tamanho (>100 MB). Veja instruções de download abaixo.

---

## Dataset de origem

**Brazilian E-Commerce Public Dataset by Olist**
- 🔗 Kaggle: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- ~100 mil pedidos reais e anonimizados
- Período: **setembro de 2016 a agosto de 2018**
- Licença: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

### Como baixar

```bash
# Opção 1 — Kaggle CLI
pip install kaggle
kaggle datasets download -d olistbr/brazilian-ecommerce
unzip brazilian-ecommerce.zip -d Data/raw/

# Opção 2 — Manual
# Acesse o link do Kaggle, faça login e clique em "Download".
# Extraia os CSVs para Data/raw/.
```

---

## Tabelas do dataset

| Tabela | Arquivo | Linhas (aprox.) | Descrição |
|--------|---------|-----------------|-----------|
| `customers` | `olist_customers_dataset.csv` | 99.441 | Dados dos clientes (ID, cidade, estado, CEP) |
| `orders` | `olist_orders_dataset.csv` | 99.441 | Status e timestamps dos pedidos |
| `order_items` | `olist_order_items_dataset.csv` | 112.650 | Produtos comprados em cada pedido, preço e frete |
| `payments` | `olist_order_payments_dataset.csv` | 103.886 | Método de pagamento, parcelas e valor |
| `reviews` | `olist_order_reviews_dataset.csv` | 99.224 | Avaliações dos clientes (score 1–5) |
| `products` | `olist_products_dataset.csv` | 32.951 | Atributos dos produtos (categoria, dimensões, peso) |
| `sellers` | `olist_sellers_dataset.csv` | 3.095 | Dados dos vendedores (ID, cidade, estado) |
| `geolocation` | `olist_geolocation_dataset.csv` | 1.000.163 | Coordenadas geográficas por CEP |
| `category_translation` | `product_category_name_translation.csv` | 71 | Tradução das categorias PT → EN |

### Diagrama de relacionamento

```
customers ──────┐
                │ customer_id
                ▼
geolocation    orders ──────── order_items ──── products
(zip_code)      │                    │
                │ order_id           │ seller_id
                ├──── payments       ▼
                ├──── reviews      sellers
                └──── order_items   (zip_code → geolocation)
```

---

## Decisões de tratamento dos dados

Todas as decisões abaixo são executadas pelos scripts em `Notebooks/` e registradas em `Data/processed/cleaning_log.txt`.

### `orders`
| Decisão | Justificativa |
|---------|---------------|
| Pedidos `canceled` e `unavailable` separados em `orders_canceled.csv` | Não representam receita realizada; mantidos para análise de taxa de cancelamento |
| `order_approved_at` nulo imputado com `purchase_timestamp + mediana de aprovação` | ~160 registros sem data de aprovação por aprovação automática imediata; imputação preserva a distribuição temporal |
| Registros com `order_delivered_customer_date` > `order_estimated_delivery_date` + 90 dias removidos | Anomalias de sistema (datas de 2020–2022 em um dataset de 2016–2018) |

### `order_items`
| Decisão | Justificativa |
|---------|---------------|
| Itens com `price ≤ 0` removidos | Preços negativos ou zerados são erros de entrada; não há produto gratuito no dataset |
| Itens com `freight_value < 0` removidos | Frete negativo é fisicamente impossível |
| Coluna `revenue = price + freight_value` criada | Representa o valor total pago pelo cliente no item |

### `payments`
| Decisão | Justificativa |
|---------|---------------|
| Registros com `payment_value ≤ 0` removidos | Vouchers zerados sem valor econômico real |
| `payment_type` normalizado (`lower + strip`) | Inconsistências de capitalização na fonte |
| Pagamentos `credit_card` com `installments = 0` removidos | Inconsistência lógica: crédito pressupõe ao menos 1 parcela |

### `reviews`
| Decisão | Justificativa |
|---------|---------------|
| Duplicatas de `review_id` removidas (mantida a mais recente) | O dataset contém reviews duplicadas por re-envio de formulário |
| Reviews com `review_score` fora de [1, 5] removidas | Valores fora da escala indicam erro de entrada |

### `products`
| Decisão | Justificativa |
|---------|---------------|
| `product_category_name` nulo preenchido com `'sem_categoria'` | Evita perda de produtos em agregações por categoria |
| Dimensões físicas nulas imputadas pela **mediana da categoria** | Preserva produtos para análises de logística; mediana é robusta a outliers |
| Produtos sem nenhum atributo físico removidos | Impossível calcular volume ou peso para análise de frete |

### `customers` e `sellers`
| Decisão | Justificativa |
|---------|---------------|
| `state` normalizado para maiúsculas (`upper + strip`) | Inconsistências de capitalização na fonte |
| `zip_code_prefix` padronizado para 5 dígitos com zero-padding | Garantir JOIN correto com a tabela de geolocalização |

### `geolocation`
| Decisão | Justificativa |
|---------|---------------|
| Duplicatas exatas de `(zip, lat, lng)` removidas | O dataset original tem ~260 mil linhas duplicadas |
| Coordenadas fora do bounding box do Brasil removidas (`lat: [-33.75, 5.27]`, `lng: [-73.99, -32.39]`) | Registros com coordenadas no Oceano Atlântico ou em outros países |

---

## Tabela mestre (`master_orders.csv`)

Gerada pelo script `03_build_master.py`. Granularidade: **1 linha por item de pedido**.

### Colunas derivadas adicionadas

| Coluna | Cálculo | Descrição |
|--------|---------|-----------|
| `revenue` | `price + freight_value` | Valor total pago pelo cliente no item |
| `delivery_days` | `delivered_date − purchase_date` (dias) | Tempo real de entrega |
| `estimated_days` | `estimated_date − purchase_date` (dias) | Prazo prometido ao cliente |
| `delay_days` | `delivery_days − estimated_days` | Positivo = atraso; negativo = adiantamento |
| `is_late` | `delay_days > 0` | Flag booleana de atraso |
| `approval_hours` | `approved_at − purchase_at` (horas) | Velocidade de aprovação do pedido |
| `year_month` | `YYYY-MM` | Chave de agregação temporal |
| `customer_region` | Mapeamento UF → macro-região | Norte / Nordeste / Centro-Oeste / Sudeste / Sul |
| `seller_region` | Mapeamento UF → macro-região | Norte / Nordeste / Centro-Oeste / Sudeste / Sul |
| `volume_cm3` | `length × width × height` | Volume físico do produto |
| `price_segment` | Faixas de preço | < R$50 / R$50-100 / R$100-250 / R$250-500 / > R$500 |

---

## Como reproduzir o pipeline

```bash
# Instalar dependências
pip install pandas numpy pyarrow

# 1. Auditar dados brutos
python Notebooks/01_data_audit.py --data_dir ./Data/raw

# 2. Limpar e tratar
python Notebooks/02_data_cleaning.py --raw_dir ./Data/raw --out_dir ./Data/processed

# 3. Construir master table
python Notebooks/03_build_master.py --processed_dir ./Data/processed

# 4. Gerar métricas para o Power BI
python Notebooks/04_eda_metrics.py --master ./Data/processed/master_orders.csv --out ./Data/metrics
```

---

## Notas sobre o versionamento

- `Data/raw/` → **não versionado** (`.gitignore`) por conta do tamanho dos arquivos
- `Data/processed/` → **não versionado** (gerado pelo pipeline)
- `Data/audit/` → **não versionado** (gerado pelo pipeline)
- `Data/metrics/` → **versionado** ✓ (inputs finais do Power BI, pequenos e estáveis)

---

*Projeto educacional — Pós-Graduação em Data Analytics FIAP*  
*Dataset: Brazilian E-Commerce Public Dataset by Olist (CC BY-NC-SA 4.0)*
