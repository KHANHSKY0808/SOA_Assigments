Để cài đặt Django sạch sẽ và tránh xung đột thư viện, cách chuẩn nhất là cài vào một môi trường ảo (**virtual environment**).

Thực hiện theo các bước sau trong Terminal (macOS/Linux) hoặc Command Prompt/PowerShell (Windows):

**1. Tạo thư mục dự án và mở thư mục đó**

```bash
mkdir myproject
cd myproject

```

_Xác nhận:_ Dòng lệnh hiện tại trỏ vào đúng thư mục `myproject`.

**2. Tạo môi trường ảo**

Tạo một môi trường riêng tên là `venv`:

```bash
python -m venv venv

```

_Xác nhận:_ Trong thư mục `myproject` xuất hiện một thư mục con tên là `venv`.

**3. Kích hoạt môi trường ảo**

- **Trên Windows:**
- CMD:

```cmd
venv\Scripts\activate

```

- PowerShell (nếu có lỗi script policy, mở PowerShell quyền Admin chạy `Set-ExecutionPolicy RemoteSigned`):

```powershell
.\venv\Scripts\Activate.ps1

```

- **Trên macOS / Linux:**

```bash
source venv/bin/activate

```

_Xác nhận:_ Đầu dòng lệnh xuất hiện tiền tố `(venv)`.

**4. Cài đặt Django bằng pip**

Nâng cấp `pip` và tải gói Django:

```bash
python -m pip install --upgrade pip
pip install django

```

_Xác nhận:_ Quá trình tải hoàn tất và hiển thị thông báo `Successfully installed django-...`.

**5. Kiểm tra cài đặt thành công**

Chạy lệnh kiểm tra phiên bản Django vừa cài:

```bash
django-admin --version

```

_Xác nhận:_ Màn hình in ra mã phiên bản (ví dụ: `5.x.x`) mà không báo lỗi lệnh không tồn tại (`command not found`).

Để viết một REST API trả về chuỗi hoặc JSON `{"message": "hello-world"}`, bạn có hai cách phổ biến:

- **Cách 1:** Dùng sẵn `JsonResponse` tích hợp trong Django (nhanh nhất, không cần cài thêm thư viện).
- **Cách 2:** Dùng **Django REST Framework (DRF)** (chuẩn công nghiệp cho các dự án thực tế).

Dưới đây là hướng dẫn chi tiết theo cả 2 cách.

---

### Cách 1: Sử dụng sẵn `JsonResponse` của Django (Nhanh, gọn)

#### Bước 1: Khởi tạo project và app

Đảm bảo bạn đang bật môi trường ảo `venv`, sau đó chạy:

```bash
django-admin startproject myapi .
python manage.py startapp core

```

#### Bước 2: Khai báo app trong `myapi/settings.py`

Mở `myapi/settings.py`, thêm `'core'` vào danh sách `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'core',
]

```

#### Bước 3: Viết View trong `core/views.py`

Mở `core/views.py` và tạo hàm trả về dữ liệu:

```python
from django.http import JsonResponse

def hello_world(request):
    return JsonResponse({"message": "hello-world"})

```

#### Bước 4: Tạo file URL cho app `core/urls.py`

Tạo một file mới tên là `urls.py` nằm trong thư mục `core/`:

```python
from django.urls import path
from .views import hello_world

urlpatterns = [
    path('hello/', hello_world, name='hello_world'),
]

```

#### Bước 5: Nối URL vào dự án chính `myapi/urls.py`

Mở file `myapi/urls.py` và sửa lại như sau:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]

```

#### Bước 6: Khởi chạy server và kiểm tra

Chạy lệnh:

```bash
python manage.py runserver

```

Mở trình duyệt hoặc Postman/cURL truy cập đường dẫn:

```text
http://127.0.0.1:8000/api/hello/

```

**Kết quả trả về:**

```json
{
  "message": "hello-world"
}
```

---

### Cách 2: Sử dụng Django REST Framework (DRF)

Nếu bạn muốn xây dựng hệ thống API chuyên nghiệp với giao diện UI kiểm thử tự động, xác thực, phân quyền:

**1. Cài đặt DRF:**

```bash
pip install djangorestframework

```

**2. Khai báo trong `myapi/settings.py`:**

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'core',
]

```

**3. Viết View trong `core/views.py`:**

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def hello_world(request):
    return Response({"message": "hello-world"})

```

Giữ nguyên cấu hình `urls.py` như Cách 1. Khi truy cập lại `[http://127.0.0.1:8000/api/hello/](http://127.0.0.1:8000/api/hello/)` trên trình duyệt, bạn sẽ thấy giao diện **Browsable API** rất trực quan của DRF.
