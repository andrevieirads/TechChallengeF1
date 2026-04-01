"""
03_build_master.py
==================
Constrói o dataset analítico mestre (master analytical table) integrando
todas as tabelas limpas do Olist em uma visão unificada de pedidos.

Modelo de dados resultante (granularidade: order_item):
───────────────────────────────────────────────────────
Cada linha representa um item de pedido enriquecido com:
  - Dados do pedido (status, datas, tempo de entrega)
  - Dados do cliente (estado, região)
  - Dados do produto (categoria PT + EN, peso, dimensões)
  - Dados do vendedor (estado, região)
  - Dados de pagamento (método, parcelas, valor total do pedido)
  - Score de avaliação do pedido
  - Flags derivadas (entrega no prazo, atraso em dias)

Colunas derivadas criadas:
  - delivery_days         : dias entre compra e entrega ao cliente
  - estimated_days        : dias entre compra e prazo estimado
  - delay_days            : delivery_days - estimated_days (positivo = atraso)
  - is_late               : booleano (delay_days > 0)
  - approval_hours        : horas entre compra e aprovação
  - year_month            : formato YYYY-MM para agregações temporais
  - customer_region       : macro-região do Brasil (Sul, Sudeste, etc.)
  - seller_region         : macro-região do vendedor
  - volume_cm3            : volume do produto (length × width × height)

Uso:
    python 03_build_master.py --processed_dir ./Data/processed

Saída:
    ./Data/processed/master_orders.csv
    ./Data/processed/master_orders.parquet  (recomendado para Power BI via Python)
"""

import os
import argparse
from datetime import datetime

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Mapeamento de estados para regiões do Brasil
# ---------------------------------------------------------------------------

REGION_MAP = {
    "AC": "Norte",    "AM": "Norte",    "AP": "Norte",
    "PA": "Norte",    "RO": "Norte",    "RR": "Norte",    "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste",  "MG": "Sudeste",  "RJ": "Sudeste",  "SP": "Sudeste",
    "PR": "Sul",      "RS": "Sul",      "SC": "Sul",
}


def map_region(state_series: pd.Series) -> pd.Series:
    return state_series.map(REGION_MAP).fillna("Desconhecido")


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------

def load_clean(processed_dir: str, name: str) -> pd.DataFrame | None:
    path = os.path.join(processed_dir, f"{name}_clean.csv")
    if not os.path.exists(path):
        print(f"[WARN] Não encontrado: {path}")
        return None
    return pd.read_csv(path, low_memory=False)


# ---------------------------------------------------------------------------
# Construção do master
# ---------------------------------------------------------------------------

def build_master(processed_dir: str) -> pd.DataFrame:
    print("[INFO] Carregando tabelas limpas...")

    orders      = load_clean(processed_dir, "orders")
    items       = load_clean(processed_dir, "order_items")
    customers   = load_clean(processed_dir, "customers")
    products    = load_clean(processed_dir, "products")
    sellers     = load_clean(processed_dir, "sellers")
    payments    = load_clean(processed_dir, "payments")
    reviews     = load_clean(processed_dir, "reviews")
    categories  = load_clean(processed_dir, "category_translation")

    # --- Parse datas em orders ---
    date_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")

    # -----------------------------------------------------------------------
    # 1. Agregar pagamentos por order_id
    #    (um pedido pode ter múltiplos métodos de pagamento)
    # -----------------------------------------------------------------------
    print("[INFO] Agregando pagamentos por pedido...")
    pay_agg = (
        payments
        .groupby("order_id")
        .agg(
            payment_methods=("payment_type", lambda x: "|".join(x.unique())),
            primary_payment=("payment_type", "first"),
            max_installments=("payment_installments", "max"),
            total_payment_value=("payment_value", "sum"),
        )
        .reset_index()
    )

    # -----------------------------------------------------------------------
    # 2. Agregar reviews por order_id (pegar score mais recente)
    # -----------------------------------------------------------------------
    print("[INFO] Agregando reviews por pedido...")
    reviews["review_creation_date"] = pd.to_datetime(
        reviews["review_creation_date"], errors="coerce"
    )
    rev_agg = (
        reviews
        .sort_values("review_creation_date", ascending=False)
        .groupby("order_id")
        .agg(review_score=("review_score", "first"))
        .reset_index()
    )

    # -----------------------------------------------------------------------
    # 3. Enriquecer produtos com tradução de categoria
    # -----------------------------------------------------------------------
    if categories is not None:
        products = products.merge(
            categories,
            on="product_category_name",
            how="left",
        )
        products["product_category_name_english"] = (
            products["product_category_name_english"].fillna(
                products["product_category_name"]
            )
        )
    else:
        products["product_category_name_english"] = products["product_category_name"]

    # Volume do produto
    if all(c in products.columns for c in ["product_length_cm", "product_width_cm", "product_height_cm"]):
        products["volume_cm3"] = (
            products["product_length_cm"] *
            products["product_width_cm"] *
            products["product_height_cm"]
        )

    # -----------------------------------------------------------------------
    # 4. JOIN principal
    # -----------------------------------------------------------------------
    print("[INFO] Construindo master table via JOINs...")

    master = (
        items
        .merge(orders,    on="order_id",    how="left")
        .merge(customers, on="customer_id", how="left")
        .merge(products,  on="product_id",  how="left")
        .merge(sellers,   on="seller_id",   how="left")
        .merge(pay_agg,   on="order_id",    how="left")
        .merge(rev_agg,   on="order_id",    how="left")
    )

    # -----------------------------------------------------------------------
    # 5. Colunas derivadas de tempo
    # -----------------------------------------------------------------------
    print("[INFO] Calculando colunas derivadas...")

    master["delivery_days"] = (
        (master["order_delivered_customer_date"] - master["order_purchase_timestamp"])
        .dt.total_seconds() / 86400
    ).round(1)

    master["estimated_days"] = (
        (master["order_estimated_delivery_date"] - master["order_purchase_timestamp"])
        .dt.total_seconds() / 86400
    ).round(1)

    master["delay_days"] = (master["delivery_days"] - master["estimated_days"]).round(1)
    master["is_late"] = master["delay_days"] > 0

    master["approval_hours"] = (
        (master["order_approved_at"] - master["order_purchase_timestamp"])
        .dt.total_seconds() / 3600
    ).round(2)

    master["year_month"] = (
        master["order_purchase_timestamp"].dt.to_period("M").astype(str)
    )
    master["year"] = master["order_purchase_timestamp"].dt.year
    master["month"] = master["order_purchase_timestamp"].dt.month
    master["weekday"] = master["order_purchase_timestamp"].dt.day_name()

    # -----------------------------------------------------------------------
    # 6. Regiões
    # -----------------------------------------------------------------------
    master["customer_region"] = map_region(master["customer_state"])
    master["seller_region"]   = map_region(master["seller_state"])

    # -----------------------------------------------------------------------
    # 7. Ticket médio por pedido (para agregações)
    # -----------------------------------------------------------------------
    # Mantemos revenue (price + freight) calculado no cleaning
    # Adicionamos price_segment para análise de faixa de preço
    bins   = [0, 50, 100, 250, 500, float("inf")]
    labels = ["< R$50", "R$50-100", "R$100-250", "R$250-500", "> R$500"]
    master["price_segment"] = pd.cut(
        master["price"], bins=bins, labels=labels, right=True
    ).astype(str)

    print(f"[OK] Master table construída: {len(master):,} linhas × {len(master.columns)} colunas")
    return master


# ---------------------------------------------------------------------------
# Relatório de integridade referencial
# ---------------------------------------------------------------------------

def check_referential_integrity(master: pd.DataFrame):
    print("\n[INFO] Verificando integridade referencial...")
    checks = {
        "customer_id nulo"      : master["customer_id"].isna().sum(),
        "product_id nulo"       : master["product_id"].isna().sum(),
        "seller_id nulo"        : master["seller_id"].isna().sum(),
        "sem pagamento"         : master["total_payment_value"].isna().sum(),
        "sem review"            : master["review_score"].isna().sum(),
        "category PT nula"      : master["product_category_name"].isna().sum(),
        "delivery_days negativo": (master["delivery_days"] < 0).sum(),
    }
    for check, count in checks.items():
        status = "✓" if count == 0 else "⚠"
        pct = round(count / len(master) * 100, 2)
        print(f"  {status}  {check:<30}: {count:>7,}  ({pct}%)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(processed_dir: str):
    master = build_master(processed_dir)
    check_referential_integrity(master)

    # Salvar CSV
    csv_path = os.path.join(processed_dir, "master_orders.csv")
    master.to_csv(csv_path, index=False)
    print(f"\n[OK] Salvo: {csv_path}")

    # Salvar Parquet (recomendado para uso com Power BI via Python connector)
    try:
        pq_path = os.path.join(processed_dir, "master_orders.parquet")
        master.to_parquet(pq_path, index=False)
        print(f"[OK] Salvo: {pq_path}")
    except ImportError:
        print("[WARN] pyarrow não instalado — parquet não gerado. Execute: pip install pyarrow")

    # Snapshot de colunas do master
    col_path = os.path.join(processed_dir, "master_columns.txt")
    with open(col_path, "w") as f:
        f.write("COLUNAS DO MASTER TABLE\n")
        f.write("=" * 50 + "\n")
        for col in master.columns:
            f.write(f"  {col:<45} {str(master[col].dtype)}\n")
    print(f"[OK] Dicionário de colunas: {col_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Constrói o master analítico do Olist.")
    parser.add_argument("--processed_dir", default="./Data/processed")
    args = parser.parse_args()
    main(args.processed_dir)
