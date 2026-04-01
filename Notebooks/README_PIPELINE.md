# Pipeline de Tratamento de Dados — Olist E-commerce
## TechChallengeF1 | Pós-Graduação Data Analytics FIAP

Este diretório contém o pipeline Python completo que justifica e documenta
todas as decisões de tratamento dos dados utilizados no dashboard Power BI.

---

## Estrutura dos Scripts

```
📂 Notebooks/
 ├── 01_data_audit.py       → Auditoria inicial dos dados brutos
 ├── 02_data_cleaning.py    → Limpeza e tratamento documentado
 ├── 03_build_master.py     → Construção da tabela analítica mestre
 └── 04_eda_metrics.py      → EDA e geração de métricas para o Power BI
```

---

## Como Executar

### 1. Instalar dependências

```bash
pip install pandas numpy pyarrow
```

### 2. Executar o pipeline em sequência

```bash
# Passo 1 — auditar dados brutos (gera relatório de qualidade)
python 01_data_audit.py --data_dir ./Data/raw

# Passo 2 — limpar e tratar dados
python 02_data_cleaning.py --raw_dir ./Data/raw --out_dir ./Data/processed

# Passo 3 — construir tabela analítica mestre
python 03_build_master.py --processed_dir ./Data/processed

# Passo 4 — calcular métricas de negócio
python 04_eda_metrics.py --master ./Data/processed/master_orders.csv --out ./Data/metrics
```

---

## Decisões de Tratamento Documentadas

### 01 — Auditoria
- Mapeia nulos, duplicatas, intervalos de datas e estatísticas descritivas
- Gera `Data/audit/auditoria_inicial.txt` e `auditoria_inicial.csv`

### 02 — Limpeza

| Tabela        | Decisão                                                                 |
|---------------|-------------------------------------------------------------------------|
| orders        | Remove cancelados/unavailable → tabela separada para análise específica |
| orders        | Imputa `order_approved_at` nulo com `purchase + mediana de aprovação`   |
| orders        | Remove anomalias de entrega (>90 dias após estimativa)                  |
| order_items   | Remove itens com `price ≤ 0` e `freight_value < 0`                      |
| order_items   | Cria coluna derivada `revenue = price + freight_value`                  |
| payments      | Remove vouchers zerados (`payment_value ≤ 0`)                           |
| payments      | Normaliza `payment_type` (lower + strip)                                |
| reviews       | Deduplica por `review_id`, mantendo avaliação mais recente              |
| products      | Imputa dimensões nulas com mediana da categoria                         |
| products      | Preenche `product_category_name` nulo com `'sem_categoria'`             |
| customers     | Normaliza UF (upper) e CEP (5 dígitos com zero-padding)                 |
| sellers       | Normaliza UF (upper) e CEP (5 dígitos com zero-padding)                 |
| geolocation   | Remove duplicatas (zip, lat, lng) e coordenadas fora do bbox do Brasil  |

### 03 — Master Table
- Granularidade: **1 linha por item de pedido**
- JOINs: orders → customers, products, sellers, payments (agregado), reviews (agregado)
- Colunas derivadas:
  - `delivery_days`, `estimated_days`, `delay_days`, `is_late`
  - `approval_hours`, `year_month`, `year`, `month`, `weekday`
  - `customer_region`, `seller_region` (macro-regiões do Brasil)
  - `volume_cm3` (produto das dimensões físicas)
  - `price_segment` (faixas: <50, 50-100, 100-250, 250-500, >500)

### 04 — Métricas para o Power BI

Arquivos gerados em `Data/metrics/`:

| Arquivo                     | Uso no Dashboard                         |
|-----------------------------|------------------------------------------|
| `evolucao_mensal.csv`       | Gráfico de linha — crescimento mensal    |
| `crescimento_anual.csv`     | Card de KPI — YoY                        |
| `top_categorias_receita.csv`| Gráfico de barras — categorias           |
| `logistica_por_estado.csv`  | Mapa — entrega por UF                    |
| `atraso_vs_review.csv`      | Gráfico dispersão — logística × NPS      |
| `meios_pagamento.csv`       | Gráfico de rosca — pagamentos            |
| `parcelamento.csv`          | Histograma — parcelas crédito            |
| `distribuicao_review.csv`   | Gráfico de barras — distribuição scores  |
| `review_por_categoria.csv`  | Tabela rankeable — categorias × NPS      |
| `seller_performance.csv`    | Tabela de sellers — visão executiva      |
| `kpis_executivos.csv`       | Cards de KPI do painel executivo         |

---

## Estrutura de Pastas Esperada

```
📂 Data/
 ├── raw/                    → CSVs originais do Kaggle (Olist)
 ├── audit/                  → Relatórios de auditoria (gerado pelo script 01)
 ├── processed/              → Dados limpos + master_orders.csv (gerado pelo script 02-03)
 └── metrics/                → Métricas agregadas para o Power BI (gerado pelo script 04)
```

---

## Dataset

**Brazilian E-Commerce Public Dataset by Olist**  
Fonte: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce  
~100 mil pedidos | 2016-2018 | 9 tabelas relacionais

---

*Projeto educacional — Pós-Graduação em Data Analytics FIAP*
