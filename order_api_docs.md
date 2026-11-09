# Hướng dẫn Kiểm thử Dịch vụ Quản lý Đơn hàng (Order Service)

## 1. Khởi chạy các Service bằng Docker

Khởi chạy cả 3 dịch vụ đồng thời qua Docker Compose:
```powershell
docker compose up --build
```
Hệ thống sẽ chạy:
- **Auth & Product Service**: Cổng `8001` (`http://localhost:8001/`)
- **Order Service**: Cổng `8002` (`http://localhost:8002/`)
- **Report Service**: Cổng `8003` (`http://localhost:8003/`)

---

## 2. Quy trình Xác thực (Authentication)
Dịch vụ Quản lý Đơn hàng yêu cầu xác thực JWT qua Auth Service đã xây dựng ở bài trước.

### Bước 1: Đăng nhập lấy Token
- **Endpoint:** `POST http://127.0.0.1:8001/login/` (hoặc `http://127.0.0.1:8002/login/`)
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

> Với tất cả các request đến `/orders` và `/order_items`, đính kèm Header:
> `Authorization: Bearer <token_vừa_lấy>`

---

## 3. Danh sách RESTful API Quản lý Đơn hàng (`/orders`)

### 3.1. Lấy danh sách tất cả các đơn hàng
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8002/orders` (hoặc `http://127.0.0.1:8002/api/orders`)
- **Query param (tùy chọn):** `?status=pending` (hoặc `completed`, `cancelled`)
- **Response (200 OK):**
  ```json
  [
    {
      "id": 1,
      "customer_name": "Nguyen Van A",
      "customer_email": "vana@example.com",
      "total_amount": "1300000.00",
      "status": "pending",
      "created_at": "2026-11-05T07:00:00Z",
      "updated_at": "2026-11-05T07:00:00Z",
      "items": [
        {
          "id": 1,
          "order_id": 1,
          "product_id": 1,
          "product_name": "Bàn phím cơ DareU",
          "quantity": 2,
          "unit_price": "650000.00",
          "total_price": "1300000.00"
        }
      ]
    }
  ]
  ```

### 3.2. Lấy thông tin chi tiết một đơn hàng
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8002/orders/1`
- **Response (200 OK):** Trả về chi tiết đơn hàng và danh sách các mặt hàng trong đơn hàng.

### 3.3. Tạo đơn hàng mới (Kiểm tra tồn kho qua Product Service)
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8002/orders`
- **Body (JSON):**
  ```json
  {
    "customer_name": "Nguyen Van A",
    "customer_email": "vana@example.com",
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }
  ```
- **Xử lý nghiệp vụ:**
  1. Kiểm tra sự tồn tại của `product_id` từ Product Service.
  2. Kiểm tra số lượng tồn kho: nếu `quantity > stock`, trả về lỗi `400 Bad Request` ("Không đủ tồn kho...").
  3. Tự động lấy giá sản phẩm `unit_price`, tính `total_price` cho từng mặt hàng và tính `total_amount` của đơn hàng.
  4. Trừ số lượng tồn kho tương ứng trong Product Service.
- **Response (201 Created):** Trả về đơn hàng vừa được tạo.

### 3.4. Cập nhật trạng thái đơn hàng
- **Method:** `PUT`
- **URL:** `http://127.0.0.1:8002/orders/1`
- **Body (JSON):**
  ```json
  {
    "status": "completed"
  }
  ```
  *(Các trạng thái hợp lệ: `pending`, `completed`, `cancelled`)*
  *Lưu ý: Nếu cập nhật sang `cancelled`, hệ thống tự động hoàn trả số lượng hàng vào kho!*
- **Response (200 OK):** Trả về thông tin đơn hàng sau khi cập nhật.

### 3.5. Xóa một đơn hàng
- **Method:** `DELETE`
- **URL:** `http://127.0.0.1:8002/orders/1`
- **Xử lý nghiệp vụ:** Nếu đơn hàng chưa bị hủy, hệ thống hoàn trả tồn kho trước khi xóa.
- **Response (204 No Content):** Xóa thành công.

---

## 4. Danh sách RESTful API Chi tiết Đơn hàng (`/order_items`)

### 4.1. Lấy danh sách mặt hàng
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8002/order_items`
- **Lọc theo đơn hàng:** `http://127.0.0.1:8002/order_items?order_id=1`
- **Response (200 OK):** Danh sách các mặt hàng.

### 4.2. Lấy thông tin chi tiết một mặt hàng
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8002/order_items/1`
- **Response (200 OK):** Thông tin mặt hàng.

### 4.3. Tạo mặt hàng mới trong đơn hàng
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8002/order_items`
- **Body (JSON):**
  ```json
  {
    "order_id": 1,
    "product_id": 1,
    "quantity": 1
  }
  ```
- **Xử lý nghiệp vụ:**
  - Kiểm tra tồn kho từ Product Service.
  - Trừ tồn kho sản phẩm.
  - Tự động cộng thêm tiền vào `total_amount` của đơn hàng tương ứng.
- **Response (201 Created)**

### 4.4. Cập nhật mặt hàng
- **Method:** `PUT`
- **URL:** `http://127.0.0.1:8002/order_items/1`
- **Body (JSON):**
  ```json
  {
    "quantity": 3
  }
  ```
- **Xử lý nghiệp vụ:**
  - So sánh số lượng cũ và mới để trừ thêm hoặc hoàn lại tồn kho trong Product Service.
  - Cập nhật lại `total_price` của item và `total_amount` của đơn hàng.
- **Response (200 OK)**

### 4.5. Xóa một mặt hàng trong đơn hàng
- **Method:** `DELETE`
- **URL:** `http://127.0.0.1:8002/order_items/1`
- **Xử lý nghiệp vụ:**
  - Tự động hoàn lại số lượng sản phẩm vào kho.
  - Tự động trừ tiền khỏi `total_amount` của đơn hàng.
- **Response (204 No Content)**

