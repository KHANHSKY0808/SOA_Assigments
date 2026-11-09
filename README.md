# Multi-Service Management System (Service-Oriented Architecture - SOA)

A **Service-Oriented Architecture (SOA)** coursework project built with **Django & Django REST Framework (DRF)**, designed with an independent distributed microservices pattern, and fully containerized with **Docker Desktop & Docker Compose**.

---

## 1. Architecture Overview

The system is decomposed into three specialized services running on isolated ports, communicating via HTTP RESTful APIs within an internal Docker bridge network (`soa-network`):

```
                                  +---------------------------------------+
                                  |     Client (Postman / Browser)        |
                                  +---------------------------------------+
                                      |               |               |
                       :8001          |        :8002  |        :8003  |
                       +--------------+        +------+        +------+
                       |                       |               |
                       v                       v               v
        +----------------------------+   +-----------+   +------------+
        |   Auth & Product Service   |   |   Order   |   |   Report   |
        |       (Port 8001)          |   |  Service  |   |  Service   |
        | - Auth JWT (/login, /auth) |   | (Port8002)|   | (Port 8003)|
        | - Products CRUD            |   +-----------+   +------------+
        +----------------------------+         |               |
                       ^                       |               |
                       |====== (JWT Verification / Inventory) =|
                       |                       |               |
                       +=======================+===============+
                                               |
                                    (Revenues & Units Sold)
```

### System Services:

| Service Name | Port | Docker Container | Core Responsibilities |
| :--- | :---: | :--- | :--- |
| **Auth & Product Service** | `8001` | `auth-product-service` | • **JWT Authentication**: Token issuance and verification (`/login/`, `/auth/`).<br>• **Product Management**: CRUD product catalog and real-time inventory tracking (`/products`). |
| **Order Management Service** | `8002` | `order-service` | • **Orders & Order Items**: Manage orders (`/orders`) and line items (`/order_items`).<br>• Inter-service inventory check: queries Product Service to verify stock, automatically deducts inventory upon order creation, and restores stock upon cancellation. |
| **Report Management Service** | `8003` | `report-service` | • **Order Reports**: Aggregates revenue, cost, and net profit per order (`/reports/orders`).<br>• **Product Reports**: Analyzes units sold, revenue, cost, and profit margin per product (`/reports/products`). |

---

## 2. Project Directory Structure

```text
SOA_Assigments/
├── core/                       # Service 1A: Auth Service (User login, JWT authentication, User model)
│   ├── models.py               # User model
│   ├── views.py                # Login, Verify Token, Hello World
│   └── urls.py
├── products/                   # Service 1B: Product Service (Product catalog & inventory)
│   ├── models.py               # Product model
│   ├── authentication.py       # ExternalTokenAuthentication (calls Auth Service)
│   ├── views.py                # CRUD Products
│   └── urls.py
├── orders/                     # Service 2: Order Service (Orders & Order items)
│   ├── models.py               # Order & OrderItem models
│   ├── authentication.py       # JWT verification via Auth Service
│   ├── services.py             # HTTP client calling Product Service (inventory check/deduction)
│   ├── views.py                # CRUD Orders & OrderItems
│   └── urls.py
├── reports/                    # Service 3: Report Service (Financial & sales analytics)
│   ├── models.py               # OrderReport & ProductReport models
│   ├── authentication.py       # JWT verification via Auth Service
│   ├── services.py             # HTTP client calling Order Service & Product Service
│   ├── views.py                # CRUD Reports (Orders & Products)
│   └── urls.py
├── myapi/                      # Django project configuration
│   ├── settings.py
│   └── urls.py
├── Dockerfile                  # Python 3.12 container image definition
├── docker-compose.yml          # Multi-container orchestration definition
├── .dockerignore
├── requirements.txt            # Python dependencies
├── manage.py
├── db.sqlite3                  # SQLite database
├── order_api_docs.md           # Detailed Order Service documentation
└── report_api_docs.md          # Detailed Report Service documentation
```

---

## 3. Database Schema

### 3.1. `orders` Table (Order Management)
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | Unique identifier of the order |
| `customer_name` | `VARCHAR(255)` | Customer name |
| `customer_email` | `VARCHAR(255)` | Customer email address |
| `total_amount` | `DECIMAL(10, 2)` | Total monetary value of the order |
| `status` | `VARCHAR(50)` | Order status: `pending`, `completed`, `cancelled` |
| `created_at` | `TIMESTAMP` | Record creation timestamp |
| `updated_at` | `TIMESTAMP` | Last updated timestamp |

### 3.2. `order_items` Table (Order Line Items)
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | Unique identifier of the order item |
| `order_id` | `INT` | Foreign Key referencing `orders.id` |
| `product_id` | `INT` | Product ID linking to Product Service |
| `product_name` | `VARCHAR(255)` | Product name at time of purchase |
| `quantity` | `INT` | Quantity purchased |
| `unit_price` | `DECIMAL(10, 2)` | Unit price at time of purchase |
| `total_price` | `DECIMAL(10, 2)` | Total item price = `quantity * unit_price` |

### 3.3. `orders_reports` Table (Order Financial Reports)
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | Unique identifier of the order report |
| `order_id` | `INT` | Referenced order ID |
| `total_revenue` | `DECIMAL(10, 2)` | Total revenue from the order |
| `total_cost` | `DECIMAL(10, 2)` | Total cost of goods for the order |
| `total_profit` | `DECIMAL(10, 2)` | Net profit = `total_revenue - total_cost` |

### 3.4. `product_reports` Table (Product Analytics Reports)
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | Unique identifier of the product report |
| `order_report_id` | `INT` | Foreign Key referencing `orders_reports.id` (optional/nullable) |
| `product_id` | `INT` | Referenced product ID |
| `total_sold` | `INT` | Total quantity sold |
| `revenue` | `DECIMAL(10, 2)` | Total revenue generated by the product |
| `cost` | `DECIMAL(10, 2)` | Total cost of goods for the product |
| `profit` | `DECIMAL(10, 2)` | Net profit = `revenue - cost` |

---

## 4. Installation & Deployment Guide

### Option 1: Docker Desktop Deployment (Recommended)

Make sure **Docker Desktop** is running on your machine.

1. **Build and start all 3 services**:
   ```powershell
   docker compose up --build -d
   ```
2. **Verify active containers**:
   ```powershell
   docker compose ps
   ```
   All three services will be operational:
   - `auth-product-service`: Port `8001`
   - `order-service`: Port `8002`
   - `report-service`: Port `8003`

3. **Stream container logs (for debugging)**:
   ```powershell
   docker compose logs -f
   ```

4. **Shut down services**:
   ```powershell
   docker compose down
   ```

---

### Option 2: Local Python Virtual Environment Deployment

If running directly without Docker:

1. **Activate virtual environment & install dependencies**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   ```

2. **Launch each service on dedicated terminal windows**:
   - **Terminal 1** - Auth & Product Service (`8001`):
     ```powershell
     python manage.py runserver 8001
     ```
   - **Terminal 2** - Order Service (`8002`):
     ```powershell
     python manage.py runserver 8002
     ```
   - **Terminal 3** - Report Service (`8003`):
     ```powershell
     python manage.py runserver 8003
     ```

---

## 5. RESTful API Testing & Integration Guide

### Step 1: Authentication & Token Issuance (Auth Service)
All protected endpoints across the services require a JWT Bearer token.
- **Method:** `POST`
- **URL:** `http://localhost:8001/login/`
- **Body (JSON):**
  ```json
  {
    "userName": "admin",
    "password": "admin123"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Đăng nhập thành công",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
> **Note:** Include header `Authorization: Bearer <TOKEN>` in all subsequent requests.

---

### Step 2: Product Management Service (`http://localhost:8001`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/products` | List all products |
| `GET` | `/products/<id>` | Retrieve product details |
| `POST` | `/products` | Create a new product (name, price, stock quantity) |
| `PUT` | `/products/<id>` | Update product details |
| `DELETE` | `/products/<id>` | Delete a product |

**Example - Create a new product:**
```bash
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "Wireless Mechanical Keyboard",
    "description": "RGB backlight, Bluetooth 5.0",
    "price": "850000.00",
    "quantity": 20
  }'
```

---

### Step 3: Order Management Service (`http://localhost:8002`)

| Method | Endpoint | Business Logic |
| :--- | :--- | :--- |
| `GET` | `/orders` | List all orders (filter with `?status=pending`) |
| `GET` | `/orders/<id>` | Retrieve order details along with line items |
| `POST` | `/orders` | **Create Order**: Calls Product Service to verify inventory, automatically deducts stock, calculates `total_amount` |
| `PUT` | `/orders/<id>` | Update order status (`completed`, `cancelled`). Restores stock if cancelled |
| `DELETE` | `/orders/<id>` | Delete an order (restores stock if not already cancelled) |
| `GET` | `/order_items` | List order items (filter with `?order_id=<id>`) |
| `GET` | `/order_items/<id>`| Retrieve order item details |
| `POST` | `/order_items` | Add item to order (verifies stock, recalculates order `total_amount`) |
| `PUT` | `/order_items/<id>`| Update item quantity (adjusts stock difference and order `total_amount`) |
| `DELETE` | `/order_items/<id>`| Remove item (restores stock, adjusts order `total_amount`) |

**Example - Create an order (with automated stock deduction):**
```bash
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "customer_name": "John Doe",
    "customer_email": "johndoe@example.com",
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }'
```

---

### Step 4: Report Management Service (`http://localhost:8003`)

| Method | Endpoint | Business Logic |
| :--- | :--- | :--- |
| `GET` | `/reports/orders` | List all order reports (includes nested `product_reports`) |
| `GET` | `/reports/orders/<id>` | Retrieve order report details |
| `POST` | `/reports/orders` | **Create Order Report**: Fetches total order value from Order Service, computes `total_revenue`, `total_cost`, `total_profit`, generates corresponding `product_reports` |
| `DELETE` | `/reports/orders/<id>` | Delete order report (cascades to related product reports) |
| `GET` | `/reports/products` | List product reports (filter with `?product_id=...`) |
| `GET` | `/reports/products/<id>`| Retrieve product report details |
| `POST` | `/reports/products` | **Create Product Report**: Queries Product Service for price, aggregates total sold from Order Service, computes `revenue`, `cost`, `profit` |
| `DELETE` | `/reports/products/<id>`| Delete product report |

**Example - Generate an Order Report:**
```bash
curl -X POST http://localhost:8003/reports/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "order_id": 1,
    "total_cost": "1000000.00"
  }'
```

---

## 6. Automated Test Suite

The project includes 15 automated unit and integration tests covering:
- JWT Token authentication and rejection of unauthorized requests (401 Unauthorized).
- Inventory validation: checking stock, rejecting out-of-stock orders, stock deduction, and restock upon cancellation.
- Full CRUD workflows for Orders and Order Items.
- Real-time computation of revenue, cost, and net profit in Order Reports and Product Reports.

Run the test suite:
```powershell
.\venv\Scripts\python.exe manage.py test
```
**Test Results:**
```text
Ran 15 tests in 0.081s - OK
```
