# Hệ Thống Quản Trị Đa Dịch Vụ Theo Kiến Trúc SOA (Service-Oriented Architecture)

Dự án môn học **Kiến trúc Hướng Dịch vụ (SOA)** được xây dựng bằng **Django & Django REST Framework (DRF)**, triển khai theo mô hình microservices độc lập và đóng gói bằng **Docker Desktop & Docker Compose**.

---

## 1. Kiến Trúc Tổng Quan (Architecture Overview)

Hệ thống phân tách thành 3 dịch vụ chuyên biệt chạy trên 3 cổng riêng biệt, giao tiếp với nhau qua giao thức HTTP RESTful API và mạng nội bộ Docker:

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
                       |====== (Xác thực JWT / Tồn kho) =======|
                       |                       |               |
                       +=======================+===============+
                                               |
                                     (Doanh thu & Số lượng bán)
```

### Các Dịch vụ trong hệ thống:

| Tên Dịch vụ | Cổng | Docker Service Name | Chức năng chính |
| :--- | :---: | :--- | :--- |
| **Auth & Product Service** | `8001` | `auth-product-service` | • **Xác thực JWT**: Cấp phát và thẩm định token (`/login/`, `/auth/`).<br>• **Quản lý Sản phẩm**: CRUD danh mục sản phẩm và quản lý số lượng tồn kho (`/products`). |
| **Order Management Service** | `8002` | `order-service` | • **Quản lý Đơn hàng & Chi tiết**: Quản lý đơn hàng (`/orders`) và mặt hàng (`/order_items`).<br>• Tự động gọi Product Service kiểm tra và trừ tồn kho, tính tổng tiền đơn hàng, hoàn kho khi hủy đơn. |
| **Report Management Service** | `8003` | `report-service` | • **Báo cáo Đơn hàng**: Tính toán doanh thu, chi phí, lợi nhuận đơn hàng (`/reports/orders`).<br>• **Báo cáo Sản phẩm**: Thống kê số lượng bán, doanh thu và biên lợi nhuận theo sản phẩm (`/reports/products`). |

---

## 2. Cấu Trúc Thư Mục (Project Structure)

```text
SOA_Assigments/
├── core/                       # Service 1A: Auth Service (Đăng nhập, JWT Token, User model)
│   ├── models.py               # Model User
│   ├── views.py                # Login, Verify Token, Hello World
│   └── urls.py
├── products/                   # Service 1B: Product Service (Quản lý sản phẩm, tồn kho)
│   ├── models.py               # Model Product
│   ├── authentication.py       # ExternalTokenAuthentication (gọi Auth Service)
│   ├── views.py                # CRUD Products
│   └── urls.py
├── orders/                     # Service 2: Order Service (Đơn hàng & Mặt hàng)
│   ├── models.py               # Model Order, OrderItem
│   ├── authentication.py       # Xác thực JWT qua Auth Service
│   ├── services.py             # HTTP Client gọi Product Service (kiểm tra/trừ kho)
│   ├── views.py                # CRUD Orders & OrderItems
│   └── urls.py
├── reports/                    # Service 3: Report Service (Báo cáo doanh thu & lợi nhuận)
│   ├── models.py               # Model OrderReport, ProductReport
│   ├── authentication.py       # Xác thực JWT qua Auth Service
│   ├── services.py             # HTTP Client gọi Order Service & Product Service
│   ├── views.py                # CRUD Reports (Orders & Products)
│   └── urls.py
├── myapi/                      # Cấu hình dự án Django
│   ├── settings.py
│   └── urls.py
├── Dockerfile                  # Đóng gói image Docker Python 3.12
├── docker-compose.yml          # Cấu hình khởi chạy 3 service đồng thời
├── .dockerignore
├── requirements.txt            # Thư viện phụ thuộc
├── manage.py
├── db.sqlite3                  # Cơ sở dữ liệu SQLite
├── order_api_docs.md           # Hướng dẫn chi tiết API Đơn hàng
└── report_api_docs.md          # Hướng dẫn chi tiết API Báo cáo
```

---

## 3. Cấu Trúc Cơ Sở Dữ Liệu (Database Schema)

### 3.1. Bảng `orders` (Quản lý Đơn hàng)
| Tên cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | ID duy nhất của đơn hàng |
| `customer_name` | `VARCHAR(255)` | Tên khách hàng |
| `customer_email` | `VARCHAR(255)` | Email khách hàng |
| `total_amount` | `DECIMAL(10, 2)` | Tổng số tiền của đơn hàng |
| `status` | `VARCHAR(50)` | Trạng thái: `pending`, `completed`, `cancelled` |
| `created_at` | `TIMESTAMP` | Ngày tạo |
| `updated_at` | `TIMESTAMP` | Ngày cập nhật |

### 3.2. Bảng `order_items` (Chi tiết Mặt hàng trong Đơn)
| Tên cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | ID chi tiết đơn hàng |
| `order_id` | `INT` | ID đơn hàng (Khóa ngoại trỏ đến `orders`) |
| `product_id` | `INT` | ID sản phẩm (Lưu vết liên kết với Product Service) |
| `product_name` | `VARCHAR(255)` | Tên sản phẩm tại thời điểm đặt |
| `quantity` | `INT` | Số lượng sản phẩm |
| `unit_price` | `DECIMAL(10, 2)` | Đơn giá tại thời điểm đặt |
| `total_price` | `DECIMAL(10, 2)` | Tổng giá trị = `quantity * unit_price` |

### 3.3. Bảng `orders_reports` (Báo cáo Đơn hàng)
| Tên cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | ID báo cáo đơn hàng |
| `order_id` | `INT` | ID đơn hàng (Lưu vết liên kết với Order Service) |
| `total_revenue` | `DECIMAL(10, 2)` | Tổng doanh thu đơn hàng |
| `total_cost` | `DECIMAL(10, 2)` | Tổng chi phí nhập sản phẩm |
| `total_profit` | `DECIMAL(10, 2)` | Tổng lợi nhuận = `total_revenue - total_cost` |

### 3.4. Bảng `product_reports` (Báo cáo Sản phẩm)
| Tên cột | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | `INT (PRIMARY KEY)` | ID báo cáo sản phẩm |
| `order_report_id` | `INT` | ID báo cáo đơn hàng (Khóa ngoại trỏ đến `orders_reports`) |
| `product_id` | `INT` | ID sản phẩm (Lưu vết liên kết với Product Service) |
| `total_sold` | `INT` | Tổng số lượng sản phẩm đã bán |
| `revenue` | `DECIMAL(10, 2)` | Doanh thu từ sản phẩm |
| `cost` | `DECIMAL(10, 2)` | Chi phí nhập sản phẩm |
| `profit` | `DECIMAL(10, 2)` | Lợi nhuận = `revenue - cost` |

---

## 4. Hướng Dẫn Cài Đặt & Khởi Chạy

### Cách 1: Khởi chạy bằng Docker Desktop (Khuyên dùng)

Đảm bảo bạn đã cài đặt và đang bật **Docker Desktop**.

1. **Khởi chạy đồng thời cả 3 dịch vụ**:
   ```powershell
   docker compose up --build -d
   ```
2. **Kiểm tra trạng thái các container**:
   ```powershell
   docker compose ps
   ```
   Kết quả hiển thị 3 service đang hoạt động:
   - `auth-product-service`: cổng `8001`
   - `order-service`: cổng `8002`
   - `report-service`: cổng `8003`

3. **Xem log container (nếu cần gỡ lỗi)**:
   ```powershell
   docker compose logs -f
   ```

4. **Dừng toàn bộ hệ thống**:
   ```powershell
   docker compose down
   ```

---

### Cách 2: Khởi chạy trực tiếp bằng Môi trường Ảo (Python venv)

Nếu không dùng Docker, bạn có thể chạy 3 terminal riêng biệt:

1. **Kích hoạt virtual environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   ```

2. **Chạy từng dịch vụ trên các terminal riêng**:
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

## 5. Hướng Dẫn Kiểm Thử RESTful API

### Bước 1: Đăng nhập lấy Token xác thực (Auth Service)
Mọi API trong Order Service và Report Service đều yêu cầu xác thực JWT.
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
> **Lưu ý:** Đính kèm header `Authorization: Bearer <TOKEN>` cho tất cả các request phía sau.

---

### Bước 2: Dịch vụ Quản lý Sản phẩm (`http://localhost:8001`)

| Method | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/products` | Lấy danh sách sản phẩm |
| `GET` | `/products/<id>` | Lấy chi tiết sản phẩm |
| `POST` | `/products` | Thêm sản phẩm mới (tên, giá, tồn kho) |
| `PUT` | `/products/<id>` | Cập nhật thông tin sản phẩm |
| `DELETE` | `/products/<id>` | Xóa sản phẩm |

**Ví dụ tạo sản phẩm mới:**
```bash
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "Bàn phím cơ AKKO",
    "description": "Bàn phím không dây",
    "price": "850000.00",
    "quantity": 20
  }'
```

---

### Bước 3: Dịch vụ Quản lý Đơn hàng (`http://localhost:8002`)

| Method | Endpoint | Mô tả nghiệp vụ |
| :--- | :--- | :--- |
| `GET` | `/orders` | Lấy danh sách đơn hàng (hỗ trợ lọc `?status=pending`) |
| `GET` | `/orders/<id>` | Lấy chi tiết đơn hàng kèm danh sách mặt hàng |
| `POST` | `/orders` | **Tạo đơn hàng**: Gọi Product Service kiểm tra tồn kho, trừ tồn kho, tự tính `total_amount` |
| `PUT` | `/orders/<id>` | Cập nhật trạng thái (`completed`, `cancelled`). Hoàn kho nếu hủy đơn |
| `DELETE` | `/orders/<id>` | Xóa đơn hàng (tự động hoàn kho) |
| `GET` | `/order_items` | Lấy danh sách mặt hàng (hỗ trợ lọc `?order_id=<id>`) |
| `GET` | `/order_items/<id>`| Lấy chi tiết một mặt hàng |
| `POST` | `/order_items` | Thêm mặt hàng vào đơn (kiểm tra tồn kho, cập nhật `total_amount`) |
| `PUT` | `/order_items/<id>`| Sửa số lượng mặt hàng (tự điều chỉnh bù trừ tồn kho) |
| `DELETE` | `/order_items/<id>`| Xóa mặt hàng (hoàn kho, trừ `total_amount` đơn hàng) |

**Ví dụ tạo đơn hàng mới:**
```bash
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "customer_name": "Nguyen Van A",
    "customer_email": "vana@example.com",
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }'
```

---

### Bước 4: Dịch vụ Báo cáo (`http://localhost:8003`)

| Method | Endpoint | Mô tả nghiệp vụ |
| :--- | :--- | :--- |
| `GET` | `/reports/orders` | Lấy danh sách báo cáo đơn hàng (kèm chi tiết `product_reports`) |
| `GET` | `/reports/orders/<id>` | Lấy chi tiết báo cáo đơn hàng |
| `POST` | `/reports/orders` | **Tạo báo cáo đơn hàng**: Lấy tổng tiền từ Order Service, tính `total_revenue`, `total_cost`, `total_profit`, tự động tạo `product_reports` |
| `DELETE` | `/reports/orders/<id>` | Xóa báo cáo đơn hàng (cascade xóa các báo cáo sản phẩm liên quan) |
| `GET` | `/reports/products` | Lấy danh sách báo cáo sản phẩm (hỗ trợ lọc `?product_id=...`) |
| `GET` | `/reports/products/<id>`| Lấy chi tiết báo cáo sản phẩm |
| `POST` | `/reports/products` | **Tạo báo cáo sản phẩm**: Lấy giá từ Product Service, tổng hợp số lượng bán từ Order Service, tính `revenue`, `cost`, `profit` |
| `DELETE` | `/reports/products/<id>`| Xóa báo cáo sản phẩm |

**Ví dụ tạo báo cáo đơn hàng:**
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

## 6. Bộ Kiểm Thử Tự Động (Automated Test Suite)

Dự án bao gồm 15 bài kiểm thử đơn vị & tích hợp bao quát toàn bộ các ca kiểm thử:
- Kiểm thử xác thực token JWT, chặn truy cập không phép (401 Unauthorized).
- Kiểm thử logic tồn kho: kiểm tra số lượng, từ chối khi hết hàng, trừ kho, hoàn kho khi hủy đơn.
- Kiểm thử CRUD Đơn hàng và Chi tiết mặt hàng.
- Kiểm thử tính toán doanh thu, chi phí, lợi nhuận trong Báo cáo Đơn hàng và Báo cáo Sản phẩm.

Chạy toàn bộ test suite:
```powershell
.\venv\Scripts\python.exe manage.py test
```
**Kết quả kiểm thử:**
```text
Ran 15 tests in 0.081s - OK
```

