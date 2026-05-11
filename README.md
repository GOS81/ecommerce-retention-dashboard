# 📊 E-Commerce Customer Retention Dashboard

🇺🇦 [Українська версія](README_UKR.md)

Interactive Power BI dashboard analyzing customer retention, cohort behavior, and RFM segmentation using real Brazilian e-commerce data (Olist, 100K+ orders, 2016–2018).

---

## 🖼️ Demo

![Executive Overview](screenshots/page1_overview.png)
![Cohort & Retention](screenshots/page2_cohorts.png)
![RFM Segmentation](screenshots/page3_rfm.png)
![Customer Journey](screenshots/page4_journey.png)

---

## ✨ Features

- **Executive Overview** — 6 KPI cards (Revenue, AOV, Orders, Customers, Review Score, On-Time Delivery), revenue trend with rolling average, top 10 categories, orders by day of week, interactive year/quarter slicers.
- **Cohort & Retention** — cohort retention heatmap with conditional formatting, retention curves by cohort, new vs returning customers dynamics, key churn metrics (Churn Rate, Repeat Rate).
- **RFM Segmentation** — customer segmentation using Recency-Frequency-Monetary model (Champions, Loyal, At Risk, Lost, etc.), scatter chart, segment summary table, revenue distribution.
- **Customer Journey** — purchase funnel (1st → 2nd → 3rd purchase), payment type analysis, installment distribution, review score histogram with conditional formatting.

---

## 🛠️ Tech Stack

|      Layer      |      Technology         |
|-----------------|-------------------------|
| ETL             | Python 3, Pandas, NumPy |
| Visualization   | Power BI Desktop        |
| Data Modeling   | Star Schema, DAX        |
| Version Control | Git, GitHub             |

---

## 🏗️ How It Works

Raw data (8 CSV files from Kaggle) is processed by the `olist_etl.py` Python script, which handles cleaning, table joins, cohort calculation, and RFM segmentation. The output is 4 analysis-ready CSV tables in a star schema format (fact_orders, cohort_data, rfm_data, dim_date). These are imported into Power BI, where the data model, 25+ DAX measures, and 4 interactive dashboard pages are built.

---

## 🚀 Installation

### Prerequisites
- [Python 3.10+](https://www.python.org/downloads/)
- [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (free version)

### Step 1 — Clone the repository

```bash
git clone https://github.com/GOS81/ecommerce-retention-dashboard.git
cd ecommerce-retention-dashboard
pip install pandas numpy
```

### Step 2 — Download data

Download the [Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle and unzip all CSVs into the `./data/` folder.
OR use ready-made data from the `./output/` folder.

### Step 3 — Run ETL

```bash
python olist_etl.py
```

4 prepared CSV files will appear in the `./output/` folder.

### Step 4 — Open dashboard

Open `dashboard/olist-customer-retention-analysis.pbix` in Power BI Desktop.

If building from scratch — import CSVs from `./output/`, add measures from `dax_measures.dax`, and create the `Funnel_Steps` table (details in the measures file).

---

## 📖 Usage

The dashboard has 4 pages with navigation buttons in the header:

- **Overview** — business snapshot. Use year and quarter slicers to filter.
- **Cohorts** — click a row in the heatmap to see details of a specific cohort.
- **RFM** — click a segment in the donut chart — all visuals cross-filter automatically.
- **Journey** — the funnel shows drop-off between purchases; histograms detail payment behavior.

---

## 📁 Project Structure

```
olist-customer-retention-analysis/
├── olist_etl.py          # Python ETL script
├── dax_measures.dax      # DAX measures with comments
├── README.md             # Documentation (English)
├── README_UKR.md         # Documentation (Ukrainian)
├── data/                 # Raw Kaggle CSVs
├── output/               # Prepared CSVs for Power BI
├── dashboard/            # Power BI file (.pbix)
└── screenshots/          # Dashboard page screenshots
```

---

## 👤 Author

**Oleksandr Golubchyk** — Data Analyst

- LinkedIn: [linkedin.com/in/oleksandrgolubchyk](https://www.linkedin.com/in/oleksandrgolubchyk/)
- GitHub: [github.com/GOS81](https://github.com/GOS81)
- Email: a_golubchyk@ukr.net
