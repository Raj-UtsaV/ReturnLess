"""Seed database with sample products and categories."""
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
    """Seed the database with sample data."""
    app = create_app()

    with app.app_context():
        print("🌱 Seeding database...")

        # Clear existing data
        db.session.query(Review).delete()
        db.session.query(ReviewSummary).delete()
        db.session.query(SizePurchaseHistory).delete()
        db.session.query(Warehouse).delete()
        db.session.query(Product).delete()
        db.session.query(Category).delete()
        db.session.query(Customer).delete()
        db.session.commit()

        # --- Categories ---
        categories_data = [
            {"name": "Electronics", "slug": "electronics", "icon": "💻", "description": "Phones, laptops, and gadgets"},
            {"name": "Clothing", "slug": "clothing", "icon": "👕", "description": "Fashion and apparel"},
            {"name": "Home & Kitchen", "slug": "home-kitchen", "icon": "🏠", "description": "Home essentials"},
            {"name": "Books", "slug": "books", "icon": "📚", "description": "Books and publications"},
            {"name": "Sports", "slug": "sports", "icon": "⚽", "description": "Sports and outdoors"},
            {"name": "Beauty", "slug": "beauty", "icon": "✨", "description": "Beauty and personal care"},
        ]

        categories = {}
        for cat_data in categories_data:
            cat = Category(**cat_data)
            db.session.add(cat)
            categories[cat_data["slug"]] = cat

        db.session.flush()

        # --- Products ---
        products_data = [
            # Electronics - Standard
            {
                "name": "Samsung Galaxy S24 Ultra - 256GB Titanium Black",
                "slug": "samsung-galaxy-s24-ultra-256gb",
                "description": "Experience the future with Galaxy AI. The Samsung Galaxy S24 Ultra features a 6.8-inch Dynamic AMOLED 2X display, Snapdragon 8 Gen 3 processor, 200MP camera system, and integrated S Pen. AI-powered features include Circle to Search, Live Translate, and Note Assist.",
                "short_description": "AI-powered flagship with 200MP camera and S Pen",
                "price": 129999,
                "original_price": 134999,
                "category_id": None,  # Set below
                "category_slug": "electronics",
                "brand": "Samsung",
                "sku": "SAM-S24U-256-BLK",
                "stock_quantity": 25,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400",
                "delivery_days_min": 2,
                "delivery_days_max": 4,
                "free_delivery": True,
                "green_credits_earn": 20,
                "avg_rating": 4.6,
                "total_reviews": 1247,
                "specifications": {"Display": "6.8\" QHD+ Dynamic AMOLED 2X", "Processor": "Snapdragon 8 Gen 3", "RAM": "12GB", "Storage": "256GB", "Battery": "5000mAh", "Camera": "200MP + 12MP + 50MP + 10MP"},
            },
            {
                "name": "Apple MacBook Air M3 - 15 inch Space Gray",
                "slug": "apple-macbook-air-m3-15-inch",
                "description": "Strikingly thin design powered by M3 chip. The 15-inch MacBook Air delivers exceptional performance and battery life in an impossibly thin design. Features Liquid Retina display, 18-hour battery life, MagSafe charging, and 1080p FaceTime HD camera.",
                "short_description": "Ultra-thin 15\" laptop with M3 chip and 18hr battery",
                "price": 149900,
                "original_price": 149900,
                "category_slug": "electronics",
                "brand": "Apple",
                "sku": "APL-MBA-M3-15-GRY",
                "stock_quantity": 15,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 5,
                "free_delivery": True,
                "green_credits_earn": 20,
                "avg_rating": 4.8,
                "total_reviews": 892,
                "eco_friendly": True,
                "specifications": {"Display": "15.3\" Liquid Retina", "Chip": "Apple M3", "RAM": "8GB Unified", "Storage": "256GB SSD", "Battery": "Up to 18 hours", "Weight": "1.51 kg"},
            },
            # Electronics - Refurbished
            {
                "name": "Apple iPhone 14 Pro Max - 128GB (Certified Refurbished)",
                "slug": "apple-iphone-14-pro-max-refurbished",
                "description": "Certified refurbished iPhone 14 Pro Max in excellent condition. Features Dynamic Island, 48MP camera system, A16 Bionic chip, and ProMotion display. Thoroughly inspected, tested, and restored to like-new condition with full warranty.",
                "short_description": "Like-new iPhone 14 Pro Max with full warranty",
                "price": 79999,
                "original_price": 139900,
                "category_slug": "electronics",
                "brand": "Apple",
                "sku": "APL-14PM-128-REFURB",
                "stock_quantity": 8,
                "product_type": "refurbished",
                "thumbnail": "https://images.unsplash.com/photo-1678685888221-cda773a3dcdb?w=400",
                "delivery_days_min": 2,
                "delivery_days_max": 5,
                "free_delivery": True,
                "green_credits_earn": 50,
                "avg_rating": 4.5,
                "total_reviews": 342,
                "grade": "A",
                "warranty_months": 12,
                "carbon_saved_kg": 72.5,
                "refurb_reason": "Customer return - unopened",
                "inspection_notes": "Device in pristine condition. Battery health 100%. All functions tested and verified. Original accessories included.",
                "refurbished_by": "ReturnLess Certified Labs",
                "specifications": {"Display": "6.7\" Super Retina XDR", "Chip": "A16 Bionic", "Storage": "128GB", "Camera": "48MP + 12MP + 12MP", "Battery": "Up to 29hr video"},
            },
            {
                "name": "Sony WH-1000XM5 Noise Cancelling Headphones (Refurbished)",
                "slug": "sony-wh-1000xm5-refurbished",
                "description": "Premium noise-cancelling headphones restored to excellent condition. Industry-leading noise cancellation with 8 microphones, 30-hour battery life, crystal clear hands-free calling, and multipoint connection. Speak-to-Chat auto pauses music.",
                "short_description": "Industry-leading ANC headphones, restored like-new",
                "price": 17999,
                "original_price": 29990,
                "category_slug": "electronics",
                "brand": "Sony",
                "sku": "SONY-XM5-BLK-REFURB",
                "stock_quantity": 12,
                "product_type": "refurbished",
                "thumbnail": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 5,
                "free_delivery": True,
                "green_credits_earn": 50,
                "avg_rating": 4.7,
                "total_reviews": 567,
                "grade": "A",
                "warranty_months": 6,
                "carbon_saved_kg": 8.3,
                "refurb_reason": "Open-box return",
                "inspection_notes": "Minimal signs of use. ANC tested at full performance. Battery holds rated charge. All pads replaced with new ones.",
                "refurbished_by": "ReturnLess Certified Labs",
                "specifications": {"Type": "Over-ear wireless", "ANC": "Industry-leading", "Battery": "30 hours", "Driver": "30mm", "Weight": "250g"},
            },
            # Clothing
            {
                "name": "Nike Dri-FIT Running T-Shirt - Men's",
                "slug": "nike-dri-fit-running-tshirt-mens",
                "description": "Lightweight Dri-FIT technology wicks sweat away from your body for a comfortable, dry fit. Made with at least 75% recycled polyester fiber. Features reflective details for low-light visibility and standard fit for a relaxed, easy feel.",
                "short_description": "Lightweight moisture-wicking running tee",
                "price": 2495,
                "original_price": 2995,
                "category_slug": "clothing",
                "brand": "Nike",
                "sku": "NIKE-DRIFIT-RUN-M-BLK",
                "stock_quantity": 50,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 6,
                "free_delivery": False,
                "green_credits_earn": 20,
                "avg_rating": 4.4,
                "total_reviews": 2156,
                "eco_friendly": True,
                "available_sizes": ["S", "M", "L", "XL", "XXL"],
                "color": "Black",
                "specifications": {"Material": "75% Recycled Polyester", "Fit": "Standard", "Neckline": "Crew", "Sleeve": "Short"},
            },
            {
                "name": "Levi's 511 Slim Fit Jeans - Dark Indigo",
                "slug": "levis-511-slim-fit-jeans-dark-indigo",
                "description": "The 511 Slim Fit sits below the waist with a slim fit through the hip and thigh for a classic look. Made with Water<Less technology using significantly less water in production. Stretch denim for all-day comfort.",
                "short_description": "Classic slim fit jeans with sustainable production",
                "price": 3999,
                "original_price": 4599,
                "category_slug": "clothing",
                "brand": "Levi's",
                "sku": "LEVIS-511-SLIM-IND-32",
                "stock_quantity": 35,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
                "delivery_days_min": 4,
                "delivery_days_max": 7,
                "free_delivery": False,
                "green_credits_earn": 20,
                "avg_rating": 4.3,
                "total_reviews": 1834,
                "eco_friendly": True,
                "available_sizes": ["28", "30", "32", "34", "36", "38"],
                "color": "Dark Indigo",
                "specifications": {"Material": "99% Cotton, 1% Elastane", "Fit": "Slim", "Rise": "Mid Rise", "Technology": "Water<Less™"},
            },
            # Home & Kitchen
            {
                "name": "Dyson V15 Detect Absolute Vacuum Cleaner",
                "slug": "dyson-v15-detect-absolute-vacuum",
                "description": "The most powerful, intelligent cordless vacuum. Laser reveals invisible dust. Piezo sensor counts and sizes particles, automatically adjusting suction. LCD screen shows scientific proof of a deep clean. Up to 60 minutes of fade-free power.",
                "short_description": "Laser-guided intelligent cordless vacuum",
                "price": 52900,
                "original_price": 58900,
                "category_slug": "home-kitchen",
                "brand": "Dyson",
                "sku": "DYS-V15-DET-ABS",
                "stock_quantity": 7,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 6,
                "free_delivery": True,
                "green_credits_earn": 20,
                "avg_rating": 4.7,
                "total_reviews": 423,
                "specifications": {"Type": "Cordless Stick", "Suction": "230 AW", "Runtime": "Up to 60 min", "Bin Volume": "0.76L", "Weight": "3.1kg"},
            },
            {
                "name": "Instant Pot Duo Plus 6-Quart (Certified Refurbished)",
                "slug": "instant-pot-duo-plus-6qt-refurbished",
                "description": "The best-selling multi-cooker restored to factory condition. 9-in-1 functionality: pressure cooker, slow cooker, rice cooker, steamer, sauté, yogurt maker, warmer, sterilizer, and sous vide. Safety-tested and quality verified.",
                "short_description": "9-in-1 multi-cooker restored to factory condition",
                "price": 5499,
                "original_price": 9999,
                "category_slug": "home-kitchen",
                "brand": "Instant Pot",
                "sku": "IP-DUO-PLUS-6Q-REFURB",
                "stock_quantity": 20,
                "product_type": "refurbished",
                "thumbnail": "https://images.unsplash.com/photo-1585515320310-259814833e62?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 5,
                "free_delivery": True,
                "green_credits_earn": 50,
                "avg_rating": 4.6,
                "total_reviews": 789,
                "grade": "B",
                "warranty_months": 6,
                "carbon_saved_kg": 15.2,
                "refurb_reason": "Minor cosmetic wear",
                "inspection_notes": "Small scratch on lid (cosmetic only). All pressure tests passed. Sealing ring replaced with new. All accessories included.",
                "refurbished_by": "ReturnLess Certified Labs",
                "specifications": {"Capacity": "6 Quart", "Functions": "9-in-1", "Power": "1000W", "Material": "Stainless Steel"},
            },
            # Books
            {
                "name": "Atomic Habits by James Clear - Hardcover",
                "slug": "atomic-habits-james-clear-hardcover",
                "description": "An Easy & Proven Way to Build Good Habits & Break Bad Ones. No matter your goals, Atomic Habits offers a proven framework for improving every day. James Clear reveals practical strategies that will teach you how to form good habits, break bad ones, and master the tiny behaviors that lead to remarkable results.",
                "short_description": "Transform your life with tiny changes that deliver big results",
                "price": 599,
                "original_price": 799,
                "category_slug": "books",
                "brand": "Penguin Random House",
                "sku": "BK-ATOMIC-HABITS-HC",
                "stock_quantity": 100,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
                "delivery_days_min": 2,
                "delivery_days_max": 4,
                "free_delivery": True,
                "green_credits_earn": 20,
                "avg_rating": 4.8,
                "total_reviews": 5621,
                "specifications": {"Author": "James Clear", "Pages": "320", "Publisher": "Penguin Random House", "ISBN": "9780735211292", "Format": "Hardcover"},
            },
            # Sports
            {
                "name": "Fitbit Charge 6 Fitness Tracker - Obsidian",
                "slug": "fitbit-charge-6-fitness-tracker",
                "description": "Advanced health and fitness tracker with built-in GPS, heart rate monitoring, sleep tracking, and stress management tools. Google integration with Maps, Wallet, and YouTube Music controls. Water resistant to 50m with 7-day battery life.",
                "short_description": "Advanced fitness tracker with Google integration",
                "price": 14999,
                "original_price": 14999,
                "category_slug": "sports",
                "brand": "Fitbit",
                "sku": "FIT-CHARGE6-OBS",
                "stock_quantity": 30,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 5,
                "free_delivery": True,
                "green_credits_earn": 20,
                "avg_rating": 4.3,
                "total_reviews": 1102,
                "specifications": {"Display": "AMOLED touchscreen", "Battery": "7 days", "Water Resistance": "50m", "Sensors": "HR, SpO2, EDA, Skin Temp", "GPS": "Built-in"},
            },
            # Beauty
            {
                "name": "The Ordinary Niacinamide 10% + Zinc 1% Serum",
                "slug": "the-ordinary-niacinamide-zinc-serum",
                "description": "High-strength vitamin and mineral formula to help reduce the appearance of blemishes and congestion. Niacinamide (Vitamin B3) helps reduce the appearance of skin blemishes and congestion. Zinc PCA helps balance visible sebum activity.",
                "short_description": "Blemish-fighting serum with 10% Niacinamide",
                "price": 590,
                "original_price": 590,
                "category_slug": "beauty",
                "brand": "The Ordinary",
                "sku": "TO-NIACINAMIDE-30ML",
                "stock_quantity": 75,
                "product_type": "standard",
                "thumbnail": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400",
                "delivery_days_min": 2,
                "delivery_days_max": 4,
                "free_delivery": False,
                "green_credits_earn": 20,
                "avg_rating": 4.5,
                "total_reviews": 3421,
                "eco_friendly": True,
                "specifications": {"Volume": "30ml", "Key Ingredients": "Niacinamide 10%, Zinc PCA 1%", "Skin Type": "All", "Vegan": "Yes", "Cruelty Free": "Yes"},
            },
            # Another refurbished
            {
                "name": "Dell XPS 15 Laptop - i7/16GB/512GB (Certified Refurbished)",
                "slug": "dell-xps-15-i7-refurbished",
                "description": "Premium ultrabook restored to excellent condition. Features 15.6-inch OLED 3.5K InfinityEdge display, Intel Core i7-13700H, 16GB RAM, 512GB SSD, and NVIDIA RTX 4050. Professional grade for creators and power users.",
                "short_description": "Premium creator laptop with OLED display, restored",
                "price": 89999,
                "original_price": 159990,
                "category_slug": "electronics",
                "brand": "Dell",
                "sku": "DELL-XPS15-I7-REFURB",
                "stock_quantity": 5,
                "product_type": "refurbished",
                "thumbnail": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400",
                "delivery_days_min": 3,
                "delivery_days_max": 6,
                "free_delivery": True,
                "green_credits_earn": 50,
                "avg_rating": 4.6,
                "total_reviews": 234,
                "grade": "A",
                "warranty_months": 12,
                "carbon_saved_kg": 320.0,
                "refurb_reason": "Corporate lease return",
                "inspection_notes": "Excellent condition from corporate environment. Battery cycle count: 47. All ports tested. Fresh OS install. Minor desk marks on bottom panel.",
                "refurbished_by": "ReturnLess Certified Labs",
                "specifications": {"Display": "15.6\" 3.5K OLED", "Processor": "Intel Core i7-13700H", "RAM": "16GB DDR5", "Storage": "512GB NVMe SSD", "GPU": "NVIDIA RTX 4050 6GB", "Weight": "1.86kg"},
            },
        ]

        for p_data in products_data:
            category_slug = p_data.pop("category_slug")
            p_data.pop("category_id", None)
            p_data["category_id"] = categories[category_slug].id
            product = Product(**p_data)
            db.session.add(product)

        # --- Sample Customers ---
        customers_data = [
            {
                "email": "demo@returnless.ai",
                "password": "demo123",
                "first_name": "Demo",
                "last_name": "User",
                "green_credits": 250,
                "lifetime_credits": 250,
            },
            {
                "email": "admin@returnless.ai",
                "password": "admin123",
                "first_name": "Admin",
                "last_name": "User",
                "green_credits": 5000,
                "lifetime_credits": 5000,
                "is_admin": True,
            },
        ]

        for c_data in customers_data:
            password = c_data.pop("password")
            customer = Customer(**c_data)
            customer.set_password(password)
            db.session.add(customer)

        db.session.flush()

        # --- Warehouses (covering all product origin cities) ---
        warehouses_data = [
            {"name": "Mumbai Central Hub", "code": "MUM-01", "city": "Mumbai", "state": "Maharashtra", "capacity": 500, "current_load": 180, "specialization": "electronics", "avg_processing_days": 1.5},
            {"name": "Delhi NCR Fulfillment", "code": "DEL-01", "city": "Delhi", "state": "Delhi", "capacity": 600, "current_load": 320, "specialization": "general", "avg_processing_days": 2.0},
            {"name": "Bangalore Tech Center", "code": "BLR-01", "city": "Bangalore", "state": "Karnataka", "capacity": 400, "current_load": 150, "specialization": "electronics", "avg_processing_days": 1.8},
            {"name": "Hyderabad Logistics Park", "code": "HYD-01", "city": "Hyderabad", "state": "Telangana", "capacity": 350, "current_load": 120, "specialization": "electronics", "avg_processing_days": 2.0},
            {"name": "Chennai South Center", "code": "CHE-01", "city": "Chennai", "state": "Tamil Nadu", "capacity": 350, "current_load": 200, "specialization": "clothing", "avg_processing_days": 2.2},
            {"name": "Kolkata East Hub", "code": "KOL-01", "city": "Kolkata", "state": "West Bengal", "capacity": 300, "current_load": 90, "specialization": "clothing", "avg_processing_days": 2.5},
            {"name": "Pune West Warehouse", "code": "PUN-01", "city": "Pune", "state": "Maharashtra", "capacity": 300, "current_load": 110, "specialization": "home-kitchen", "avg_processing_days": 1.8},
            {"name": "Ahmedabad Distribution", "code": "AMD-01", "city": "Ahmedabad", "state": "Gujarat", "capacity": 250, "current_load": 80, "specialization": "home-kitchen", "avg_processing_days": 2.3},
            {"name": "Jaipur North Hub", "code": "JAI-01", "city": "Jaipur", "state": "Rajasthan", "capacity": 200, "current_load": 60, "specialization": "general", "avg_processing_days": 2.5},
            {"name": "Lucknow Central", "code": "LKO-01", "city": "Lucknow", "state": "Uttar Pradesh", "capacity": 250, "current_load": 95, "specialization": "general", "avg_processing_days": 2.8},
            {"name": "Surat Textile Hub", "code": "SUR-01", "city": "Surat", "state": "Gujarat", "capacity": 200, "current_load": 70, "specialization": "clothing", "avg_processing_days": 2.0},
            {"name": "Bhopal Central Warehouse", "code": "BPL-01", "city": "Bhopal", "state": "Madhya Pradesh", "capacity": 200, "current_load": 45, "specialization": "electronics", "avg_processing_days": 3.0},
        ]
        for wh_data in warehouses_data:
            wh = Warehouse(**wh_data)
            db.session.add(wh)

        db.session.flush()
        print(f"   🏭 {len(warehouses_data)} warehouses created")

        # --- Sample Reviewer Customers ---
        reviewer_customers = []
        reviewer_data = [
            {"email": "priya.sharma@example.com", "first_name": "Priya", "last_name": "Sharma"},
            {"email": "rahul.kumar@example.com", "first_name": "Rahul", "last_name": "Kumar"},
            {"email": "anita.patel@example.com", "first_name": "Anita", "last_name": "Patel"},
            {"email": "vikram.singh@example.com", "first_name": "Vikram", "last_name": "Singh"},
            {"email": "sneha.reddy@example.com", "first_name": "Sneha", "last_name": "Reddy"},
            {"email": "arjun.nair@example.com", "first_name": "Arjun", "last_name": "Nair"},
            {"email": "meera.gupta@example.com", "first_name": "Meera", "last_name": "Gupta"},
            {"email": "karthik.iyer@example.com", "first_name": "Karthik", "last_name": "Iyer"},
        ]
        for rc_data in reviewer_data:
            rc = Customer(green_credits=50, lifetime_credits=50, **rc_data)
            rc.set_password("reviewer123")
            db.session.add(rc)
            reviewer_customers.append(rc)

        db.session.flush()

        # --- Sample Reviews ---
        # Get first product (Samsung Galaxy)
        samsung = Product.query.filter_by(sku="SAM-S24U-256-BLK").first()
        nike_shirt = Product.query.filter_by(sku="NIKE-DRIFIT-RUN-M-BLK").first()
        iphone_refurb = Product.query.filter_by(sku="APL-14PM-128-REFURB").first()

        reviews_seed = []

        if samsung:
            reviews_seed.extend([
                {
                    "product_id": samsung.id,
                    "customer_id": reviewer_customers[0].id,
                    "rating": 5,
                    "title": "Best Android phone I've ever used",
                    "body": "The S24 Ultra is absolutely incredible. The display is stunning - colors are vibrant and the 120Hz refresh rate makes everything buttery smooth. Battery life easily lasts a full day with heavy use. The camera system is phenomenal, especially the 200MP main sensor. AI features like Circle to Search are genuinely useful. The S Pen is a nice bonus for note-taking. Worth every rupee!",
                    "verified_purchase": True,
                    "sentiment_score": 0.9,
                    "sentiment_label": "positive",
                    "topics": ["screen display", "battery life", "camera quality", "performance speed"],
                    "ai_processed": True,
                },
                {
                    "product_id": samsung.id,
                    "customer_id": reviewer_customers[1].id,
                    "rating": 4,
                    "title": "Great phone but heavy",
                    "body": "Performance is blazing fast, camera is excellent especially in low light. The AI features are interesting but still a bit gimmicky. My only complaint is the weight - it's quite heavy for daily use and the edges can feel uncomfortable during long calls. Battery life is good though, easily gets through the day.",
                    "verified_purchase": True,
                    "sentiment_score": 0.5,
                    "sentiment_label": "positive",
                    "topics": ["performance speed", "camera quality", "comfort fit", "battery life"],
                    "ai_processed": True,
                },
                {
                    "product_id": samsung.id,
                    "customer_id": reviewer_customers[2].id,
                    "rating": 5,
                    "title": "Photography beast",
                    "body": "I bought this primarily for the camera and I'm blown away. The 200MP sensor captures incredible detail. Night mode is phenomenal. The 100x Space Zoom is actually usable unlike previous generations. Build quality is premium - feels like holding a premium device. Fast charging is a lifesaver.",
                    "verified_purchase": True,
                    "sentiment_score": 0.85,
                    "sentiment_label": "positive",
                    "topics": ["camera quality", "build quality", "design looks"],
                    "ai_processed": True,
                },
                {
                    "product_id": samsung.id,
                    "customer_id": reviewer_customers[3].id,
                    "rating": 3,
                    "title": "Overpriced for what you get",
                    "body": "It's a good phone but at this price point I expected more. The AI features feel half-baked and the software can be laggy sometimes. Battery drain is noticeable when using 5G. Camera is great though. Value for money isn't the best - you're paying a premium for the brand.",
                    "verified_purchase": True,
                    "sentiment_score": -0.1,
                    "sentiment_label": "neutral",
                    "topics": ["value for money", "performance speed", "battery life"],
                    "ai_processed": True,
                },
                {
                    "product_id": samsung.id,
                    "customer_id": reviewer_customers[4].id,
                    "rating": 5,
                    "title": "Upgraded from S22 - no regrets",
                    "body": "Coming from S22 Ultra, this is a massive upgrade. Everything is faster, the display is brighter, camera is significantly better. Love the flat screen design. S Pen integration is seamless. The titanium frame gives it a premium feel. Highly recommend for anyone looking for the best Android experience.",
                    "verified_purchase": True,
                    "sentiment_score": 0.88,
                    "sentiment_label": "positive",
                    "topics": ["performance speed", "screen display", "design looks", "build quality"],
                    "ai_processed": True,
                },
            ])

        if nike_shirt:
            reviews_seed.extend([
                {
                    "product_id": nike_shirt.id,
                    "customer_id": reviewer_customers[0].id,
                    "rating": 5,
                    "title": "Perfect running companion",
                    "body": "Incredibly lightweight and comfortable. The Dri-FIT material works amazing - keeps you dry even during intense workouts. Fits true to size. I ordered M and it's perfect. The recycled material angle is a bonus. Great for both gym and outdoor runs.",
                    "verified_purchase": True,
                    "size_purchased": "M",
                    "sentiment_score": 0.85,
                    "sentiment_label": "positive",
                    "topics": ["comfort fit", "material quality", "value for money"],
                    "ai_processed": True,
                },
                {
                    "product_id": nike_shirt.id,
                    "customer_id": reviewer_customers[5].id,
                    "rating": 4,
                    "title": "Good but runs slightly small",
                    "body": "Nice shirt, moisture-wicking works great. However, it runs a bit small compared to other Nike shirts. I usually wear L but this felt tight around the shoulders. Recommend sizing up if you want a relaxed fit. Material quality is excellent.",
                    "verified_purchase": True,
                    "size_purchased": "L",
                    "sentiment_score": 0.4,
                    "sentiment_label": "positive",
                    "topics": ["comfort fit", "material quality"],
                    "ai_processed": True,
                },
                {
                    "product_id": nike_shirt.id,
                    "customer_id": reviewer_customers[6].id,
                    "rating": 4,
                    "title": "Great for hot weather",
                    "body": "Perfect for summer runs. Very breathable and quick drying. The fit is a little snug compared to regular Nike tees - I'd say it runs small. Got M but might try L next time. Otherwise excellent quality and the eco-friendly material is a nice touch.",
                    "verified_purchase": True,
                    "size_purchased": "M",
                    "sentiment_score": 0.5,
                    "sentiment_label": "positive",
                    "topics": ["comfort fit", "material quality"],
                    "ai_processed": True,
                },
                {
                    "product_id": nike_shirt.id,
                    "customer_id": reviewer_customers[7].id,
                    "rating": 5,
                    "title": "Love everything about this",
                    "body": "Fantastic running shirt. True to size for me (XL), incredibly comfortable during long runs. Dries super fast after washing too. The reflective details are a nice safety feature for evening runs. Will buy more colors!",
                    "verified_purchase": True,
                    "size_purchased": "XL",
                    "sentiment_score": 0.9,
                    "sentiment_label": "positive",
                    "topics": ["comfort fit", "ease of use", "durability"],
                    "ai_processed": True,
                },
            ])

        if iphone_refurb:
            reviews_seed.extend([
                {
                    "product_id": iphone_refurb.id,
                    "customer_id": reviewer_customers[1].id,
                    "rating": 5,
                    "title": "Like brand new - amazing value!",
                    "body": "Cannot believe this is refurbished. Phone looks and works like brand new. Battery health at 100%, not a single scratch. Dynamic Island is cool. Camera is outstanding. Saved almost 60k compared to new price. The 12-month warranty gives peace of mind. ReturnLess's refurbishment quality is impressive!",
                    "verified_purchase": True,
                    "sentiment_score": 0.92,
                    "sentiment_label": "positive",
                    "topics": ["value for money", "build quality", "camera quality"],
                    "ai_processed": True,
                },
                {
                    "product_id": iphone_refurb.id,
                    "customer_id": reviewer_customers[3].id,
                    "rating": 4,
                    "title": "Great refurb, minor nitpick",
                    "body": "Overall excellent condition. Performance is identical to new. Battery is perfect. The only thing - the box doesn't have original Apple packaging (expected for refurb). Everything else is perfect. The savings are substantial and you're helping the environment. Win-win!",
                    "verified_purchase": True,
                    "sentiment_score": 0.6,
                    "sentiment_label": "positive",
                    "topics": ["value for money", "performance speed", "delivery packaging"],
                    "ai_processed": True,
                },
                {
                    "product_id": iphone_refurb.id,
                    "customer_id": reviewer_customers[5].id,
                    "rating": 5,
                    "title": "Eco-friendly and wallet-friendly",
                    "body": "Bought this to reduce e-waste and save money. Mission accomplished on both fronts! Phone is pristine, all features work perfectly. Camera takes stunning photos. Love that I saved 72kg of CO2 by choosing refurbished. More people should consider this option.",
                    "verified_purchase": True,
                    "sentiment_score": 0.88,
                    "sentiment_label": "positive",
                    "topics": ["value for money", "camera quality", "ease of use"],
                    "ai_processed": True,
                },
            ])

        for r_data in reviews_seed:
            review = Review(**r_data)
            db.session.add(review)

        db.session.commit()

        # --- Size Purchase History for Demo User ---
        demo_customer = Customer.query.filter_by(email="demo@returnless.ai").first()
        clothing_cat = Category.query.filter_by(slug="clothing").first()

        if demo_customer and clothing_cat and nike_shirt:
            size_history_data = [
                # Demo user buys M consistently and keeps them
                {"customer_id": demo_customer.id, "product_id": nike_shirt.id, "category_id": clothing_cat.id, "size_purchased": "M", "brand": "Nike", "kept": True},
                {"customer_id": demo_customer.id, "product_id": nike_shirt.id, "category_id": clothing_cat.id, "size_purchased": "M", "brand": "Nike", "kept": True},
                {"customer_id": demo_customer.id, "product_id": nike_shirt.id, "category_id": clothing_cat.id, "size_purchased": "M", "brand": "Adidas", "kept": True},
                {"customer_id": demo_customer.id, "product_id": nike_shirt.id, "category_id": clothing_cat.id, "size_purchased": "L", "brand": "Nike", "kept": False, "return_reason": "too_large"},
                {"customer_id": demo_customer.id, "product_id": nike_shirt.id, "category_id": clothing_cat.id, "size_purchased": "M", "brand": "Levi's", "kept": True},
            ]
            for sh_data in size_history_data:
                sh = SizePurchaseHistory(**sh_data)
                db.session.add(sh)
            db.session.commit()
            print(f"   📏 {len(size_history_data)} size history records created")

        # --- Generate AI Summaries ---
        from ai_reviews.services import ReviewService

        products_with_reviews = set(r["product_id"] for r in reviews_seed)
        summaries_generated = 0
        for pid in products_with_reviews:
            summary = ReviewService.generate_product_summary(pid)
            if summary:
                summaries_generated += 1

        print("✅ Database seeded successfully!")
        print(f"   📦 {len(products_data)} products created")
        print(f"   📁 {len(categories_data)} categories created")
        print(f"   👤 {len(customers_data) + len(reviewer_data)} customers created")
        print(f"   💬 {len(reviews_seed)} reviews created")
        print(f"   🤖 {summaries_generated} AI summaries generated")
        print()
        print("   🔑 Demo account: demo@returnless.ai / demo123")
        print("   🛠️  Admin account: admin@returnless.ai / admin123")


if __name__ == "__main__":
    seed()
