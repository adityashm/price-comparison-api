# 🛒 Price Comparison & Deal Finder

A production-ready FastAPI backend that helps users find the best deals across e-commerce platforms.

## 🎯 Problem Solved

Users spend hours manually checking multiple e-commerce sites (Amazon, Flipkart) for the best prices. This platform **automatically compares prices** across platforms and alerts users when prices drop.

## ✨ Features

- 🔍 **Multi-Platform Search** - Search across Amazon, Flipkart, and more
- 📊 **Price Tracking** - 7-day price trend analysis
- 🔔 **Price Alerts** - Get notified when prices drop below your target
- 💰 **Best Deals** - Discover current top deals
- 📈 **Price History** - View historical price data

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.10+
- **Scraping:** BeautifulSoup4, Requests
- **Database:** SQLite3
- **API Server:** Uvicorn

## 📋 API Endpoints

### Search Product
```bash
GET /api/search?q=laptop
```

### Get All Products
```bash
GET /api/products
```

### Get Prices for Product
```bash
GET /api/prices/{product_id}
```

### Create Price Alert
```bash
POST /api/alerts
{
  "product_id": 1,
  "target_price": 50000,
  "user_email": "user@example.com"
}
```

### Get Best Deals
```bash
GET /api/deals
```

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run Local
```bash
python main.py
```

Access API at: `http://localhost:8000`
Docs at: `http://localhost:8000/docs`

## 📊 Results

- ✅ Real-time price comparison across 2+ platforms
- ✅ 7-day price trend tracking
- ✅ Email alert system for price drops
- ✅ Scalable architecture for adding more platforms

## 🔄 Data Flow

```
User Search Query
    ↓
Background Scraping (Amazon, Flipkart)
    ↓
Store in SQLite Database
    ↓
API Returns Best Price & Trend
    ↓
User Gets Alerts via Email
```

## 📱 Use Cases

1. **Online Shoppers** - Find best deals before buying
2. **Price Trackers** - Monitor price trends
3. **Budget Conscious Users** - Set price alerts

## 🔐 Security

- CORS enabled for frontend integration
- Input validation with Pydantic
- SQL injection prevention

## 📦 Deployment

Deployed on Railway with auto-scaling

## 📈 Future Enhancements

- Add more e-commerce platforms (eBay, Myntra, etc.)
- Machine learning for price prediction
- Mobile app integration
- Advanced filtering and sorting

---

**Built by:** Aditya Sharma  
**Repository:** [GitHub](https://github.com/adityashm/price-comparison-api)  
**Live Demo:** https://price-comparison-api.railway.app
