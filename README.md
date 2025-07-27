# Tillie - Inventory Management System

A Django REST API backend for multi-shop inventory management with user authentication and dashboard analytics.

## 🚀 Features

- **User Authentication** - JWT-based auth with custom user model
- **Multi-Shop Support** - Users can be assigned to specific shops
- **Inventory Management** - Products, categories, and stock tracking
- **Dashboard API** - Real-time analytics by category
- **Admin Interface** - Django admin for easy management
- **Rate Limiting** - Security features with Redis cache

## 🛠️ Tech Stack

- Django 5.2.4
- Django REST Framework
- JWT Authentication
- Redis (caching & rate limiting)
- PostgreSQL/SQLite
- Python 3.13

## 📊 API Endpoints

- `/api/auth/` - Authentication (register, login, user management)
- `/api/inventory/` - Inventory management (products, categories)
- `/api/inventory/dashboard/` - Analytics dashboard

## 🏃‍♂️ Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Start server: `python manage.py runserver`

## 📚 Study Project

This project was developed as part of my studies to demonstrate:
- Django backend development
- REST API design
- Database modeling
- Authentication systems
- Business logic implementation
