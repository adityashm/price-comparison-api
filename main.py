from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
from typing import List, Optional
import random

app = FastAPI(
    title="Price Comparison API",
    description="Find the best deals across e-commerce platforms",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for products
MOCK_PRODUCTS = {
    "laptop": [
        {"platform": "Amazon", "price": 45999, "url": "https://amazon.in"},
        {"platform": "Flipkart", "price": 43999, "url": "https://flipkart.com"},
        {"platform": "eBay", "price": 44500, "url": "https://ebay.com"}
    ],
    "phone": [
        {"platform": "Amazon", "price": 29999, "url": "https://amazon.in"},
        {"platform": "Flipkart", "price": 27999, "url": "https://flipkart.com"},
        {"platform": "eBay", "price": 28500, "url": "https://ebay.com"}
    ],
    "headphones": [
        {"platform": "Amazon", "price": 3999, "url": "https://amazon.in"},
        {"platform": "Flipkart", "price": 3499, "url": "https://flipkart.com"},
        {"platform": "eBay", "price": 3800, "url": "https://ebay.com"}
    ],
    "monitor": [
        {"platform": "Amazon", "price": 15999, "url": "https://amazon.in"},
        {"platform": "Flipkart", "price": 14999, "url": "https://flipkart.com"},
        {"platform": "eBay", "price": 15500, "url": "https://ebay.com"}
    ],
    "keyboard": [
        {"platform": "Amazon", "price": 5999, "url": "https://amazon.in"},
        {"platform": "Flipkart", "price": 4999, "url": "https://flipkart.com"},
        {"platform": "eBay", "price": 5500, "url": "https://ebay.com"}
    ]
}

# Database initialization
def init_db():
    try:
        conn = sqlite3.connect('prices.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                platform TEXT,
                price REAL,
                url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                target_price REAL,
                user_email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database init warning: {e}")

init_db()

# Pydantic models
class Product(BaseModel):
    name: str
    category: str = "General"

class PriceAlert(BaseModel):
    product_id: int
    target_price: float
    user_email: str

class ProductPrice(BaseModel):
    platform: str
    price: float
    url: str

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Price Comparison & Deal Finder API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/search")
async def search_product(q: str):
    """Search for a product across platforms"""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    
    q_lower = q.lower()
    
    # Find matching products
    matching = []
    for key, prices in MOCK_PRODUCTS.items():
        if q_lower in key or key in q_lower:
            lowest = min(prices, key=lambda x: x["price"])
            matching.append({
                "id": hash(key) % 1000,
                "name": key.capitalize(),
                "lowest_price": lowest["price"],
                "platform": lowest["platform"],
                "url": lowest["url"],
                "all_prices": prices
            })
    
    if not matching:
        # Return random products if no match
        key = random.choice(list(MOCK_PRODUCTS.keys()))
        prices = MOCK_PRODUCTS[key]
        lowest = min(prices, key=lambda x: x["price"])
        return [{
            "id": hash(key) % 1000,
            "name": key.capitalize(),
            "lowest_price": lowest["price"],
            "platform": lowest["platform"],
            "url": lowest["url"],
            "all_prices": prices
        }]
    
    return matching

@app.get("/api/products")
async def get_all_products():
    """Get all products with their best prices"""
    products = []
    for name, prices in MOCK_PRODUCTS.items():
        lowest = min(prices, key=lambda x: x["price"])
        products.append({
            "id": hash(name) % 1000,
            "name": name.capitalize(),
            "lowest_price": lowest["price"],
            "platform": lowest["platform"],
            "url": lowest["url"]
        })
    return products

@app.get("/api/deals")
async def get_best_deals():
    """Get current best deals"""
    deals = []
    for name, prices in MOCK_PRODUCTS.items():
        best = min(prices, key=lambda x: x["price"])
        deals.append({
            "id": hash(name) % 1000,
            "name": name.capitalize(),
            "price": best["price"],
            "platform": best["platform"],
            "savings": "Up to 15% off"
        })
    return sorted(deals, key=lambda x: x["price"])[:5]

@app.post("/api/alerts")
async def create_price_alert(alert: PriceAlert):
    """Create a price alert"""
    try:
        conn = sqlite3.connect('prices.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO price_alerts (product_id, target_price, user_email)
            VALUES (?, ?, ?)
        ''', (alert.product_id, alert.target_price, alert.user_email))
        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": alert_id,
            "status": "created",
            "message": f"Alert set for ${alert.target_price}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
