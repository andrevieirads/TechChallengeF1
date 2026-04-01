"""
02_data_cleaning.py
===================
Limpeza e tratamento dos dados brutos do dataset Brazilian E-Commerce (Olist).

Decisões de tratamento documentadas:
--------------------------------------
ORDERS
  - Remover pedidos com status 'canceled' e 'unavailable' para análise de receita
    (mantidos em tabela separada para análise de cancelamento).
  - Preencher order_approved_at nulo (pedidos aprovados automaticamente) com
    order_purchase_timestamp + mediana do tempo de aprovação.
  - Remover registros onde order_delivered_customer_date > order_estimated_delivery_date + 90 dias
    (anomalias de data — provavelmente erros de sistema).

ORDER_ITEMS
  - Remover itens com price <= 0 (4 registros conhecidos no dataset — preços negativos).
  - Remover itens com freight_value < 0 (impossível fisicamente).
  - Calcular coluna derivada: revenue = price + freight_value.

PAYMENTS
  - Remover registros com payment_value <= 0 (vouchers zerados sem valor real).
  - Normalizar payment_type: padronizar strings (lower + strip).

REVIEWS
  - Remover duplicatas de review_id mantendo a avaliação mais recente
    (review_answer_timestamp mais alto).
  - Padronizar review_score: garantir valores inteiros entre 1 e 5.

PRODUCTS
  - Imputar dimensões faltantes (product_length_cm, width, height, weight)
    com mediana da mesma categoria.
  - Imputar product_category_name nulo com 'sem_categoria'.
  - Remover produto sem nenhum atributo preenchido.

CUSTOMERS / SELLERS
  - Normalizar strings de estado (customer_state, seller_state): upper + strip.
  - Normalizar CEPs: garantir 8 dígitos com zero-padding.

GEOLOCATION
  - Remover duplicatas exatas de (geolocation_zip_code_prefix, lat, lng).
  - Manter apenas coordenadas dentro do bbox do Brasil:
    lat: [-33.75, 5.27]  |  lng: [-73.99, -32.39]

Uso:
    python 02_data_cleaning.py --raw_dir ./Data/raw --out_dir ./Data/processed

Saída:
    ./Data/processed/<tabela>_clean.csv  — uma tabela limpa por arquivo
    ./Data/processed/cleaning_log.txt    — log de todas as decisões tomadas
"""

import os
import argparse
from datetime import datetime
from typing import Tuple

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Utilitários de logging
# ---------------------------------------------------------------------------

LOG_LINES = []


def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    LOG_LINES.append(line)


def save_log(out_dir: str):
    path = os.path.join(out_dir, "cleaning_log.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("CLEANING LOG — OLIST DATASET\n")
        f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        f.write("\n".join(LOG_LINES))
    log(f"Log salvo em: {path}")


# ---------------------------------------------------------------------------
# Funções de limpeza por tabela
# ---------------------------------------------------------------------------

def clean_orders(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Retorna (orders_clean, orders_canceled).
    - orders_clean: pedidos válidos para análise de receita/entrega
    - orders_canceled: pedidos cancelados/unavailable (análise de cancelamento)
    """
    log("ORDERS — iniciando limpeza")
    n0 = len(df)

    # Parse datas
    date_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Separar cancelados
    canceled_status = ["canceled", "unavailable"]
    mask_canceled = df["order_status"].isin(canceled_status)
    orders_canceled = df[mask_canceled].copy()
    df = df[~mask_canceled].copy()
    log(f"  Removidos {mask_canceled.sum():,} pedidos cancelados/unavailable → tabela separada")

    # Imputar order_approved_at nulo
    # Estratégia: purchase + mediana do tempo de aprovação (timedelta)
    df["_approval_delta"] = df["order_approved_at"] - df["order_purchase_timestamp"]
    median_approval = df["_approval_delta"].median()
    mask_null_approved = df["order_approved_at"].isna()
    df.loc[mask_null_approved, "order_approved_at"] = (
        df.loc[mask_null_approved, "order_purchase_timestamp"] + median_approval
    )
    log(f"  Imputados {mask_null_approved.sum():,} nulos em order_approved_at "
        f"(mediana = {median_approval})")
    df.drop(columns=["_approval_delta"], inplace=True)

    # Remover anomalias de data de entrega
    # Entregues > 90 dias após estimativa → erro de sistema
    mask_anomaly = (
        df["order_delivered_customer_date"].notna() &
        df["order_estimated_delivery_date"].notna() &
        (
            (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"])
            > pd.Timedelta(days=90)
        )
    )
    n_anomaly = mask_anomaly.sum()
    df = df[~mask_anomaly].copy()
    log(f"  Removidos {n_anomaly:,} registros com anomalia de data de entrega (>90d após estimativa)")

    # Remover pedidos sem purchase_timestamp (impossível analisar)
    n_no_date = df["order_purchase_timestamp"].isna().sum()
    df = df[df["order_purchase_timestamp"].notna()].copy()
    log(f"  Removidos {n_no_date:,} pedidos sem order_purchase_timestamp")

    log(f"  ORDERS: {n0:,} → {len(df):,} registros (clean) + {len(orders_canceled):,} cancelados")
    return df, orders_canceled


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    log("ORDER_ITEMS — iniciando limpeza")
    n0 = len(df)

    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")

    # Remover preços inválidos
    mask_price = df["price"] <= 0
    df = df[~mask_price].copy()
    log(f"  Removidos {mask_price.sum():,} itens com price <= 0")

    # Remover frete negativo
    mask_freight = df["freight_value"] < 0
    df = df[~mask_freight].copy()
    log(f"  Removidos {mask_freight.sum():,} itens com freight_value < 0")

    # Coluna derivada
    df["revenue"] = df["price"] + df["freight_value"]
    log("  Criada coluna derivada: revenue = price + freight_value")

    log(f"  ORDER_ITEMS: {n0:,} → {len(df):,} registros")
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    log("PAYMENTS — iniciando limpeza")
    n0 = len(df)

    # Remover pagamentos sem valor real
    mask_zero = df["payment_value"] <= 0
    df = df[~mask_zero].copy()
    log(f"  Removidos {mask_zero.sum():,} registros com payment_value <= 0")

    # Normalizar payment_type
    df["payment_type"] = df["payment_type"].str.lower().str.strip()
    log("  Normalizado payment_type: lower + strip")

    # Remover payment_installments = 0 com tipo crédito (inconsistência)
    mask_installments = (
        (df["payment_type"] == "credit_card") & (df["payment_installments"] == 0)
    )
    df = df[~mask_installments].copy()
    log(f"  Removidos {mask_installments.sum():,} pagamentos crédito com installments=0")

    log(f"  PAYMENTS: {n0:,} → {len(df):,} registros")
    return df


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    log("REVIEWS — iniciando limpeza")
    n0 = len(df)

    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    # Remover review_score fora de [1, 5]
    mask_score = ~df["review_score"].between(1, 5)
    df = df[~mask_score].copy()
    log(f"  Removidos {mask_score.sum():,} reviews com score fora do intervalo [1,5]")

    # Deduplicar review_id: manter a avaliação mais recente
    before_dedup = len(df)
    df = (
        df.sort_values("review_answer_timestamp", ascending=False, na_position="last")
        .drop_duplicates(subset=["review_id"])
        .reset_index(drop=True)
    )
    log(f"  Removidas {before_dedup - len(df):,} duplicatas de review_id (mantida a mais recente)")

    log(f"  REVIEWS: {n0:,} → {len(df):,} registros")
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    log("PRODUCTS — iniciando limpeza")
    n0 = len(df)

    # Imputar category name
    null_cat = df["product_category_name"].isna().sum()
    df["product_category_name"] = df["product_category_name"].fillna("sem_categoria")
    log(f"  Imputados {null_cat:,} nulos em product_category_name com 'sem_categoria'")

    # Imputar dimensões com mediana da categoria
    dim_cols = [
        "product_weight_g", "product_length_cm",
        "product_height_cm", "product_width_cm",
    ]
    for col in dim_cols:
        nulls = df[col].isna().sum()
        if nulls > 0:
            medians = df.groupby("product_category_name")[col].transform("median")
            df[col] = df[col].fillna(medians)
            # Fallback global se a categoria inteira for nula
            df[col] = df[col].fillna(df[col].median())
            log(f"  Imputados {nulls:,} nulos em {col} (mediana por categoria)")

    # Remover produtos sem nenhum atributo físico
    mask_all_null = df[dim_cols].isna().all(axis=1)
    df = df[~mask_all_null].copy()
    log(f"  Removidos {mask_all_null.sum():,} produtos sem nenhum atributo físico")

    log(f"  PRODUCTS: {n0:,} → {len(df):,} registros")
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    log("CUSTOMERS — iniciando limpeza")

    df["customer_state"] = df["customer_state"].str.upper().str.strip()
    df["customer_zip_code_prefix"] = (
        df["customer_zip_code_prefix"].astype(str).str.zfill(5)
    )
    log("  Normalizado customer_state (upper) e zip_code (5 dígitos com zero-padding)")
    return df


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    log("SELLERS — iniciando limpeza")

    df["seller_state"] = df["seller_state"].str.upper().str.strip()
    df["seller_zip_code_prefix"] = (
        df["seller_zip_code_prefix"].astype(str).str.zfill(5)
    )
    log("  Normalizado seller_state (upper) e zip_code (5 dígitos com zero-padding)")
    return df


def clean_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    log("GEOLOCATION — iniciando limpeza")
    n0 = len(df)

    # Remover duplicatas exatas
    before = len(df)
    df = df.drop_duplicates(
        subset=["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"]
    )
    log(f"  Removidas {before - len(df):,} duplicatas exatas de (zip, lat, lng)")

    # Filtrar coordenadas fora do bbox do Brasil
    BRAZIL_LAT = (-33.75, 5.27)
    BRAZIL_LNG = (-73.99, -32.39)
    mask_bbox = (
        df["geolocation_lat"].between(*BRAZIL_LAT) &
        df["geolocation_lng"].between(*BRAZIL_LNG)
    )
    n_out = (~mask_bbox).sum()
    df = df[mask_bbox].reset_index(drop=True)
    log(f"  Removidas {n_out:,} coordenadas fora do bbox do Brasil")

    log(f"  GEOLOCATION: {n0:,} → {len(df):,} registros")
    return df


def clean_category_translation(df: pd.DataFrame) -> pd.DataFrame:
    log("CATEGORY_TRANSLATION — iniciando limpeza")
    df["product_category_name"] = df["product_category_name"].str.strip().str.lower()
    df["product_category_name_english"] = (
        df["product_category_name_english"].str.strip().str.lower()
    )
    log("  Normalizado: lower + strip em ambas as colunas")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(raw_dir: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    def load(filename: str, date_cols: list = None) -> pd.DataFrame:
        path = os.path.join(raw_dir, filename)
        if not os.path.exists(path):
            log(f"Arquivo não encontrado: {path}", "WARN")
            return None
        df = pd.read_csv(path, low_memory=False)
        if date_cols:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    def save(df: pd.DataFrame, name: str):
        path = os.path.join(out_dir, f"{name}_clean.csv")
        df.to_csv(path, index=False)
        log(f"  Salvo: {path}")

    # --- Orders ---
    df = load("olist_orders_dataset.csv")
    if df is not None:
        orders_clean, orders_canceled = clean_orders(df)
        save(orders_clean, "orders")
        save(orders_canceled, "orders_canceled")

    # --- Order Items ---
    df = load("olist_order_items_dataset.csv")
    if df is not None:
        save(clean_order_items(df), "order_items")

    # --- Payments ---
    df = load("olist_order_payments_dataset.csv")
    if df is not None:
        save(clean_payments(df), "payments")

    # --- Reviews ---
    df = load("olist_order_reviews_dataset.csv")
    if df is not None:
        save(clean_reviews(df), "reviews")

    # --- Products ---
    df = load("olist_products_dataset.csv")
    if df is not None:
        save(clean_products(df), "products")

    # --- Customers ---
    df = load("olist_customers_dataset.csv")
    if df is not None:
        save(clean_customers(df), "customers")

    # --- Sellers ---
    df = load("olist_sellers_dataset.csv")
    if df is not None:
        save(clean_sellers(df), "sellers")

    # --- Geolocation ---
    df = load("olist_geolocation_dataset.csv")
    if df is not None:
        save(clean_geolocation(df), "geolocation")

    # --- Category Translation ---
    df = load("product_category_name_translation.csv")
    if df is not None:
        save(clean_category_translation(df), "category_translation")

    save_log(out_dir)
    log("✓ Limpeza concluída.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpeza dos dados brutos Olist.")
    parser.add_argument("--raw_dir", default="./Data/raw")
    parser.add_argument("--out_dir", default="./Data/processed")
    args = parser.parse_args()
    main(args.raw_dir, args.out_dir)
