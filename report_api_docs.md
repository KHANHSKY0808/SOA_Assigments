# Hướng dẫn Kiểm thử Dịch vụ Báo cáo (Report Service)

## 1. Khởi chạy Hệ thống Đa Dịch vụ bằng Docker Desktop

Khởi chạy đồng thời cả 3 dịch vụ chỉ với một lệnh Docker duy nhất:
```powershell
docker compose up --build
```
Hệ thống sẽ tự động khởi tạo 3 container:
- **Service 1: Auth & Product Service** (`http://localhost:8001/`)
- **Service 2: Order Management Service** (`http://localhost:8002/`)
- **Service 3: Report Management Service** (`http://localhost:8003/`)

Để dừng hệ thống:
```powershell
docker compose down
```

---

## 2. Quy trình Xác thực (Authentication)
Dịch vụ Báo cáo yêu cầu xác thực JWT qua Auth Service đã xây dựng ở Bài thực hành số 2.

### Đăng nhập lấy Token
- **Endpoint:** `POST http://127.0.0.1:8001/login/` (hoặc cổng `8002`, `8003`)
- **Body:**
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

> Đính kèm Header cho mọi request báo cáo:
> `Authorization: Bearer <TOKEN>`

---

## 3. Danh sách API Báo cáo Đơn hàng (`/reports/orders`)

### 3.1. Tạo báo cáo đơn hàng mới (POST /reports/orders)
Tự động lấy dữ liệu từ Dịch vụ Quản lý Đơn hàng (Order Service), tính doanh thu, chi phí, lợi nhuận và tự động tạo các báo cáo chi tiết sản phẩm.

- **URL:** `POST http://127.0.0.1:8003/reports/orders`
- **Body (JSON):**
  ```json
  {
    "order_id": 1,
    "total_cost": "1000000.00"
  }
  ```
  *(Nếu không truyền `total_cost`, hệ thống tự tính chi phí ước lượng 70% doanh thu: `total_revenue * 0.70`)*
- **Công thức nghiệp vụ:**
  - `total_revenue = order.total_amount` (lấy từ Order Service)
  - `total_cost = chi_phí_nhập`
  - `total_profit = total_revenue - total_cost`
- **Response (201 Created):**
  ```json
  {
    "id": 1,
    "order_id": 1,
    "total_revenue": "1700000.00",
    "total_cost": "1000000.00",
    "total_profit": "700000.00",
    "created_at": "2026-11-09T08:50:00Z",
    "updated_at": "2026-11-09T08:50:00Z",
    "product_reports": [
      {
        "id": 1,
        "order_report_id": 1,
        "product_id": 1,
        "total_sold": 2,
        "revenue": "1300000.00",
        "cost": "910000.00",
        "profit": "390000.00"
      }
    ]
  }
  ```

### 3.2. Lấy danh sách tất cả các báo cáo đơn hàng (GET /reports/orders)
- **URL:** `GET http://127.0.0.1:8003/reports/orders`
- **Lọc theo đơn hàng:** `GET http://127.0.0.1:8003/reports/orders?order_id=1`
- **Response (200 OK):** Danh sách các báo cáo đơn hàng kèm chi tiết các mặt hàng.

### 3.3. Lấy chi tiết báo cáo đơn hàng (GET /reports/orders/<id>)
- **URL:** `GET http://127.0.0.1:8003/reports/orders/1`
- **Response (200 OK):** Chi tiết báo cáo và các mặt hàng trực thuộc.

### 3.4. Xóa báo cáo đơn hàng (DELETE /reports/orders/<id>)
- **URL:** `DELETE http://127.0.0.1:8003/reports/orders/1`
- **Response (204 No Content)**

---

## 4. Danh sách API Báo cáo Sản phẩm (`/reports/products`)

### 4.1. Tạo báo cáo sản phẩm mới (POST /reports/products)
Lấy thông tin giá bán từ Product Service và số lượng đã bán từ Order Service.

- **URL:** `POST http://127.0.0.1:8003/reports/products`
- **Body 1: Báo cáo sản phẩm trong một `order_report` cụ thể:**
  ```json
  {
    "order_report_id": 1,
    "product_id": 1,
    "cost": "900000.00"
  }
  ```
- **Body 2: Báo cáo sản phẩm tổng hợp trên toàn hệ thống đơn hàng:**
  ```json
  {
    "product_id": 1,
    "cost_per_unit": "450000.00"
  }
  ```
- **Công thức nghiệp vụ:**
  - `total_sold = tổng số lượng sản phẩm bán ra` (tổng hợp từ Order Service)
  - `revenue = tổng doanh thu sản phẩm` (tổng hợp từ Order Service)
  - `cost = cost_per_unit * total_sold` (hoặc giá trị `cost` chỉ định)
  - `profit = revenue - cost`
- **Response (201 Created):**
  ```json
  {
    "id": 1,
    "order_report_id": 1,
    "product_id": 1,
    "total_sold": 2,
    "revenue": "1300000.00",
    "cost": "900000.00",
    "profit": "400000.00",
    "created_at": "2026-11-09T08:50:00Z",
    "updated_at": "2026-11-09T08:50:00Z"
  }
  ```

### 4.2. Lấy danh sách tất cả các báo cáo theo sản phẩm (GET /reports/products)
- **URL:** `GET http://127.0.0.1:8003/reports/products`
- **Lọc theo sản phẩm:** `GET http://127.0.0.1:8003/reports/products?product_id=1`
- **Response (200 OK):** Danh sách báo cáo sản phẩm.

### 4.3. Lấy chi tiết báo cáo sản phẩm (GET /reports/products/<id>)
- **URL:** `GET http://127.0.0.1:8003/reports/products/1`
- **Response (200 OK):** Chi tiết báo cáo sản phẩm.

### 4.4. Xóa báo cáo sản phẩm (DELETE /reports/products/<id>)
- **URL:** `DELETE http://127.0.0.1:8003/reports/products/1`
- **Response (204 No Content)**

