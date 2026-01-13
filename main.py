from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import requests
from bs4 import BeautifulSoup
import asyncio
from typing import List, Optional
import json

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

# Database initialization
def init_db():
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

init_db()

# Pydantic models
class Product(BaseModel):
    name: str
    category: str = "General"

class PriceAlert(BaseModel):
    product_id: int
    target_price: float
    user_email: str

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    lowest_price: float
    platform: str
    url: str
    price_trend: List[float]

# Web scraping functions
def scrape_amazon(product_name: str):
    """Scrape Amazon for product prices"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        search_url = f"https://www.amazon.in/s?k={product_name}"
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Mock data for demo (actual scraping would extract from page)
        return {
            'platform': 'Amazon',
            'price': 5999.00,
            'url': search_url
        }
    except Exception as e:
        return None

def scrape_flipkart(product_name: str):
    """Scrape Flipkart for product prices"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        search_url = f"https://www.flipkart.com/search?q={product_name}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        # Mock data for demo
        return {
            'platform': 'Flipkart',
            'price': 5499.00,
            'url': search_url
        }
    except Exception as e:
        return None

def get_price_trend(product_id: int) -> List[float]:
    """Get 7-day price trend for a product"""
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    week_ago = datetime.now() - timedelta(days=7)
    cursor.execute('''
        SELECT AVG(price) FROM prices 
        WHERE product_id = ? AND timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY timestamp DESC
        LIMIT 7
    ''', (product_id, week_ago))
    
    prices = [row[0] for row in cursor.fetchall()]
    conn.close()
    return prices[::-1]  # Return in ascending order

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Price Comparison & Deal Finder API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search?q=product_name",
            "products": "/api/products",
            "prices": "/api/prices/{product_id}",
            "alerts": "/api/alerts"
        }
    }

@app.get("/api/search")
async def search_product(q: str, background_tasks: BackgroundTasks):
    """Search for a product across platforms"""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    # Check if product exists
    cursor.execute('SELECT id FROM products WHERE name ILIKE ?', (f'%{q}%',))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute('INSERT INTO products (name, category) VALUES (?, ?)', (q, 'General'))
        conn.commit()
        product_id = cursor.lastrowid
    else:
        product_id = existing[0]
    
    # Scrape prices (in background)
    def scrape_all_platforms():
        results = []
        
        amazon = scrape_amazon(q)
        if amazon:
            results.append(amazon)
            cursor.execute(
                'INSERT INTO prices (product_id, platform, price, url) VALUES (?, ?, ?, ?)',
                (product_id, amazon['platform'], amazon['price'], amazon['url'])
            )
        
        flipkart = scrape_flipkart(q)
        if flipkart:
            results.append(flipkart)
            cursor.execute(
                'INSERT INTO prices (product_id, platform, price, url) VALUES (?, ?, ?, ?)',
                (product_id, flipkart['platform'], flipkart['price'], flipkart['url'])
            )
        
        conn.commit()
    
    background_tasks.add_task(scrape_all_platforms)
    
    conn.close()
    
    return {
        "product_id": product_id,
        "query": q,
        "message": "Searching across platforms...",
        "status": "in_progress"
    }

@app.get("/api/products")
async def get_all_products():
    """Get all products with their best prices"""
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.category, MIN(pr.price), pr.platform, pr.url
        FROM products p
        LEFT JOIN prices pr ON p.id = pr.product_id
        GROUP BY p.id
        ORDER BY pr.timestamp DESC
    ''')
    
    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'lowest_price': row[3] or 0,
            'platform': row[4] or 'N/A',
            'url': row[5] or '#',
            'price_trend': get_price_trend(row[0])
        })
    
    conn.close()
    return {'count': len(products), 'products': products}

@app.get("/api/prices/{product_id}")
async def get_product_prices(product_id: int):
    """Get all prices for a specific product"""
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    cursor.execute('''
        SELECT platform, price, url, timestamp 
        FROM prices 
        WHERE product_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    ''', (product_id,))
    
    prices = [{
        'platform': row[0],
        'price': row[1],
        'url': row[2],
        'timestamp': row[3]
    } for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'product_id': product_id,
        'product_name': product[0],
        'prices': prices,
        'lowest_price': min([p['price'] for p in prices]) if prices else 0
    }

@app.post("/api/alerts")
async def create_price_alert(alert: PriceAlert):
    """Create a price alert"""
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO price_alerts (product_id, target_price, user_email) VALUES (?, ?, ?)',
        (alert.product_id, alert.target_price, alert.user_email)
    )
    
    conn.commit()
    conn.close()
    
    return {
        'status': 'success',
        'message': f'Alert created. You\'ll be notified when price drops below ₹{alert.target_price}'
    }

@app.get("/api/deals")
async def get_best_deals():
    """Get current best deals (items with significant price drops)"""
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, MIN(pr.price), pr.platform
        FROM products p
        JOIN prices pr ON p.id = pr.product_id
        GROUP BY p.id
        ORDER BY pr.price ASC
        LIMIT 10
    ''')
    
    deals = [{
        'id': row[0],
        'name': row[1],
        'price': row[2],
        'platform': row[3]
    } for row in cursor.fetchall()]
    
    conn.close()
    
    return {'deals': deals, 'count': len(deals)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
