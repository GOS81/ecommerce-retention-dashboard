"""
Olist E-Commerce ETL Pipeline
=============================
Підготовка даних з Kaggle Olist Dataset для Power BI дашборду.

Датасет: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Завантаж архів, розпакуй у папку ./data/

Запуск:
    pip install pandas numpy
    python olist_etl.py

Результат: 4 CSV-файли в папці ./output/ для імпорту в Power BI.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ── Конфігурація ──────────────────────────────────────────────

DATA_DIR = Path("./data")
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 1. Завантаження даних ─────────────────────────────────────

print("📦 Завантаження CSV файлів...")

orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv",
                     parse_dates=["order_purchase_timestamp",
                                  "order_approved_at",
                                  "order_delivered_customer_date",
                                  "order_estimated_delivery_date"])

items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
products = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
reviews = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv",
                      parse_dates=["review_creation_date"])
sellers = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
category_translation = pd.read_csv(
    DATA_DIR / "product_category_name_translation.csv"
)

print(f"   Orders: {len(orders):,} rows")
print(f"   Items:  {len(items):,} rows")
print(f"   Products: {len(products):,} rows")

# ── 2. Очищення та зʼєднання ──────────────────────────────────

print("🔧 Очищення та обʼєднання таблиць...")

# Фільтруємо тільки доставлені замовлення
orders_clean = orders[orders["order_status"] == "delivered"].copy()

# Переклад категорій на англійську
products = products.merge(category_translation, on="product_category_name",
                          how="left")
products["category"] = products["product_category_name_english"].fillna(
    "other"
)

# Агрегуємо платежі по замовленнях
payments_agg = (payments
                .groupby("order_id")
                .agg(total_payment=("payment_value", "sum"),
                     payment_installments=("payment_installments", "max"),
                     payment_type=("payment_type", "first"))
                .reset_index())

# Агрегуємо товари по замовленнях
items_agg = (items
             .merge(products[["product_id", "category"]], on="product_id",
                    how="left")
             .groupby("order_id")
             .agg(total_items=("order_item_id", "max"),
                  total_price=("price", "sum"),
                  total_freight=("freight_value", "sum"),
                  main_category=("category", lambda x: x.mode().iloc[0]
                                 if len(x.mode()) > 0 else "other"))
             .reset_index())

# Середній review score
reviews_agg = (reviews
               .groupby("order_id")
               .agg(review_score=("review_score", "mean"))
               .reset_index())

# ── 3. Фактова таблиця (fact_orders) ──────────────────────────

print("📊 Створення фактової таблиці...")

fact = (orders_clean
        .merge(customers, on="customer_id", how="left")
        .merge(items_agg, on="order_id", how="left")
        .merge(payments_agg, on="order_id", how="left")
        .merge(reviews_agg, on="order_id", how="left"))

# Розрахунок часу доставки (днів)
fact["delivery_days"] = (
    (fact["order_delivered_customer_date"] -
     fact["order_purchase_timestamp"]).dt.total_seconds() / 86400
).round(1)

# Чи вчасно доставлено
fact["on_time"] = (
    fact["order_delivered_customer_date"] <=
    fact["order_estimated_delivery_date"]
).astype(int)

# Дата-поля для Power BI
fact["order_date"] = fact["order_purchase_timestamp"].dt.date
fact["order_month"] = fact["order_purchase_timestamp"].dt.to_period("M").astype(str)
fact["order_year"] = fact["order_purchase_timestamp"].dt.year
fact["order_dow"] = fact["order_purchase_timestamp"].dt.day_name()

# Числовий порядок днів тижня (для сортування в Power BI)
dow_map = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4,
           "Friday": 5, "Saturday": 6, "Sunday": 7}
fact["dow_sort"] = fact["order_dow"].map(dow_map)

# Revenue = price + freight
fact["revenue"] = fact["total_price"].fillna(0) + fact["total_freight"].fillna(0)

# Фінальні колонки
fact_cols = [
    "order_id", "customer_unique_id", "order_date", "order_month",
    "order_year", "order_dow", "dow_sort", "main_category", "total_items",
    "total_price", "total_freight", "revenue", "total_payment",
    "payment_type", "payment_installments", "review_score",
    "delivery_days", "on_time",
    "customer_city", "customer_state"
]

fact_orders = fact[fact_cols].copy()

print(f"   fact_orders: {len(fact_orders):,} rows, {len(fact_cols)} columns")

# ── 4. Когортна таблиця (cohort_data) ─────────────────────────

print("📈 Побудова когортної таблиці...")

# Перша покупка кожного клієнта
customer_first = (fact
                  .groupby("customer_unique_id")["order_purchase_timestamp"]
                  .min()
                  .reset_index()
                  .rename(columns={"order_purchase_timestamp":
                                   "first_purchase"}))

customer_first["cohort_month"] = (
    customer_first["first_purchase"].dt.to_period("M").astype(str)
)

# Зʼєднуємо з фактами
cohort_base = fact.merge(customer_first, on="customer_unique_id", how="left")

cohort_base["order_period"] = (
    cohort_base["order_purchase_timestamp"].dt.to_period("M")
)
cohort_base["first_period"] = (
    cohort_base["first_purchase"].dt.to_period("M")
)
cohort_base["period_number"] = (
    (cohort_base["order_period"] - cohort_base["first_period"])
    .apply(lambda x: x.n if pd.notna(x) else None)
)

# Когортна матриця
cohort_matrix = (cohort_base
                 .groupby(["cohort_month", "period_number"])
                 ["customer_unique_id"]
                 .nunique()
                 .reset_index()
                 .rename(columns={"customer_unique_id": "customers"}))

# Розмір когорти (period 0)
cohort_sizes = (cohort_matrix[cohort_matrix["period_number"] == 0]
                [["cohort_month", "customers"]]
                .rename(columns={"customers": "cohort_size"}))

cohort_data = cohort_matrix.merge(cohort_sizes, on="cohort_month", how="left")
cohort_data["retention_rate"] = (
    (cohort_data["customers"] / cohort_data["cohort_size"] * 100).round(2)
)

print(f"   cohort_data: {len(cohort_data):,} rows")

# ── 5. RFM-сегментація (rfm_data) ─────────────────────────────

print("🎯 Обчислення RFM-сегментів...")

snapshot_date = fact["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

rfm = (fact
       .groupby("customer_unique_id")
       .agg(
           recency=("order_purchase_timestamp",
                    lambda x: (snapshot_date - x.max()).days),
           frequency=("order_id", "nunique"),
           monetary=("revenue", "sum")
       )
       .reset_index())

# Квантильний скоринг (1-5)
rfm["r_score"] = pd.qcut(rfm["recency"], q=5,
                          labels=[5, 4, 3, 2, 1]).astype(int)
rfm["f_score"] = pd.cut(rfm["frequency"],
                         bins=[0, 1, 2, 3, 5, rfm["frequency"].max()],
                         labels=[1, 2, 3, 4, 5],
                         include_lowest=True).astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary"], q=5,
                          labels=[1, 2, 3, 4, 5]).astype(int)

rfm["rfm_score"] = rfm["r_score"] * 100 + rfm["f_score"] * 10 + rfm["m_score"]

# Сегменти
def assign_segment(row):
    r, f = row["r_score"], row["f_score"]
    if r >= 4 and f >= 4:
        return "Champions"
    elif r >= 3 and f >= 3:
        return "Loyal"
    elif r >= 4 and f <= 2:
        return "New Customers"
    elif r >= 3 and f <= 2:
        return "Promising"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f >= 4:
        return "Cant Lose"
    elif r <= 2 and f <= 2:
        return "Lost"
    else:
        return "Need Attention"

rfm["segment"] = rfm.apply(assign_segment, axis=1)

# Додаємо дані клієнта (місто, штат)
customer_geo = (fact
                .groupby("customer_unique_id")
                .agg(customer_city=("customer_city", "first"),
                     customer_state=("customer_state", "first"))
                .reset_index())

rfm_data = rfm.merge(customer_geo, on="customer_unique_id", how="left")

print(f"   rfm_data: {len(rfm_data):,} rows")
print(f"   Segments: {rfm_data['segment'].value_counts().to_dict()}")

# ── 6. Таблиця дат (dim_date) ─────────────────────────────────

print("📅 Генерація таблиці дат...")

date_range = pd.date_range(
    start=fact["order_purchase_timestamp"].min().normalize(),
    end=fact["order_purchase_timestamp"].max().normalize(),
    freq="D"
)

dim_date = pd.DataFrame({"date": date_range})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%B")
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["quarter_label"] = "Q" + dim_date["quarter"].astype(str)
dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
dim_date["day_of_week"] = dim_date["date"].dt.day_name()
dim_date["is_weekend"] = dim_date["date"].dt.dayofweek.isin([5, 6]).astype(int)
dim_date["week_number"] = dim_date["date"].dt.isocalendar().week.astype(int)

print(f"   dim_date: {len(dim_date):,} rows")

# ── 7. Збереження ─────────────────────────────────────────────

print("\n💾 Збереження файлів...")

fact_orders.to_csv(OUTPUT_DIR / "fact_orders.csv", index=False)
cohort_data.to_csv(OUTPUT_DIR / "cohort_data.csv", index=False)
rfm_data.to_csv(OUTPUT_DIR / "rfm_data.csv", index=False)
dim_date.to_csv(OUTPUT_DIR / "dim_date.csv", index=False)

print(f"""
✅ Готово! Файли збережено в {OUTPUT_DIR}/

   fact_orders.csv   — {len(fact_orders):,} рядків (фактова таблиця замовлень)
   cohort_data.csv   — {len(cohort_data):,} рядків (когортна матриця)
   rfm_data.csv      — {len(rfm_data):,} рядків (RFM-сегментація)
   dim_date.csv      — {len(dim_date):,} рядків (таблиця дат)

🔜 Наступний крок: імпортуй CSV у Power BI Desktop → побудуй модель даних.
""")
