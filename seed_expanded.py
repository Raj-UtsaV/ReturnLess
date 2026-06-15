"""Expanded seed data — more products per category + 10-15 reviews per product."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from shared.database import db
from products.models import Product, Category
from customers.models import Customer
from ai_reviews.models import Review, ReviewSummary
from recommendations.models import SizePurchaseHistory
from routing.models import Warehouse


def seed():
    app = create_app()
    with app.app_context():
        print("🌱 Seeding expanded database...")

        # Clear
        db.session.query(Review).delete()
        db.session.query(ReviewSummary).delete()
        db.session.query(SizePurchaseHistory).delete()
        db.session.query(Warehouse).delete()
        db.session.query(Product).delete()
        db.session.query(Category).delete()
        db.session.query(Customer).delete()
        db.session.commit()

        # ── Categories ──
        categories_data = [
            {"name": "Electronics", "slug": "electronics", "icon": "💻", "description": "Phones, laptops, and gadgets"},
            {"name": "Clothing", "slug": "clothing", "icon": "👕", "description": "Fashion and apparel"},
            {"name": "Home & Kitchen", "slug": "home-kitchen", "icon": "🏠", "description": "Home essentials"},
            {"name": "Books", "slug": "books", "icon": "📚", "description": "Books and publications"},
            {"name": "Sports", "slug": "sports", "icon": "⚽", "description": "Sports and outdoors"},
            {"name": "Beauty", "slug": "beauty", "icon": "✨", "description": "Beauty and personal care"},
        ]
        categories = {}
        for c in categories_data:
            cat = Category(**c)
            db.session.add(cat)
            categories[c["slug"]] = cat
        db.session.flush()

        # ── Products ──
        products_data = [
            # === ELECTRONICS (6 products) ===
            {"name": "Samsung Galaxy S24 Ultra - 256GB Titanium Black", "slug": "samsung-galaxy-s24-ultra-256gb", "description": "Experience the future with Galaxy AI. 6.8-inch Dynamic AMOLED 2X, Snapdragon 8 Gen 3, 200MP camera, S Pen.", "short_description": "AI-powered flagship with 200MP camera", "price": 129999, "original_price": 134999, "category_slug": "electronics", "brand": "Samsung", "sku": "SAM-S24U-256-BLK", "stock_quantity": 25, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.6, "total_reviews": 1247, "specifications": {"Display": "6.8\" QHD+", "Processor": "Snapdragon 8 Gen 3", "RAM": "12GB", "Storage": "256GB", "Battery": "5000mAh"}},
            {"name": "Apple MacBook Air M3 - 15 inch Space Gray", "slug": "apple-macbook-air-m3-15-inch", "description": "Ultra-thin design powered by M3 chip. 15.3-inch Liquid Retina, 18-hour battery, MagSafe.", "short_description": "Ultra-thin 15\" laptop with M3 chip", "price": 149900, "original_price": 149900, "category_slug": "electronics", "brand": "Apple", "sku": "APL-MBA-M3-15-GRY", "stock_quantity": 15, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.8, "total_reviews": 892, "eco_friendly": True, "specifications": {"Display": "15.3\" Liquid Retina", "Chip": "Apple M3", "RAM": "8GB", "Storage": "256GB SSD", "Battery": "18 hours"}},
            {"name": "Apple iPhone 14 Pro Max - 128GB (Certified Refurbished)", "slug": "apple-iphone-14-pro-max-refurbished", "description": "Certified refurbished iPhone 14 Pro Max. Dynamic Island, 48MP camera, A16 Bionic.", "short_description": "Like-new iPhone 14 Pro Max with full warranty", "price": 79999, "original_price": 139900, "category_slug": "electronics", "brand": "Apple", "sku": "APL-14PM-128-REFURB", "stock_quantity": 8, "product_type": "refurbished", "thumbnail": "https://images.unsplash.com/photo-1678685888221-cda773a3dcdb?w=400", "delivery_days_min": 2, "delivery_days_max": 5, "free_delivery": True, "green_credits_earn": 50, "avg_rating": 4.5, "total_reviews": 342, "grade": "A", "warranty_months": 12, "carbon_saved_kg": 72.5, "refurb_reason": "Customer return - unopened", "inspection_notes": "Pristine condition. Battery health 100%.", "refurbished_by": "ReturnLess Labs", "specifications": {"Display": "6.7\" Super Retina XDR", "Chip": "A16 Bionic", "Storage": "128GB"}},
            {"name": "Sony WH-1000XM5 Noise Cancelling Headphones (Refurbished)", "slug": "sony-wh-1000xm5-refurbished", "description": "Industry-leading ANC with 8 microphones, 30-hour battery, multipoint connection.", "short_description": "Industry-leading ANC headphones, restored", "price": 17999, "original_price": 29990, "category_slug": "electronics", "brand": "Sony", "sku": "SONY-XM5-BLK-REFURB", "stock_quantity": 12, "product_type": "refurbished", "thumbnail": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": True, "green_credits_earn": 50, "avg_rating": 4.7, "total_reviews": 567, "grade": "A", "warranty_months": 6, "carbon_saved_kg": 8.3, "refurb_reason": "Open-box return", "inspection_notes": "Minimal use. ANC at full performance.", "refurbished_by": "ReturnLess Labs", "specifications": {"Type": "Over-ear wireless", "ANC": "Industry-leading", "Battery": "30 hours"}},
            {"name": "Dell XPS 15 Laptop - i7/16GB/512GB (Certified Refurbished)", "slug": "dell-xps-15-i7-refurbished", "description": "Premium ultrabook. 15.6-inch OLED 3.5K, i7-13700H, 16GB RAM, RTX 4050.", "short_description": "Premium OLED ultrabook, restored", "price": 89999, "original_price": 159990, "category_slug": "electronics", "brand": "Dell", "sku": "DELL-XPS15-I7-REFURB", "stock_quantity": 5, "product_type": "refurbished", "thumbnail": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400", "delivery_days_min": 3, "delivery_days_max": 6, "free_delivery": True, "green_credits_earn": 50, "avg_rating": 4.6, "total_reviews": 234, "grade": "A", "warranty_months": 12, "carbon_saved_kg": 320.0, "refurb_reason": "Corporate lease return", "inspection_notes": "Excellent condition. Battery cycle: 47.", "refurbished_by": "ReturnLess Labs", "specifications": {"Display": "15.6\" 3.5K OLED", "CPU": "i7-13700H", "RAM": "16GB DDR5", "GPU": "RTX 4050"}},
            {"name": "OnePlus 12 - 256GB Flowy Emerald", "slug": "oneplus-12-256gb-emerald", "description": "Flagship killer with Snapdragon 8 Gen 3, 50MP Hasselblad camera, 5400mAh battery, 100W charging.", "short_description": "Flagship killer with Hasselblad camera", "price": 64999, "original_price": 69999, "category_slug": "electronics", "brand": "OnePlus", "sku": "OP-12-256-EMR", "stock_quantity": 18, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.5, "total_reviews": 876, "specifications": {"Display": "6.82\" 2K LTPO", "Processor": "Snapdragon 8 Gen 3", "RAM": "12GB", "Battery": "5400mAh", "Charging": "100W"}},

            # === CLOTHING (5 products) ===
            {"name": "Nike Dri-FIT Running T-Shirt - Men's", "slug": "nike-dri-fit-running-tshirt-mens", "description": "Lightweight Dri-FIT wicks sweat. 75% recycled polyester. Reflective details.", "short_description": "Lightweight moisture-wicking running tee", "price": 2495, "original_price": 2995, "category_slug": "clothing", "brand": "Nike", "sku": "NIKE-DRIFIT-RUN-M-BLK", "stock_quantity": 50, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400", "delivery_days_min": 3, "delivery_days_max": 6, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.4, "total_reviews": 2156, "eco_friendly": True, "available_sizes": ["S", "M", "L", "XL", "XXL"], "color": "Black", "specifications": {"Material": "75% Recycled Polyester", "Fit": "Standard", "Sleeve": "Short"}},
            {"name": "Levi's 511 Slim Fit Jeans - Dark Indigo", "slug": "levis-511-slim-fit-jeans-dark-indigo", "description": "Slim fit through hip and thigh. Water<Less technology. Stretch denim.", "short_description": "Classic slim fit jeans, sustainable", "price": 3999, "original_price": 4599, "category_slug": "clothing", "brand": "Levi's", "sku": "LEVIS-511-SLIM-IND-32", "stock_quantity": 35, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400", "delivery_days_min": 4, "delivery_days_max": 7, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.3, "total_reviews": 1834, "eco_friendly": True, "available_sizes": ["28", "30", "32", "34", "36", "38"], "color": "Dark Indigo", "specifications": {"Material": "99% Cotton, 1% Elastane", "Fit": "Slim", "Rise": "Mid Rise"}},
            {"name": "Adidas Ultraboost Light Running Shoes", "slug": "adidas-ultraboost-light-running", "description": "Lightest Ultraboost ever. BOOST midsole, Continental rubber outsole, Primeknit+ upper.", "short_description": "Lightest Ultraboost with BOOST cushion", "price": 14999, "original_price": 16999, "category_slug": "clothing", "brand": "Adidas", "sku": "ADI-UBL-BLK-9", "stock_quantity": 20, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400", "delivery_days_min": 3, "delivery_days_max": 6, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.6, "total_reviews": 1523, "available_sizes": ["7", "8", "9", "10", "11"], "color": "Core Black", "specifications": {"Type": "Running", "Midsole": "BOOST", "Upper": "Primeknit+", "Outsole": "Continental Rubber"}},
            {"name": "H&M Regular Fit Oxford Shirt - White", "slug": "hm-oxford-shirt-white", "description": "Classic Oxford shirt in woven cotton. Button-down collar, chest pocket. Versatile everyday wear.", "short_description": "Classic Oxford shirt for everyday", "price": 1499, "original_price": 1999, "category_slug": "clothing", "brand": "H&M", "sku": "HM-OXFORD-WHT-M", "stock_quantity": 40, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400", "delivery_days_min": 4, "delivery_days_max": 7, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.2, "total_reviews": 987, "available_sizes": ["S", "M", "L", "XL"], "color": "White", "specifications": {"Material": "100% Cotton", "Fit": "Regular", "Collar": "Button-down"}},
            {"name": "Zara Oversized Hoodie - Charcoal Gray", "slug": "zara-oversized-hoodie-charcoal", "description": "Soft brushed fleece hoodie with kangaroo pocket. Oversized relaxed fit. Drawstring hood.", "short_description": "Cozy oversized fleece hoodie", "price": 2799, "original_price": 3499, "category_slug": "clothing", "brand": "Zara", "sku": "ZARA-HOOD-CHAR-L", "stock_quantity": 30, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400", "delivery_days_min": 4, "delivery_days_max": 7, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.4, "total_reviews": 654, "available_sizes": ["S", "M", "L", "XL", "XXL"], "color": "Charcoal Gray", "specifications": {"Material": "80% Cotton, 20% Polyester", "Fit": "Oversized", "Features": "Kangaroo pocket, drawstring hood"}},

            # === HOME & KITCHEN (4 products) ===
            {"name": "Dyson V15 Detect Absolute Vacuum Cleaner", "slug": "dyson-v15-detect-absolute-vacuum", "description": "Most powerful cordless vacuum. Laser dust detection, piezo sensor, 60 min runtime.", "short_description": "Laser-guided intelligent cordless vacuum", "price": 52900, "original_price": 58900, "category_slug": "home-kitchen", "brand": "Dyson", "sku": "DYS-V15-DET-ABS", "stock_quantity": 7, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400", "delivery_days_min": 3, "delivery_days_max": 6, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.7, "total_reviews": 423, "specifications": {"Type": "Cordless Stick", "Suction": "230 AW", "Runtime": "60 min", "Weight": "3.1kg"}},
            {"name": "Instant Pot Duo Plus 6-Quart (Certified Refurbished)", "slug": "instant-pot-duo-plus-6qt-refurbished", "description": "9-in-1 multi-cooker restored to factory condition. Pressure, slow, rice, steam, sauté.", "short_description": "9-in-1 multi-cooker, factory restored", "price": 5499, "original_price": 9999, "category_slug": "home-kitchen", "brand": "Instant Pot", "sku": "IP-DUO-PLUS-6Q-REFURB", "stock_quantity": 20, "product_type": "refurbished", "thumbnail": "https://images.unsplash.com/photo-1585515320310-259814833e62?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": True, "green_credits_earn": 50, "avg_rating": 4.6, "total_reviews": 789, "grade": "B", "warranty_months": 6, "carbon_saved_kg": 15.2, "refurb_reason": "Minor cosmetic wear", "inspection_notes": "Small scratch on lid. All tests passed.", "refurbished_by": "ReturnLess Labs", "specifications": {"Capacity": "6 Quart", "Functions": "9-in-1", "Power": "1000W"}},
            {"name": "Philips Air Fryer HD9200/90 - 4.1L", "slug": "philips-air-fryer-hd9200", "description": "Rapid Air technology for crispy food with 90% less fat. 4.1L capacity, 1400W, dishwasher safe.", "short_description": "Crispy food with 90% less fat", "price": 6999, "original_price": 8999, "category_slug": "home-kitchen", "brand": "Philips", "sku": "PHI-AF-HD9200", "stock_quantity": 15, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1626082927389-6cd097cee6b6?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.4, "total_reviews": 2341, "specifications": {"Capacity": "4.1L", "Power": "1400W", "Technology": "Rapid Air", "Dishwasher Safe": "Yes"}},
            {"name": "IKEA KALLAX Shelf Unit - White", "slug": "ikea-kallax-shelf-white", "description": "Versatile storage unit. Use horizontally or vertically. Compatible with inserts and boxes.", "short_description": "Versatile modular shelf unit", "price": 4990, "original_price": 5990, "category_slug": "home-kitchen", "brand": "IKEA", "sku": "IKEA-KALLAX-4-WHT", "stock_quantity": 10, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400", "delivery_days_min": 5, "delivery_days_max": 10, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.3, "total_reviews": 1567, "specifications": {"Dimensions": "77x77x39 cm", "Material": "Particleboard", "Compartments": "4", "Assembly": "Required"}},

            # === BOOKS (4 products) ===
            {"name": "Atomic Habits by James Clear - Hardcover", "slug": "atomic-habits-james-clear-hardcover", "description": "Proven framework for building good habits and breaking bad ones.", "short_description": "Build good habits, break bad ones", "price": 599, "original_price": 799, "category_slug": "books", "brand": "Penguin Random House", "sku": "BK-ATOMIC-HABITS-HC", "stock_quantity": 100, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.8, "total_reviews": 5621, "specifications": {"Author": "James Clear", "Pages": "320", "Format": "Hardcover"}},
            {"name": "Psychology of Money by Morgan Housel", "slug": "psychology-of-money-morgan-housel", "description": "Timeless lessons on wealth, greed, and happiness. How people think about money.", "short_description": "Timeless lessons on wealth and happiness", "price": 399, "original_price": 499, "category_slug": "books", "brand": "Harper Business", "sku": "BK-PSYCH-MONEY-PB", "stock_quantity": 80, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.7, "total_reviews": 4230, "specifications": {"Author": "Morgan Housel", "Pages": "256", "Format": "Paperback"}},
            {"name": "Deep Work by Cal Newport", "slug": "deep-work-cal-newport", "description": "Rules for focused success in a distracted world. Learn to work deeply.", "short_description": "Rules for focused success", "price": 449, "original_price": 599, "category_slug": "books", "brand": "Grand Central", "sku": "BK-DEEP-WORK-PB", "stock_quantity": 60, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.5, "total_reviews": 2890, "specifications": {"Author": "Cal Newport", "Pages": "304", "Format": "Paperback"}},
            {"name": "Sapiens by Yuval Noah Harari", "slug": "sapiens-yuval-noah-harari", "description": "A brief history of humankind. How Homo sapiens conquered the world.", "short_description": "A brief history of humankind", "price": 499, "original_price": 699, "category_slug": "books", "brand": "Vintage", "sku": "BK-SAPIENS-PB", "stock_quantity": 70, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.6, "total_reviews": 6120, "specifications": {"Author": "Yuval Noah Harari", "Pages": "498", "Format": "Paperback"}},

            # === SPORTS (4 products) ===
            {"name": "Fitbit Charge 6 Fitness Tracker - Obsidian", "slug": "fitbit-charge-6-fitness-tracker", "description": "Built-in GPS, heart rate, sleep tracking, Google integration. 7-day battery.", "short_description": "Advanced fitness tracker with GPS", "price": 14999, "original_price": 14999, "category_slug": "sports", "brand": "Fitbit", "sku": "FIT-CHARGE6-OBS", "stock_quantity": 30, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": True, "green_credits_earn": 20, "avg_rating": 4.3, "total_reviews": 1102, "specifications": {"Display": "AMOLED", "Battery": "7 days", "GPS": "Built-in", "Water Resistance": "50m"}},
            {"name": "Decathlon Domyos Resistance Bands Set", "slug": "decathlon-resistance-bands-set", "description": "Set of 5 resistance bands with different strengths. Ideal for home workouts and rehab.", "short_description": "5-band set for home workouts", "price": 799, "original_price": 999, "category_slug": "sports", "brand": "Decathlon", "sku": "DEC-BANDS-SET5", "stock_quantity": 50, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400", "delivery_days_min": 3, "delivery_days_max": 6, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.4, "total_reviews": 876, "specifications": {"Quantity": "5 bands", "Resistance": "Light to Heavy", "Material": "Natural Latex"}},
            {"name": "Yoga Mat Premium 6mm - Purple", "slug": "yoga-mat-premium-6mm-purple", "description": "Non-slip TPE material, 6mm thickness for joint comfort. Eco-friendly, includes carry strap.", "short_description": "Eco-friendly non-slip yoga mat", "price": 1299, "original_price": 1799, "category_slug": "sports", "brand": "Boldfit", "sku": "BF-YOGA-6MM-PRP", "stock_quantity": 45, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.3, "total_reviews": 2134, "eco_friendly": True, "specifications": {"Thickness": "6mm", "Material": "TPE (Eco-friendly)", "Size": "183x61cm", "Includes": "Carry strap"}},
            {"name": "Nivia Storm Football - Size 5", "slug": "nivia-storm-football-size5", "description": "Machine stitched, 32 panel construction. Suitable for training and recreational play.", "short_description": "Durable training football", "price": 699, "original_price": 899, "category_slug": "sports", "brand": "Nivia", "sku": "NIV-STORM-FB-5", "stock_quantity": 60, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1614632537197-38a17061c2bd?w=400", "delivery_days_min": 3, "delivery_days_max": 5, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.1, "total_reviews": 1456, "specifications": {"Size": "5", "Panels": "32", "Stitching": "Machine", "Material": "PVC"}},

            # === BEAUTY (4 products) ===
            {"name": "The Ordinary Niacinamide 10% + Zinc 1% Serum", "slug": "the-ordinary-niacinamide-zinc-serum", "description": "Reduces blemishes and congestion. Zinc PCA balances sebum activity.", "short_description": "Blemish-fighting serum", "price": 590, "original_price": 590, "category_slug": "beauty", "brand": "The Ordinary", "sku": "TO-NIACINAMIDE-30ML", "stock_quantity": 75, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.5, "total_reviews": 3421, "eco_friendly": True, "specifications": {"Volume": "30ml", "Key Ingredients": "Niacinamide 10%, Zinc PCA 1%", "Skin Type": "All"}},
            {"name": "Cetaphil Gentle Skin Cleanser - 500ml", "slug": "cetaphil-gentle-cleanser-500ml", "description": "Mild soap-free formula for sensitive skin. Dermatologist recommended. Non-comedogenic.", "short_description": "Gentle cleanser for sensitive skin", "price": 799, "original_price": 899, "category_slug": "beauty", "brand": "Cetaphil", "sku": "CET-GENTLE-500ML", "stock_quantity": 40, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.6, "total_reviews": 4567, "specifications": {"Volume": "500ml", "Skin Type": "Sensitive", "Soap Free": "Yes", "Dermatologist Tested": "Yes"}},
            {"name": "Maybelline Fit Me Foundation - 128 Warm Nude", "slug": "maybelline-fit-me-foundation-128", "description": "Lightweight foundation with natural finish. Poreless formula with SPF. Oil-free.", "short_description": "Natural finish lightweight foundation", "price": 499, "original_price": 599, "category_slug": "beauty", "brand": "Maybelline", "sku": "MAY-FITME-128", "stock_quantity": 55, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.2, "total_reviews": 3890, "specifications": {"Volume": "30ml", "Finish": "Natural", "SPF": "Yes", "Shade": "128 Warm Nude"}},
            {"name": "L'Oreal Paris Hyaluronic Acid Serum", "slug": "loreal-hyaluronic-acid-serum", "description": "1.5% pure Hyaluronic Acid for intense hydration. Plumps skin, reduces fine lines.", "short_description": "Intense hydration serum", "price": 699, "original_price": 899, "category_slug": "beauty", "brand": "L'Oreal", "sku": "LOR-HA-SERUM-30ML", "stock_quantity": 35, "product_type": "standard", "thumbnail": "https://images.unsplash.com/photo-1570194065650-d99fb4b38b17?w=400", "delivery_days_min": 2, "delivery_days_max": 4, "free_delivery": False, "green_credits_earn": 20, "avg_rating": 4.4, "total_reviews": 2670, "specifications": {"Volume": "30ml", "Key Ingredient": "1.5% Hyaluronic Acid", "Skin Type": "All", "Concern": "Hydration, Fine Lines"}},
        ]

        for p in products_data:
            slug = p.pop("category_slug")
            p["category_id"] = categories[slug].id
            db.session.add(Product(**p))
        db.session.flush()
        print(f"   📦 {len(products_data)} products created")

        # ── Customers ──
        customers_main = [
            {"email": "demo@returnless.ai", "password": "demo123", "first_name": "Demo", "last_name": "User", "green_credits": 250, "lifetime_credits": 250},
            {"email": "admin@returnless.ai", "password": "admin123", "first_name": "Admin", "last_name": "User", "green_credits": 5000, "lifetime_credits": 5000, "is_admin": True},
        ]
        for c in customers_main:
            pwd = c.pop("password")
            cust = Customer(**c)
            cust.set_password(pwd)
            db.session.add(cust)

        # Reviewer customers (20 for diverse reviews) with body measurements for ML training
        reviewer_names = [
            ("Priya", "Sharma"), ("Rahul", "Kumar"), ("Anita", "Patel"), ("Vikram", "Singh"),
            ("Sneha", "Reddy"), ("Arjun", "Nair"), ("Meera", "Gupta"), ("Karthik", "Iyer"),
            ("Deepa", "Joshi"), ("Rohit", "Verma"), ("Kavita", "Das"), ("Amit", "Rao"),
            ("Pooja", "Mishra"), ("Suresh", "Pillai"), ("Neha", "Agarwal"), ("Ravi", "Bhat"),
            ("Swati", "Kulkarni"), ("Manoj", "Tiwari"), ("Divya", "Menon"), ("Sanjay", "Chauhan"),
        ]
        # Body measurements + sizes they typically keep (for ML training)
        body_data = [
            (155, 48, "slim", "S"), (170, 72, "regular", "M"), (162, 55, "slim", "S"),
            (180, 85, "athletic", "L"), (158, 52, "slim", "S"), (175, 78, "athletic", "L"),
            (165, 60, "regular", "M"), (178, 82, "regular", "L"), (160, 58, "regular", "M"),
            (182, 90, "plus", "XL"), (155, 50, "slim", "S"), (172, 70, "regular", "M"),
            (168, 65, "regular", "M"), (176, 80, "athletic", "L"), (158, 53, "slim", "S"),
            (185, 95, "plus", "XL"), (163, 57, "regular", "M"), (179, 88, "athletic", "L"),
            (166, 62, "regular", "M"), (183, 92, "plus", "XL"),
        ]
        reviewers = []
        for i, (fn, ln) in enumerate(reviewer_names):
            h, w, bt, _ = body_data[i]
            r = Customer(
                email=f"{fn.lower()}.{ln.lower()}@example.com",
                first_name=fn, last_name=ln,
                green_credits=50, lifetime_credits=50,
                height_cm=h, weight_kg=w, body_type=bt,
            )
            r.set_password("reviewer123")
            db.session.add(r)
            reviewers.append(r)
        db.session.flush()
        print(f"   👤 {2 + len(reviewers)} customers created")

        # ── Warehouses ──
        warehouses_data = [
            {"name": "Mumbai Central Hub", "code": "MUM-01", "city": "Mumbai", "state": "Maharashtra", "capacity": 500, "current_load": 180, "specialization": "electronics"},
            {"name": "Delhi NCR Fulfillment", "code": "DEL-01", "city": "Delhi", "state": "Delhi", "capacity": 600, "current_load": 320, "specialization": "general"},
            {"name": "Bangalore Tech Center", "code": "BLR-01", "city": "Bangalore", "state": "Karnataka", "capacity": 400, "current_load": 150, "specialization": "electronics"},
            {"name": "Hyderabad Logistics Park", "code": "HYD-01", "city": "Hyderabad", "state": "Telangana", "capacity": 350, "current_load": 120, "specialization": "electronics"},
            {"name": "Chennai South Center", "code": "CHE-01", "city": "Chennai", "state": "Tamil Nadu", "capacity": 350, "current_load": 200, "specialization": "clothing"},
            {"name": "Kolkata East Hub", "code": "KOL-01", "city": "Kolkata", "state": "West Bengal", "capacity": 300, "current_load": 90, "specialization": "clothing"},
            {"name": "Pune West Warehouse", "code": "PUN-01", "city": "Pune", "state": "Maharashtra", "capacity": 300, "current_load": 110, "specialization": "home-kitchen"},
            {"name": "Ahmedabad Distribution", "code": "AMD-01", "city": "Ahmedabad", "state": "Gujarat", "capacity": 250, "current_load": 80, "specialization": "home-kitchen"},
            {"name": "Jaipur North Hub", "code": "JAI-01", "city": "Jaipur", "state": "Rajasthan", "capacity": 200, "current_load": 60, "specialization": "general"},
            {"name": "Lucknow Central", "code": "LKO-01", "city": "Lucknow", "state": "Uttar Pradesh", "capacity": 250, "current_load": 95, "specialization": "general"},
            {"name": "Surat Textile Hub", "code": "SUR-01", "city": "Surat", "state": "Gujarat", "capacity": 200, "current_load": 70, "specialization": "clothing"},
            {"name": "Bhopal Central Warehouse", "code": "BPL-01", "city": "Bhopal", "state": "Madhya Pradesh", "capacity": 200, "current_load": 45, "specialization": "electronics"},
        ]
        for w in warehouses_data:
            db.session.add(Warehouse(**w))
        db.session.flush()
        print(f"   🏭 {len(warehouses_data)} warehouses created")

        # ── Size History for Demo user ──
        demo = Customer.query.filter_by(email="demo@returnless.ai").first()
        clothing_cat = categories["clothing"]
        nike = Product.query.filter_by(sku="NIKE-DRIFIT-RUN-M-BLK").first()
        if demo and nike:
            for _ in range(3):
                db.session.add(SizePurchaseHistory(customer_id=demo.id, product_id=nike.id, category_id=clothing_cat.id, size_purchased="M", brand="Nike", kept=True))
            db.session.add(SizePurchaseHistory(customer_id=demo.id, product_id=nike.id, category_id=clothing_cat.id, size_purchased="L", brand="Nike", kept=False, return_reason="too_large"))
            db.session.add(SizePurchaseHistory(customer_id=demo.id, product_id=nike.id, category_id=clothing_cat.id, size_purchased="M", brand="Levi's", kept=True))
            db.session.flush()

        # ── Size History for Reviewers (ML training data) ──
        clothing_products = Product.query.filter_by(category_id=clothing_cat.id).all()
        if clothing_products:
            for i, reviewer in enumerate(reviewers):
                _, _, _, typical_size = body_data[i]
                # Each reviewer "bought and kept" their typical size from a random clothing product
                prod = clothing_products[i % len(clothing_products)]
                if typical_size in (prod.available_sizes or []):
                    db.session.add(SizePurchaseHistory(
                        customer_id=reviewer.id,
                        product_id=prod.id,
                        category_id=clothing_cat.id,
                        size_purchased=typical_size,
                        brand=prod.brand,
                        kept=True,
                    ))
            db.session.flush()
            print(f"   📏 Size history for {len(reviewers)} reviewers created (ML training data)")

        # ── REVIEWS (10-15 per product) ──
        all_products = Product.query.all()
        review_templates = {
            "electronics": [
                (5, "Absolutely incredible!", "Best tech purchase I've made. Performance is blazing fast, display is stunning, and battery easily lasts all day. Camera quality is phenomenal."),
                (5, "Worth every penny", "Premium build quality, excellent performance. The AI features are genuinely useful. Highly recommend for power users."),
                (4, "Great but pricey", "Fantastic device with amazing specs. Only complaint is the high price point, but you get what you pay for. Build quality is top notch."),
                (4, "Solid upgrade", "Coming from an older model, this is a huge improvement. Everything is faster and smoother. Battery life is impressive."),
                (5, "Camera beast", "The camera system blows my mind. Night mode is incredible, video recording is cinema quality. Best phone camera I've ever used."),
                (3, "Good but overpriced", "It's a good device but at this price I expected more. Some software features feel half-baked. Performance is great though."),
                (4, "Reliable daily driver", "Using it for work and personal use. Very reliable, no lag, great screen. Sound quality through speakers is impressive."),
                (5, "No regrets", "Did a lot of research before buying. Absolutely no regrets. Everything works flawlessly. The ecosystem integration is seamless."),
                (2, "Disappointed with battery", "Battery drain is terrible when using 5G. Phone gets warm during gaming. Camera is great but battery life needs work."),
                (4, "Feature packed", "So many features packed into this device. The AI assistants, cameras, display - all top class. Charging speed is amazing too."),
                (5, "Best in class", "After trying multiple brands, this is the best. Display clarity, processing speed, and camera quality are unmatched."),
                (3, "Mixed feelings", "Hardware is excellent but software has bugs. Regular updates fix things but it's annoying. Otherwise a solid device."),
            ],
            "clothing": [
                (5, "Perfect fit!", "Fits true to size. Material quality is excellent. Very comfortable for all-day wear. Colors don't fade after washing."),
                (4, "Good but runs slightly small", "Nice quality overall. However, it runs a bit small compared to other brands. Recommend sizing up if between sizes."),
                (5, "Love the material", "Super soft and breathable. Perfect for workouts and casual wear. The stitching is solid, no loose threads."),
                (3, "Decent for the price", "It's okay for the price. Material is thinner than expected. Fit is a bit tight around shoulders. Acceptable quality."),
                (5, "My go-to brand now", "Third time buying from this brand. Always consistent sizing, great material quality. True to size every time."),
                (4, "Comfortable everyday wear", "Very comfortable for daily use. Washes well without shrinking. Colors stay vibrant. Slightly long in the torso."),
                (2, "Size issue", "Ordered my usual size but it was way too small. Had to return. The sizing chart seems off for this particular item."),
                (5, "Excellent quality", "Premium feel, excellent stitching, comfortable fit. Wore it multiple times and it still looks brand new after washing."),
                (4, "Great for the gym", "Moisture wicking works perfectly. Light and breathable. A bit tight if you have broader shoulders, consider sizing up."),
                (5, "Sustainable and stylish", "Love that it's made from recycled materials. Doesn't compromise on style or comfort. Would buy again in other colors."),
                (3, "Average", "Nothing special but nothing bad either. Standard quality, standard fit. Gets the job done for everyday wear."),
                (4, "Nice design", "Clean design, good quality. Fits well after one wash (slight initial tightness is normal). Great value for money."),
            ],
            "home-kitchen": [
                (5, "Game changer!", "Completely changed how I cook. Easy to use, easy to clean, saves so much time. Best kitchen investment ever."),
                (4, "Great but noisy", "Works wonderfully. Results are always consistent. Only downside is it's a bit noisy during operation. Otherwise perfect."),
                (5, "Perfect for small kitchen", "Compact enough for my small kitchen but powerful. Uses it daily for various recipes. Highly recommended."),
                (3, "Took time to figure out", "Initial learning curve was steep. Manual could be better. Once you get the hang of it, it's great though."),
                (5, "Restaurant quality at home", "The results are restaurant quality. Family loves the food. Cleanup is a breeze. Worth every rupee spent."),
                (4, "Solid build quality", "Heavy and well-built. Feels premium. Been using for 6 months with no issues. Some accessories could be better quality."),
                (5, "Energy efficient", "Uses less power than expected. Cooks food perfectly every time. Timer function is very accurate. Silent operation."),
                (2, "Broke after 3 months", "Worked great initially but stopped working after 3 months. Customer service was unhelpful. Disappointed."),
                (4, "Good value for money", "Does what it promises at a fair price. Build quality is good, not exceptional. Easy to maintain and clean."),
                (5, "Best purchase this year", "Honestly the best thing I've bought all year. Makes cooking fun and effortless. Space-saving design too."),
                (4, "Mostly great", "90% of the time it's perfect. Occasionally needs more time than stated. Temperature accuracy is excellent."),
                (3, "Decent but overrated", "It's a solid product but online hype set my expectations too high. It's good, not life-changing. Works as advertised."),
            ],
            "books": [
                (5, "Life changing!", "This book completely changed my perspective. Practical advice that's actually actionable. Read it three times already."),
                (5, "Must read", "Everyone should read this. Concepts are explained clearly with real examples. Engaging writing style keeps you hooked."),
                (4, "Great content, slow start", "First few chapters are slow but it picks up. The core ideas are brilliant and have genuinely helped me."),
                (5, "Gifted to 5 friends", "So good that I bought copies for friends and family. The insights are timeless and applicable to everyone."),
                (4, "Solid advice", "Well-researched with good evidence. Some concepts are obvious but presented in a fresh way. Worth the read."),
                (3, "Overhyped", "Good book with some useful ideas but not the life-changing experience everyone claims. Still worth reading though."),
                (5, "Page turner", "Couldn't put it down. Each chapter builds on the last perfectly. Highlights real stories that make concepts stick."),
                (5, "Best in its category", "I've read many similar books and this stands above all of them. Clear, concise, and incredibly insightful."),
                (4, "Good for beginners", "If you're new to this topic, it's perfect. Some advanced readers might find it basic but the frameworks are solid."),
                (4, "Well written", "Author's writing style is engaging and easy to follow. Good use of anecdotes. Practical takeaways in every chapter."),
                (5, "Reference book", "I keep coming back to this. It's become my reference for decision making. Underlined half the book."),
            ],
            "sports": [
                (5, "Excellent tracking!", "Accurate heart rate, GPS is spot on, and battery lasts the full 7 days. Sleep tracking is insightful too."),
                (4, "Good for the price", "Does everything it claims. Screen could be brighter outdoors. Otherwise great for tracking workouts and sleep."),
                (5, "Perfect workout companion", "Tracks everything I need. Water resistance is great for swimming. Notifications are handy without being intrusive."),
                (3, "Average build quality", "Works fine functionally but the band started peeling after 2 months. Had to buy a replacement band. Tracking is accurate."),
                (4, "Comfortable to wear", "Light and comfortable, forget you're wearing it. Data syncs smoothly. App could be more intuitive though."),
                (5, "Motivating!", "The reminders and goals keep me motivated. Seeing my progress over weeks has pushed me to be more active. Love it."),
                (4, "Reliable tracker", "Using it for 4 months without issues. Battery is consistent. Heart rate accuracy matches my chest strap well."),
                (2, "Connectivity issues", "Keeps disconnecting from my phone. Have to re-pair it frequently. When it works, the data is good though."),
                (5, "Best purchase for fitness", "Since buying this, I've become much more consistent with exercise. The data insights are incredibly useful."),
                (4, "Great features", "Packed with features for the price. GPS could be slightly more accurate in dense areas. Overall very satisfied."),
                (3, "Decent but basic", "Fine for basic tracking but lacks advanced metrics that serious athletes need. Good for casual fitness enthusiasts."),
            ],
            "beauty": [
                (5, "Holy grail product!", "Been using for 3 months and my skin has never looked better. Completely cleared my breakouts. Must-have!"),
                (4, "Works well but slow results", "Took about 6 weeks to see noticeable results. Now my skin is much clearer. Be patient with this one."),
                (5, "Gentle and effective", "Perfect for my sensitive skin. No irritation at all. Reduced redness and pores noticeably within a month."),
                (3, "Caused initial breakout", "First 2 weeks made my skin worse (purging). After that, it improved significantly. Wish I was warned about purging."),
                (5, "Amazing value", "For the price, you can't beat this. Works as well as products 5x more expensive. Texture is lovely on skin."),
                (4, "Good daily routine addition", "Light, absorbs quickly, no residue. I use it morning and night. Skin feels smoother and more even-toned."),
                (5, "Recommend to everyone", "My whole friend group uses this now after seeing my results. Fades dark spots and controls oil brilliantly."),
                (2, "Not for my skin type", "Caused dryness and flaking on my dry skin. Works better for oily skin types. Check your skin type before buying."),
                (4, "Solid product", "Does what it says. No miracles but consistent improvement over time. Good texture, not sticky. Layers well under moisturizer."),
                (5, "Dermatologist recommended", "My dermatologist suggested this and it's been fantastic. Affordable, effective, and gentle. Perfect for daily use."),
                (4, "Nice packaging too", "Product works well and the packaging is minimal and recyclable. Appreciated the eco-friendly approach."),
                (3, "Decent", "Average product. Some improvement in skin texture but nothing dramatic. Maybe I need a higher concentration."),
            ],
        }

        total_reviews = 0
        for product in all_products:
            cat_slug = product.category.slug if product.category else "electronics"
            templates = review_templates.get(cat_slug, review_templates["electronics"])

            for i, (rating, title, body) in enumerate(templates[:12]):
                if i >= len(reviewers):
                    break
                review = Review(
                    product_id=product.id,
                    customer_id=reviewers[i].id,
                    rating=rating,
                    title=title,
                    body=body,
                    verified_purchase=True,
                    sentiment_score=0.8 if rating >= 4 else (0.0 if rating == 3 else -0.5),
                    sentiment_label="positive" if rating >= 4 else ("neutral" if rating == 3 else "negative"),
                    topics=["quality", "value for money"] if rating >= 4 else ["issues"],
                    ai_processed=True,
                )
                if cat_slug == "clothing" and product.available_sizes:
                    review.size_purchased = product.available_sizes[i % len(product.available_sizes)]
                db.session.add(review)
                total_reviews += 1

        db.session.commit()
        print(f"   💬 {total_reviews} reviews created")

        # Generate AI summaries
        from ai_reviews.services import ReviewService
        summaries = 0
        for product in all_products:
            s = ReviewService.generate_product_summary(product.id)
            if s:
                summaries += 1
        print(f"   🤖 {summaries} AI summaries generated")

        print("\n✅ Expanded database seeded!")
        print(f"   🔑 Demo: demo@returnless.ai / demo123")
        print(f"   🛠️  Admin: admin@returnless.ai / admin123")


if __name__ == "__main__":
    seed()
