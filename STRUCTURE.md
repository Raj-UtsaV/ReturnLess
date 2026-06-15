# ReturnLess — Project Structure & Architecture Guide

## Overview

ReturnLess is a circular economy marketplace that reduces preventable returns using AI and gives returned products a second life through certified refurbishment.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, SQLAlchemy, Flask-Login, Flask-Migrate |
| Database | SQLite (dev), PostgreSQL-ready |
| Frontend | Tailwind CSS, DaisyUI, HTMX, Alpine.js |
| AI/ML | Sentence Transformers, Scikit-learn (optional, falls back to mock) |
| Testing | pytest, pytest-flask |

---

## Folder Structure

```
returnless_ai/
├── app.py                      # Flask app factory, blueprint registration
├── config.py                   # Config classes (dev/test/prod)
├── run.py                      # Entry point: python run.py
├── seed_data.py                # Database seeder with sample data
├── setup.sh / setup.bat        # OS-independent setup scripts
├── requirements.txt            # Python dependencies
├── STRUCTURE.md                # This file
│
├── shared/                     # Shared utilities (used by all modules)
│   ├── __init__.py
│   ├── database.py             # SQLAlchemy db instance + TimestampMixin
│   ├── auth.py                 # Flask-Login setup + user_loader
│   ├── decorators.py           # @admin_required decorator
│   └── utils.py                # File upload, price formatting helpers
│
├── products/                   # Phase 1: Product Catalog
│   ├── models.py               # Product, Category, ProductImage
│   ├── services.py             # ProductService, CategoryService
│   ├── routes.py               # /products/ endpoints
│   └── templates/products/     # Catalog, detail, partials
│
├── customers/                  # Phase 1: Customer accounts (isolated)
│   ├── models.py               # Customer, Address
│   ├── services.py             # CustomerService, AddressService
│   ├── routes.py               # /account/ endpoints
│   └── templates/customers/    # Login, register, profile
│
├── ai_reviews/                 # Phase 2: AI Review Analysis
│   ├── models.py               # Review, ReviewSummary
│   ├── ai_engine.py            # Sentiment, topics, summary (ML + mock)
│   ├── services.py             # ReviewService
│   ├── routes.py               # /reviews/ endpoints
│   └── templates/reviews/      # Review pages + partials
│
├── recommendations/            # Phase 3: AI Size Recommendation
│   ├── models.py               # SizePurchaseHistory, SizeRecommendation
│   ├── ai_engine.py            # Size scoring engine
│   ├── services.py             # SizeRecommendationService
│   ├── routes.py               # /recommendations/ endpoints
│   └── templates/recommendations/  # Size rec partials
│
├── checkout/                   # Phase 4: Cart + Checkout + Orders
│   ├── models.py               # CartItem, Order, OrderItem
│   ├── services.py             # CartService, OrderService
│   ├── routes.py               # /cart, /checkout, /orders, /api/cart
│   └── templates/checkout/     # Cart, checkout, order confirmation, history
│
├── returns/                    # Phase 5: Returns & Cancellations
│   ├── models.py               # ReturnRequest
│   ├── services.py             # ReturnService (credit penalty logic)
│   ├── routes.py               # /returns/ endpoints
│   └── templates/returns/      # Cancel, return, history pages
│
├── grading/                    # Phase 6: Quality Grading
│   ├── models.py               # InspectionRecord
│   ├── ai_engine.py            # GradingEngine (A/B/C/D scoring)
│   ├── services.py             # GradingService
│   ├── routes.py               # /grading/ (admin only)
│   └── templates/grading/      # Inspection form, detail, list
│
├── routing/                    # Phase 7: Warehouse Routing
│   ├── models.py               # Warehouse, RoutingDecision
│   ├── services.py             # RoutingService (scoring algorithm)
│   ├── routes.py               # /routing/ (admin only)
│   └── templates/routing/      # Dashboard with warehouse stats
│
├── credits/                    # Phase 8: Green Credits System
│   ├── models.py               # CreditTransaction
│   ├── services.py             # CreditService (tiers, history)
│   ├── routes.py               # /credits/ endpoints
│   └── templates/credits/      # Dashboard, history
│
├── marketplace/                # Phase 9: Refurbished Marketplace
│   ├── routes.py               # /marketplace/ endpoints
│   └── templates/marketplace/  # Dedicated refurbished shopping page
│
├── admin_dashboard/            # Admin Dashboard (unified analytics)
│   ├── __init__.py
│   ├── routes.py               # /admin/ endpoint
│   └── templates/admin/        # Dashboard with all widgets
│
├── static/
│   ├── css/app.css             # Custom styles, skeleton loaders, animations
│   ├── js/app.js               # HTMX/Alpine.js integration, dark mode
│   └── uploads/                # User-uploaded files
│
├── templates/                  # Global templates
│   ├── base.html               # Master layout (Tailwind + DaisyUI + HTMX + Alpine)
│   ├── index.html              # Homepage
│   └── components/
│       ├── navbar.html         # Main navigation + cart badge + user menu
│       ├── footer.html         # Site footer
│       └── toast.html          # Flash message toasts
│
├── tests/                      # Test suite (174 tests)
│   ├── conftest.py             # Fixtures: app, db, client, sample data
│   ├── test_products.py        # Product + Customer tests (Phase 1)
│   ├── test_ai_reviews.py      # AI review tests (Phase 2)
│   ├── test_recommendations.py # Size rec tests (Phase 3)
│   ├── test_checkout.py        # Cart + order tests (Phase 4)
│   ├── test_returns.py         # Return + cancel tests (Phase 5)
│   └── test_grading.py         # Grading tests (Phase 6)
│
├── instance/
│   └── returnless.db               # SQLite database (auto-created)
│
└── venv/                       # Virtual environment (not committed)
```

---

## Architecture Patterns

### 1. Repository/Service Pattern
Every module follows: `models.py → services.py → routes.py`

- **Models** — SQLAlchemy models, properties, serialization
- **Services** — All business logic. Routes never contain logic.
- **Routes** — Thin controllers: validate input → call service → render template

### 2. Customer Data Isolation
Customer module owns ALL customer data. Product module never stores customer info directly. Cross-references use foreign keys only.

### 3. AI Decisions Include Explanations
Every AI output (size recommendations, review analysis, grading, routing) includes a human-readable `explanation` field explaining how the decision was made.

### 4. Graceful ML Fallback
AI engines check for ML library availability at import time. If `sentence-transformers` or `scikit-learn` aren't installed, they fall back to rule-based keyword matching. The app works fully without ML dependencies.

### 5. HTMX for Progressive Enhancement
Partial templates in `partials/` subdirectories are swappable via HTMX without full page reload (cart updates, review loading, size recommendations).

---

## Module Dependency Map

```
products ──────────────────────┐
customers ─────────────────────┤
ai_reviews ── (uses products, customers) ─┤
recommendations ── (uses products, customers, ai_reviews) ─┤
checkout ── (uses products, customers, recommendations) ─┤
returns ── (uses checkout, customers, products, routing, grading) ─┤
grading ── (uses products, returns) ─┤
routing ── (uses returns, products) ─┤
credits ── (uses customers) ─┤
marketplace ── (uses products) ─┤
admin_dashboard ── (reads from all) ─┘
```

---

## Green Credit Rules

| Action | Credits |
|--------|---------|
| Standard purchase | +20 |
| Refurbished purchase | +50 |
| Eco shipping | +10 |
| Cancel (pre-ship) | Reverse earned |
| Cancel (shipped) | Reverse + **-15** penalty |
| Return (defective) | Reverse earned (no penalty) |
| Return (non-defective) | Reverse + **-15** penalty |
| Return (serial: 3+/month) | Reverse + **-30** penalty |

### Tiers
| Tier | Lifetime Credits |
|------|-----------------|
| 🥈 Silver | 0+ |
| 🥇 Gold | 500+ |
| 💎 Platinum | 1500+ |
| 🌍 Green Hero | 3000+ |

---

## Quality Grading Scale

| Grade | Score | Description | Action |
|-------|-------|-------------|--------|
| A | 90-100 | Like new | Resell as-is or light refurb |
| B | 70-89 | Good | Refurbish then resell |
| C | 50-69 | Fair | Refurbish if functional |
| D | 0-49 | Salvage | Recycle or dispose |

**Scoring weights**: Functional (40%) + Exterior (30%) + Cosmetic (20%) + Packaging (10%)

---

## Routing Algorithm

Warehouse selection uses weighted scoring:
- **Capacity** (35%): Available space
- **Specialization** (25%): Category match
- **Distance** (20%): Proximity to customer
- **Demand** (20%): Local demand for product type

Customer NEVER sees routing decisions. Only admin views.

---

## Key URLs

| URL | Access | Description |
|-----|--------|-------------|
| `/` | Public | Homepage |
| `/products/` | Public | Product catalog |
| `/products/<slug>` | Public | Product detail |
| `/marketplace/` | Public | Refurbished marketplace |
| `/account/login` | Public | Login |
| `/account/register` | Public | Register |
| `/cart` | Auth | Shopping cart |
| `/checkout` | Auth | Checkout with AI size validation |
| `/orders` | Auth | Order history |
| `/credits/` | Auth | Green credits dashboard |
| `/reviews/product/<id>` | Public | Product reviews |
| `/recommendations/size/<id>` | Auth | AI size recommendation |
| `/returns/cancel/<id>` | Auth | Cancel order |
| `/returns/return/<id>/<item>` | Auth | Return item |
| `/admin/` | Admin | Admin dashboard |
| `/grading/` | Admin | Quality grading |
| `/routing/` | Admin | Warehouse routing |

---

## How to Add a New Module

1. Create folder: `returnless_ai/new_module/`
2. Add files: `__init__.py`, `models.py`, `services.py`, `routes.py`
3. Add templates: `new_module/templates/new_module/`
4. Register blueprint in `app.py` → `_register_blueprints()`
5. Import models in `app.py` → `_import_models()`
6. Add tests in `tests/test_new_module.py`
7. Run `python -m pytest tests/` to verify

---

## How to Modify Credit Logic

Edit `returns/services.py`:
- `CANCEL_SHIPPED_PENALTY` — penalty for cancelling shipped orders
- `RETURN_STANDARD_PENALTY` — penalty for non-defective returns
- `RETURN_SERIAL_PENALTY` — penalty for frequent returners
- `DEFECTIVE_REASONS` — set of reasons that get no penalty

Edit `checkout/services.py` → `OrderService.create_order()`:
- Modify `green_credits_earn` logic for purchases

---

## How to Add a New Product Category

1. Add to `seed_data.py` in the `categories_data` list
2. Add products for that category in `products_data`
3. Run `python seed_data.py` to reseed
4. (Optional) Add category link in `templates/components/navbar.html` category bar

---

## How to Adjust AI Behavior

### Review Analysis
Edit `ai_reviews/ai_engine.py`:
- `positive_words` / `negative_words` — sentiment keywords
- `topic_keywords` — aspect extraction rules
- Threshold values for sentiment classification

### Size Recommendations
Edit `recommendations/ai_engine.py`:
- `SIZE_ORDER` — size ordering map
- `_score_size()` — factor weights (history 45%, returns 25%, reviews 20%, brand 10%)

### Quality Grading
Edit `grading/ai_engine.py`:
- `GRADE_THRESHOLDS` — score-to-grade mapping
- `_calculate_overall_score()` — weight factors
- `CARBON_SAVINGS_BY_CATEGORY` — CO₂ estimates

### Warehouse Routing
Edit `routing/services.py`:
- Factor weights in `route_return()` (capacity 35%, spec 25%, distance 20%, demand 20%)
- `state_regions` mapping for proximity calculation

---

## Database Migration (SQLite → PostgreSQL)

1. Set `DATABASE_URL` environment variable:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/returnless
   ```
2. Set `FLASK_ENV=production`
3. Run `flask db init && flask db migrate && flask db upgrade`
4. Reseed: `python seed_data.py`

No code changes needed — the ORM handles the rest.

---

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_checkout.py -v

# With coverage (install pytest-cov first)
python -m pytest tests/ --cov=. --cov-report=term-missing
```

---

## Debug Features

- **Order status buttons**: On every order detail page, yellow "Debug" section lets you manually change status to test cancel/return flows
- **Mock AI mode**: Works without ML libraries installed (keyword-based heuristics)
- **SQLite**: No database server needed for development
