"""
01_data_audit.py
================
Auditoria inicial dos dados brutos do dataset Brazilian E-Commerce (Olist).

Objetivo:
    Inspecionar cada tabela do dataset e documentar:
    - Dimensões (linhas × colunas)
    - Tipos de dados
    - Nulos por coluna
    - Duplicatas
    - Intervalos de datas
    - Distribuição de status de pedidos

Uso:
    python 01_data_audit.py --data_dir ./Data/raw

Saída:
    ./Data/audit/auditoria_inicial.txt  — relatório textual completo
    ./Data/audit/auditoria_inicial.csv  — resumo tabular por coluna
"""

import os
import argparse
import textwrap
from datetime import datetime

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Configuração dos arquivos esperados e seus tipos de dados nas colunas-chave
# ---------------------------------------------------------------------------

TABLES = {
    "customers": {
        "file": "olist_customers_dataset.csv",
        "pk": "customer_id",
        "date_cols": [],
    },
    "orders": {
        "file": "olist_orders_dataset.csv",
        "pk": "order_id",
        "date_cols": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    "order_items": {
        "file": "olist_order_items_dataset.csv",
        "pk": None,   # PK composta: order_id + order_item_id
        "date_cols": ["shipping_limit_date"],
    },
    "payments": {
        "file": "olist_order_payments_dataset.csv",
        "pk": None,
        "date_cols": [],
    },
    "reviews": {
        "file": "olist_order_reviews_dataset.csv",
        "pk": "review_id",
        "date_cols": ["review_creation_date", "review_answer_timestamp"],
    },
    "products": {
        "file": "olist_products_dataset.csv",
        "pk": "product_id",
        "date_cols": [],
    },
    "sellers": {
        "file": "olist_sellers_dataset.csv",
        "pk": "seller_id",
        "date_cols": [],
    },
    "geolocation": {
        "file": "olist_geolocation_dataset.csv",
        "pk": None,
        "date_cols": [],
    },
    "category_translation": {
        "file": "product_category_name_translation.csv",
        "pk": "product_category_name",
        "date_cols": [],
    },
}


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def load_table(path: str, date_cols: list) -> pd.DataFrame:
    """Carrega CSV convertendo colunas de data para datetime."""
    df = pd.read_csv(path, low_memory=False)
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def audit_table(name: str, df: pd.DataFrame, pk: str, date_cols: list) -> dict:
    """Executa auditoria completa de uma tabela e retorna dicionário com métricas."""
    report = {"table": name, "rows": len(df), "cols": len(df.columns)}

    # --- Chave primária ---
    if pk and pk in df.columns:
        dup_pk = df[pk].duplicated().sum()
        null_pk = df[pk].isna().sum()
        report["pk_duplicates"] = int(dup_pk)
        report["pk_nulls"] = int(null_pk)
    else:
        report["pk_duplicates"] = "N/A"
        report["pk_nulls"] = "N/A"

    # --- Duplicatas de linha inteira ---
    report["full_row_duplicates"] = int(df.duplicated().sum())

    # --- Nulos por coluna ---
    null_counts = df.isna().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    report["nulls_by_col"] = {
        col: {"count": int(null_counts[col]), "pct": float(null_pct[col])}
        for col in df.columns
        if null_counts[col] > 0
    }

    # --- Intervalos de datas ---
    date_ranges = {}
    for col in date_cols:
        if col in df.columns:
            valid = df[col].dropna()
            if len(valid):
                date_ranges[col] = {
                    "min": str(valid.min()),
                    "max": str(valid.max()),
                    "nulls": int(df[col].isna().sum()),
                }
    report["date_ranges"] = date_ranges

    # --- Colunas numéricas: stats básicos ---
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_stats = {}
    for col in num_cols:
        s = df[col].describe()
        num_stats[col] = {
            "min": round(float(s["min"]), 4),
            "max": round(float(s["max"]), 4),
            "mean": round(float(s["mean"]), 4),
            "std": round(float(s["std"]), 4),
        }
    report["numeric_stats"] = num_stats

    return report


def format_report(reports: list) -> str:
    """Formata lista de relatórios em texto legível."""
    lines = []
    sep = "=" * 70
    lines.append(sep)
    lines.append("AUDITORIA INICIAL — OLIST BRAZILIAN E-COMMERCE DATASET")
    lines.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(sep)

    for r in reports:
        lines.append(f"\n{'─' * 70}")
        lines.append(f"TABELA: {r['table'].upper()}")
        lines.append(f"{'─' * 70}")
        lines.append(f"  Linhas           : {r['rows']:,}")
        lines.append(f"  Colunas          : {r['cols']}")
        lines.append(f"  Duplicatas de PK : {r['pk_duplicates']}")
        lines.append(f"  Nulos na PK      : {r['pk_nulls']}")
        lines.append(f"  Linhas duplicadas: {r['full_row_duplicates']:,}")

        if r["nulls_by_col"]:
            lines.append("\n  NULOS POR COLUNA:")
            for col, info in r["nulls_by_col"].items():
                lines.append(f"    {col:<45} {info['count']:>7,}  ({info['pct']}%)")
        else:
            lines.append("\n  NULOS: nenhum encontrado ✓")

        if r["date_ranges"]:
            lines.append("\n  INTERVALOS DE DATAS:")
            for col, info in r["date_ranges"].items():
                lines.append(f"    {col}")
                lines.append(f"      min: {info['min']}  |  max: {info['max']}  |  nulos: {info['nulls']:,}")

        if r["numeric_stats"]:
            lines.append("\n  ESTATÍSTICAS NUMÉRICAS:")
            for col, s in r["numeric_stats"].items():
                lines.append(
                    f"    {col:<40}  min={s['min']:<10}  max={s['max']:<12}  "
                    f"mean={s['mean']:<12}  std={s['std']}"
                )

    lines.append(f"\n{'=' * 70}")
    lines.append("FIM DO RELATÓRIO")
    lines.append("=" * 70)
    return "\n".join(lines)


def to_summary_df(reports: list) -> pd.DataFrame:
    """Converte relatórios em DataFrame resumido para exportação CSV."""
    rows = []
    for r in reports:
        rows.append({
            "tabela": r["table"],
            "linhas": r["rows"],
            "colunas": r["cols"],
            "pk_duplicatas": r["pk_duplicates"],
            "pk_nulos": r["pk_nulls"],
            "linhas_duplicadas": r["full_row_duplicates"],
            "colunas_com_nulos": len(r["nulls_by_col"]),
            "total_nulos": sum(v["count"] for v in r["nulls_by_col"].values()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(data_dir: str):
    audit_dir = os.path.join(os.path.dirname(data_dir), "audit")
    os.makedirs(audit_dir, exist_ok=True)

    reports = []
    missing = []

    for name, meta in TABLES.items():
        path = os.path.join(data_dir, meta["file"])
        if not os.path.exists(path):
            print(f"[AVISO] Arquivo não encontrado: {path}")
            missing.append(name)
            continue

        print(f"[INFO] Auditando: {name}...")
        df = load_table(path, meta["date_cols"])
        report = audit_table(name, df, meta["pk"], meta["date_cols"])
        reports.append(report)

    if not reports:
        print("[ERRO] Nenhum arquivo encontrado. Verifique o caminho --data_dir.")
        return

    # Salvar relatório textual
    text = format_report(reports)
    report_path = os.path.join(audit_dir, "auditoria_inicial.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n[OK] Relatório salvo em: {report_path}")

    # Salvar CSV resumo
    summary_df = to_summary_df(reports)
    csv_path = os.path.join(audit_dir, "auditoria_inicial.csv")
    summary_df.to_csv(csv_path, index=False)
    print(f"[OK] Resumo CSV salvo em: {csv_path}")

    # Imprimir resumo no terminal
    print("\n" + "=" * 70)
    print("RESUMO RÁPIDO")
    print("=" * 70)
    print(summary_df.to_string(index=False))

    if missing:
        print(f"\n[AVISO] Tabelas ausentes: {missing}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoria inicial do dataset Olist.")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="./Data/raw",
        help="Caminho para a pasta com os CSVs brutos do Olist.",
    )
    args = parser.parse_args()
    main(args.data_dir)
