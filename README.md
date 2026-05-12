# Veridi Logistics : Last Mile Delivery Performance Audit

> **Data Engineering Program Submission**
> Dataset: Olist Brazilian E-Commerce (Kaggle) | Tool: Python, Streamlit, Plotly

---

## A. Executive Summary

Analysis of **96,470 delivered orders** from the Olist Brazilian e-commerce platform reveals that **6.8% of deliveries arrive late**, with Super Late orders (>5 days) generating an average review score of just **2.27/5** compared to **4.29/5** for on-time deliveries; a 47% collapse in customer satisfaction directly caused by logistics failure. The problem is **not nationwide**: northern and northeastern states (AL, AM, RR, AP) suffer 3-5× higher late rates than São Paulo, pointing to last-mile infrastructure gaps far from the main distribution hub. A custom **"Revenue at Risk"** analysis estimates **R$ 1,150,866** in direct financial exposure from late orders, giving leadership a concrete business case, not just an NPS argument, for logistics investment.

---

## B. Project Links

| Deliverable | Link |
|---|---|
| Notebook (Google Colab) | https://colab.research.google.com/drive/12_q-9lkmRBPh0GOeqSJIzjZO5g8Kd3W9#scrollTo=fPVDYpmpFXWd |
| Dashboard (Streamlit) | https://veridi-logistics-audit-6acrnmx6nggheseydzy9h7.streamlit.app/ |
| Presentation (Canva Slides) | https://canva.link/ijhld6d1io6w1zn |
| Video Walkthrough (YouTube) | https://youtu.be/QAj2qv-lpBA |

---

## C. Technical Explanation

### Data Cleaning
- **Date parsing:** All 5 timestamp columns converted from string to `datetime64` using `pd.to_datetime()`.
- **Duplicate reviews:** 547 orders had multiple reviews (up to 3). Deduplicated by keeping the most recent `review_answer_timestamp` per `order_id` — the most representative signal of final customer sentiment.
- **Undelivered orders excluded:** Orders with `order_status` of `canceled` or `unavailable`, and any delivered orders with a null `order_delivered_customer_date`, were excluded from delay analysis to avoid misleading delay calculations.
- **Join integrity:** All table joins used LEFT joins anchored on the `orders` table. A row-count assertion (`assert len(master) == len(orders)`) confirms zero row duplication from 1-to-many join errors.
- **Relative paths:** All CSV files are loaded using relative paths (e.g. `pd.read_csv('olist_orders_dataset.csv')`), ensuring full reproducibility on any machine.

### Candidate's Choice — "Revenue at Risk" Analysis
**What it is:** A financial exposure metric that joins the `olist_order_payments_dataset.csv` to attach a real R$ value to every late delivery, then aggregates total GMV by delivery status.

**Why it matters to the business:** Late delivery metrics alone (percentages, review scores) are useful for operations but difficult to escalate to the CFO or board. By expressing the problem as **R$ 1,150,866 in revenue at risk**, this feature bridges the gap between logistics data and financial decision-making. Orders tied to late deliveries are at elevated risk of refund claims, chargebacks, and — most expensively — lost repeat purchases. This single number gives the CEO a concrete ROI argument for any proposed logistics infrastructure investment.

---

## D. User Stories Completed

| Story | Description | Status |
|---|---|---|
| Story 1 | Schema Builder — joined Orders, Reviews, Customers, Products | Done |
| Story 2 | Delay Calculator — `days_difference`, On Time / Late / Super Late | Done |
| Story 3 | Geographic Heatmap — late % by Brazilian state | Done |
| Story 4 | Sentiment Correlation — delay vs. review score | Done |
| Bonus | Product category translation (Portuguese → English) | Done |
| Candidate's Choice | Revenue at Risk analysis | Done |

---

## E. How to Run

### Option 1 — Google Colab (Notebook)
1. Open the Colab link above
2. Upload the 7 Olist CSV files to the session storage
3. Runtime → Run all

### Option 2 — Streamlit Dashboard (Local)
```bash
pip install -r requirements.txt
streamlit run app.py
```
Upload the 7 CSV files when prompted. No local paths needed.

### Option 3 — Streamlit Cloud (Live Dashboard)
Visit the dashboard link above - no login required.

---

## F. Repository Structure

```
veridi-logistics-audit/
├── veridi_logistics_audit.ipynb   ← Main analysis notebook
├── veridi_logistics_audit.html    ← Exported notebook (viewable without Colab)
├── app.py                         ← Streamlit dashboard
├── requirements.txt               ← Python dependencies
├── README.md                      ← This file
└── .gitignore                     ← Excludes CSVs and temp files
```

> ⚠️ Raw CSV files are NOT committed to this repo (see `.gitignore`).
> Upload them manually when running locally or use the dashboard's file uploader.
