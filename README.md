# ♻️ ReturnLess — AI-Powered Circular Commerce Platform

> Reduce preventable returns. Give every product a meaningful second life.

ReturnLess is a full-stack AI-powered e-commerce platform that prevents returns before they happen using machine learning, and creates a certified refurbished marketplace for products that do come back.

---

## 🎯 The Problem

Millions of products bought online are returned despite being perfectly usable. Returns cost the industry over $800B annually, 40% of fashion returns are due to wrong sizing, and each returned package generates 4.7x more carbon than a kept one. Customers want refurbished products but don't trust the quality.

## 💡 Our Solution

ReturnLess attacks the return problem from both ends:
- **Before purchase** — AI predicts the right size and catches compatibility issues at checkout
- **After return** — AI grades, routes, and relists products in a trusted refurbished marketplace
- **Behavioral layer** — Green credits reward sustainable choices and penalize careless returns

---

## ✨ Key Features

### 🤖 AI Size Prediction
- **New users**: Enter height + weight → RandomForest ML model (trained on real purchase data) predicts size
- **Returning users**: Purchase history + NLP review analysis (Sentence Transformers) recommends the best fit
- **Review analysis**: Encodes reviews into embeddings, computes cosine similarity to sizing anchors to detect if products run small/large

### 🛒 Smart Checkout Validation
- AI warns if selected size doesn't match recommendation (blocks order until acknowledged)
- Category-specific compatibility checklists auto-generated from review analysis
- Electronics: power, connectivity, storage checks | Clothing: size verification | Beauty: skin type alerts

### 🔍 AI Quality Grading
- 4-dimension scoring: Functional (40%) + Exterior (30%) + Cosmetic (20%) + Packaging (10%)
- Grades: A (Like New) → B (Good) → C (Fair) → D (Salvage)
- AI determines: resell as-is / refurbish / recycle / dispose
- Recommendations based on return reason (defective → refurbish, not recycle)

### 🏭 Intelligent Warehouse Routing
- Scores 12 warehouses across India on: capacity, specialization, distance, demand
- Auto-routes returned items to optimal facility (invisible to customer)
- Full transparency for admin: routing score, alternatives, AI explanation

### 🌱 Green Credit Economy
- +20 credits per standard purchase, +50 for refurbished, +10 for eco shipping
- Returns: earned credits reversed + penalty (15 for careless, 30 for serial returners)
- Tiers: Silver → Gold → Platinum → Green Hero
- Credits = 0? Returns blocked, contact support

### ♻️ Certified Refurbished Marketplace
- Dedicated marketplace with trust badges, warranty, CO₂ savings data
- Full inspection reports and grade transparency
- Same shopping experience as new products, 30-60% cheaper

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Flask, SQLAlchemy, Flask-Login | Modular blueprint architecture |
| Database | SQLite (dev) / PostgreSQL (prod) | Switch with one env var |
| AI/ML | Sentence Transformers (all-MiniLM-L6-v2) | Review NLP, sizing analysis |
| ML | Scikit-learn RandomForest | Body-based size prediction |
| Frontend | Tailwind CSS, DaisyUI, HTMX, Alpine.js | Fast, lightweight, reactive |
| Deployment | Render, Gunicorn | Production ready |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/returnless.git
cd returnless

# Setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Seed database (27 products, 316 reviews, 12 warehouses)
python seed_expanded.py

# Run
python run.py
# Open http://localhost:5000
```

### Accounts
| Role | Email | Password |
|------|-------|----------|
| Customer | demo@returnless.ai | demo123 |
| Admin | admin@returnless.ai | admin123 |

---

## 📁 Project Structure

```
returnless/
├── products/          # Product catalog, search, filters
├── customers/         # Auth, profiles, body measurements
├── ai_reviews/        # Sentiment analysis, topic extraction, AI summaries
├── recommendations/   # ML size prediction (RandomForest + Sentence Transformers)
├── checkout/          # Cart, checkout validation, orders
├── returns/           # Cancel/return with credit penalties
├── grading/           # AI quality inspection (4-dimension scoring)
├── routing/           # Warehouse routing (multi-factor scoring)
├── credits/           # Green credit dashboard, tiers, history
├── marketplace/       # Dedicated refurbished marketplace
├── admin_dashboard/   # Unified admin analytics
├── shared/            # Database, auth, decorators, utilities
├── templates/         # Global templates (base, navbar, footer)
├── static/            # CSS, JS
└── tests/             # 174 tests
```

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
# 174 tests passing
```

---

## 🌐 Deploy to Render

1. Push to GitHub
2. On [render.com](https://render.com) → New → Blueprint → Connect repo
3. Auto-detects `render.yaml` → deploys with PostgreSQL
4. Live at `https://your-app.onrender.com`

---

## 📊 How the AI Works

### Size Prediction Pipeline
```
New User → Height/Weight form → RandomForest (trained on user purchase data) → Predicted size
                                        +
                              Sentence Transformers encode reviews → Cosine similarity to
                              "runs small" / "true to size" / "runs large" anchors → Adjustment
                                        ↓
                              Final recommendation with confidence %
```

### Return Processing Pipeline
```
Customer returns item → Credit check → Penalty calculated → AI grades product
        → Routes to optimal warehouse → Product re-enters refurbished marketplace
```

---

## 🏅 Credit Rules

| Action | Credits |
|--------|---------|
| Standard purchase | +20 |
| Refurbished purchase | +50 |
| Eco shipping | +10 |
| Cancel (before ship) | Reverse earned |
| Cancel (shipped) | Reverse + 10 penalty |
| Return (defective) | Reverse earned only |
| Return (non-defective) | Reverse + 15 penalty |
| Return (serial: 3+/month) | Reverse + 30 penalty |

---

## 🤝 Team

Built for Amazon Smbhav Hackathon 2025

---

## 📄 License

MIT
