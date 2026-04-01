"""
04_eda_metrics.py
=================
Análise Exploratória de Dados (EDA) e métricas de negócio para o dashboard
Power BI do projeto TechChallengeF1 — Olist E-commerce.

Gera arquivos CSV prontos para importação no Power BI como:
  - Tabelas de métricas agregadas
  - Séries temporais
  - Rankings

Métricas calculadas:
───────────────────────────────────────────────────────────────
CRESCIMENTO
  - evolucao_mensal.csv          : pedidos, receita e ticket médio por mês
  - crescimento_anual.csv        : YoY de pedidos e receita

PRODUTOS
  - top_categorias_receita.csv   : top 20 categorias por receita total
  - top_categorias_volume.csv    : top 20 categorias por volume de pedidos

LOGÍSTICA
  - logistica_por_estado.csv     : tempo médio de entrega e atraso por UF
  - atraso_vs_review.csv         : correlação atraso × score de avaliação
  - entrega_ontime_rate.csv      : taxa de entrega no prazo por UF

PAGAMENTOS
  - meios_pagamento.csv          : distribuição de meios de pagamento
  - parcelamento.csv             : distribuição de parcelas (crédito)

SATISFAÇÃO
  - distribuicao_review.csv      : contagem por score
  - review_por_categoria.csv     : score médio por categoria
  - review_por_delivery_bucket.csv : score médio por faixa de prazo de entrega

SELLERS
  - top_sellers_receita.csv      : top 50 sellers por receita
  - seller_performance.csv       : receita, qtd, score e atraso médio por seller

CLIENTES
  - clientes_por_estado.csv      : concentração geográfica de clientes
  - receita_por_regiao.csv       : receita por macro-região

Uso:
    python 04_eda_metrics.py --master ./Data/processed/master_orders.csv --out ./Data/metrics

Saída:
    ./Data/metrics/*.csv
    ./Data/metrics/kpis_executivos.csv  (resumo executivo com 1 linha de KPIs)
"""

import os
import argparse
from datetime import datetime

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------

def load_master(path: str) -> pd.DataFrame:
    print(f"[INFO] Carregando master table: {path}")
    df = pd.read_csv(path, low_memory=False)

    date_cols = ["order_purchase_timestamp", "order_delivered_customer_date",
                 "order_estimated_delivery_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Garantir tipos booleanos
    if "is_late" in df.columns:
        df["is_late"] = df["is_late"].astype(bool)

    print(f"[OK] {len(df):,} linhas carregadas.")
    return df


# ---------------------------------------------------------------------------
# Crescimento
# ---------------------------------------------------------------------------

def calc_evolucao_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Pedidos, receita total e ticket médio por ano-mês."""
    # Usar granularidade de pedido (não de item) para contagem de pedidos
    orders_unique = df.drop_duplicates(subset=["order_id"])
    
    monthly = (
        orders_unique
        .groupby("year_month")
        .agg(
            total_pedidos=("order_id", "count"),
        )
        .reset_index()
    )

    # Receita no nível de item (soma de price de todos os itens)
    receita = (
        df.groupby("year_month")
        .agg(receita_total=("price", "sum"))
        .reset_index()
    )
    monthly = monthly.merge(receita, on="year_month")
    monthly["ticket_medio"] = (monthly["receita_total"] / monthly["total_pedidos"]).round(2)
    monthly["receita_total"] = monthly["receita_total"].round(2)

    # Crescimento MoM
    monthly = monthly.sort_values("year_month").reset_index(drop=True)
    monthly["mom_pedidos_pct"] = monthly["total_pedidos"].pct_change().mul(100).round(2)
    monthly["mom_receita_pct"] = monthly["receita_total"].pct_change().mul(100).round(2)

    return monthly


def calc_crescimento_anual(df: pd.DataFrame) -> pd.DataFrame:
    orders_unique = df.drop_duplicates(subset=["order_id"])
    annual = (
        orders_unique
        .groupby("year")
        .agg(total_pedidos=("order_id", "count"))
        .reset_index()
    )
    receita = df.groupby("year").agg(receita_total=("price", "sum")).reset_index()
    annual = annual.merge(receita, on="year")
    annual["receita_total"] = annual["receita_total"].round(2)
    annual["yoy_pedidos_pct"] = annual["total_pedidos"].pct_change().mul(100).round(2)
    annual["yoy_receita_pct"] = annual["receita_total"].pct_change().mul(100).round(2)
    return annual


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------

def calc_top_categorias(df: pd.DataFrame, top_n: int = 20) -> tuple:
    cat_col = "product_category_name_english" if "product_category_name_english" in df.columns \
              else "product_category_name"

    by_receita = (
        df.groupby(cat_col)
        .agg(receita_total=("price", "sum"), qtd_itens=("order_id", "count"))
        .reset_index()
        .sort_values("receita_total", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    by_receita["receita_total"] = by_receita["receita_total"].round(2)
    by_receita["rank"] = range(1, len(by_receita) + 1)

    by_volume = (
        df.groupby(cat_col)
        .agg(qtd_pedidos=("order_id", "count"), receita_total=("price", "sum"))
        .reset_index()
        .sort_values("qtd_pedidos", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    by_volume["receita_total"] = by_volume["receita_total"].round(2)
    by_volume["rank"] = range(1, len(by_volume) + 1)

    return by_receita, by_volume


# ---------------------------------------------------------------------------
# Logística
# ---------------------------------------------------------------------------

def calc_logistica_estado(df: pd.DataFrame) -> pd.DataFrame:
    delivered = df[df["delivery_days"].notna() & df["delivery_days"] > 0]
    log_df = (
        delivered
        .groupby("customer_state")
        .agg(
            media_dias_entrega=("delivery_days", "mean"),
            media_dias_estimado=("estimated_days", "mean"),
            media_atraso_dias=("delay_days", "mean"),
            pct_atraso=("is_late", "mean"),
            total_pedidos=("order_id", "count"),
        )
        .reset_index()
    )
    for col in ["media_dias_entrega", "media_dias_estimado", "media_atraso_dias"]:
        log_df[col] = log_df[col].round(1)
    log_df["pct_atraso"] = (log_df["pct_atraso"] * 100).round(2)
    log_df["regiao"] = log_df["customer_state"].map({
        "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
        "RO": "Norte", "RR": "Norte", "TO": "Norte",
        "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
        "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
        "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
        "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
        "PR": "Sul", "RS": "Sul", "SC": "Sul",
    }).fillna("Desconhecido")
    return log_df.sort_values("media_dias_entrega", ascending=False)


def calc_atraso_vs_review(df: pd.DataFrame) -> pd.DataFrame:
    """Score médio de review por faixa de atraso em dias."""
    delivered = df[df["delay_days"].notna() & df["review_score"].notna()].copy()
    bins = [-float("inf"), -7, 0, 7, 14, 30, float("inf")]
    labels = ["Muito adiantado (>7d)", "No prazo (0-7d)", "Leve atraso (1-7d)",
              "Atraso moderado (8-14d)", "Atraso alto (15-30d)", "Atraso crítico (>30d)"]
    delivered["delay_bucket"] = pd.cut(delivered["delay_days"], bins=bins, labels=labels)
    result = (
        delivered.groupby("delay_bucket", observed=True)
        .agg(
            media_review=("review_score", "mean"),
            total_pedidos=("order_id", "count"),
        )
        .reset_index()
    )
    result["media_review"] = result["media_review"].round(3)
    return result


# ---------------------------------------------------------------------------
# Pagamentos
# ---------------------------------------------------------------------------

def calc_meios_pagamento(df: pd.DataFrame) -> pd.DataFrame:
    payments = df.drop_duplicates(subset=["order_id"])[["order_id", "primary_payment"]].copy()
    result = (
        payments.groupby("primary_payment")
        .agg(qtd_pedidos=("order_id", "count"))
        .reset_index()
        .sort_values("qtd_pedidos", ascending=False)
    )
    result["pct"] = (result["qtd_pedidos"] / result["qtd_pedidos"].sum() * 100).round(2)
    return result


def calc_parcelamento(df: pd.DataFrame) -> pd.DataFrame:
    credito = df[df["primary_payment"] == "credit_card"].drop_duplicates(subset=["order_id"])
    result = (
        credito.groupby("max_installments")
        .agg(qtd_pedidos=("order_id", "count"))
        .reset_index()
        .sort_values("max_installments")
    )
    result["pct"] = (result["qtd_pedidos"] / result["qtd_pedidos"].sum() * 100).round(2)
    return result


# ---------------------------------------------------------------------------
# Satisfação
# ---------------------------------------------------------------------------

def calc_distribuicao_review(df: pd.DataFrame) -> pd.DataFrame:
    orders_rev = df.drop_duplicates(subset=["order_id"])
    result = (
        orders_rev.groupby("review_score")
        .agg(qtd=("order_id", "count"))
        .reset_index()
        .sort_values("review_score")
    )
    result["pct"] = (result["qtd"] / result["qtd"].sum() * 100).round(2)
    return result


def calc_review_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    cat_col = "product_category_name_english" if "product_category_name_english" in df.columns \
              else "product_category_name"
    result = (
        df[df["review_score"].notna()]
        .groupby(cat_col)
        .agg(
            media_review=("review_score", "mean"),
            qtd_avaliacoes=("review_score", "count"),
        )
        .reset_index()
        .query("qtd_avaliacoes >= 30")   # mínimo de avaliações para relevância estatística
        .sort_values("media_review", ascending=False)
    )
    result["media_review"] = result["media_review"].round(3)
    return result


# ---------------------------------------------------------------------------
# Sellers
# ---------------------------------------------------------------------------

def calc_seller_performance(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    result = (
        df.groupby("seller_id")
        .agg(
            receita_total=("price", "sum"),
            qtd_pedidos=("order_id", "nunique"),
            ticket_medio=("price", "mean"),
            media_review=("review_score", "mean"),
            media_atraso=("delay_days", "mean"),
            pct_atraso=("is_late", "mean"),
            seller_state=("seller_state", "first"),
            seller_region=("seller_region", "first"),
        )
        .reset_index()
        .sort_values("receita_total", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    result["receita_total"] = result["receita_total"].round(2)
    result["ticket_medio"] = result["ticket_medio"].round(2)
    result["media_review"] = result["media_review"].round(3)
    result["media_atraso"] = result["media_atraso"].round(1)
    result["pct_atraso"] = (result["pct_atraso"] * 100).round(2)
    result["rank"] = range(1, len(result) + 1)
    return result


# ---------------------------------------------------------------------------
# KPIs executivos
# ---------------------------------------------------------------------------

def calc_kpis_executivos(df: pd.DataFrame) -> pd.DataFrame:
    orders_u = df.drop_duplicates(subset=["order_id"])
    delivered = df[df["delivery_days"].notna() & (df["delivery_days"] > 0)]

    kpis = {
        "total_pedidos": len(orders_u),
        "total_receita_R$": round(df["price"].sum(), 2),
        "ticket_medio_R$": round(df["price"].sum() / len(orders_u), 2),
        "receita_frete_R$": round(df["freight_value"].sum(), 2) if "freight_value" in df.columns else None,
        "media_dias_entrega": round(delivered["delivery_days"].mean(), 1),
        "pct_entregas_no_prazo": round((~orders_u["is_late"].fillna(False)).mean() * 100, 2),
        "media_review_score": round(df["review_score"].mean(), 3),
        "total_sellers_ativos": df["seller_id"].nunique(),
        "total_clientes_unicos": df["customer_id"].nunique(),
        "total_categorias": df["product_category_name"].nunique(),
        "periodo_inicio": str(df["order_purchase_timestamp"].min().date()),
        "periodo_fim": str(df["order_purchase_timestamp"].max().date()),
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return pd.DataFrame([kpis])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(master_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    df = load_master(master_path)

    def save(result: pd.DataFrame, name: str):
        path = os.path.join(out_dir, f"{name}.csv")
        result.to_csv(path, index=False)
        print(f"  [OK] {name}.csv  ({len(result):,} linhas)")

    print("\n[INFO] Calculando métricas de CRESCIMENTO...")
    save(calc_evolucao_mensal(df), "evolucao_mensal")
    save(calc_crescimento_anual(df), "crescimento_anual")

    print("\n[INFO] Calculando métricas de PRODUTOS...")
    top_receita, top_volume = calc_top_categorias(df)
    save(top_receita, "top_categorias_receita")
    save(top_volume, "top_categorias_volume")

    print("\n[INFO] Calculando métricas de LOGÍSTICA...")
    save(calc_logistica_estado(df), "logistica_por_estado")
    save(calc_atraso_vs_review(df), "atraso_vs_review")

    print("\n[INFO] Calculando métricas de PAGAMENTOS...")
    save(calc_meios_pagamento(df), "meios_pagamento")
    save(calc_parcelamento(df), "parcelamento")

    print("\n[INFO] Calculando métricas de SATISFAÇÃO...")
    save(calc_distribuicao_review(df), "distribuicao_review")
    save(calc_review_por_categoria(df), "review_por_categoria")

    print("\n[INFO] Calculando métricas de SELLERS...")
    save(calc_seller_performance(df), "seller_performance")

    print("\n[INFO] Calculando KPIs EXECUTIVOS...")
    kpis = calc_kpis_executivos(df)
    save(kpis, "kpis_executivos")

    # Imprimir KPIs no terminal
    print("\n" + "=" * 60)
    print("KPIs EXECUTIVOS")
    print("=" * 60)
    for col in kpis.columns:
        print(f"  {col:<35}: {kpis[col].values[0]}")

    print(f"\n[✓] Todas as métricas salvas em: {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EDA e métricas de negócio — Olist.")
    parser.add_argument("--master", default="./Data/processed/master_orders.csv")
    parser.add_argument("--out", default="./Data/metrics")
    args = parser.parse_args()
    main(args.master, args.out)
