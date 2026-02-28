"""
GLOWUP BEAUTY STORE v2.0
========================
Cấu trúc:
  main.py              - Entry point, khởi chạy ứng dụng
  login_window.py      - Màn hình đăng nhập / đăng ký
  admin_window.py      - Cửa sổ quản lý (Admin)
  customer_window.py   - Cửa sổ khách hàng

  ui/
    login_ui.py        - UI màn hình đăng nhập (tương đương login.ui)
    admin_ui.py        - UI Admin (tương đương admin.ui)
    customer_ui.py     - UI Khách hàng (tương đương customer.ui)
    login.ui           - Qt Designer XML - Đăng nhập
    admin.ui           - Qt Designer XML - Admin
    customer.ui        - Qt Designer XML - Khách hàng

  modules/
    data_handler.py    - Đọc/ghi JSON, sinh ID
    inventory.py       - Quản lý kho hàng (CRUD sản phẩm)
    orders.py          - Xử lý đơn hàng, giỏ hàng, thanh toán
    customers.py       - Quản lý khách hàng
    staff.py           - Quản lý nhân viên
    analytics.py       - Thống kê doanh thu
    chatbot.py         - Chatbot tư vấn mỹ phẩm AI
    recommendation.py  - Engine gợi ý sản phẩm theo da
    pdf_export.py      - Xuất hóa đơn PDF (yêu cầu: pip install reportlab)
    excel_export.py    - Xuất báo cáo Excel (yêu cầu: pip install openpyxl)

  data/
    accounts.json      - Tài khoản đăng nhập (admin + khách hàng)
    products.json      - Danh sách sản phẩm (50 SP)
    customers.json     - Danh sách khách hàng (16 KH)
    orders.json        - Lịch sử đơn hàng
    staffs.json        - Danh sách nhân viên
    ...

Tài khoản mặc định:
  Admin   : username=admin    | password=admin123
  KH mẫu : username=anbinh   | password=kh123
           username=thanhbinh | password=kh123
           username=baomai    | password=kh123
           (và nhiều tài khoản khác, xem data/accounts.json)

Chạy ứng dụng:
  python main.py

Cài đặt thư viện (nếu chưa có):

  pip install PyQt6 
  pip install reportlab 
  pip install openpyxl
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import module chính xác
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

from login_window import LoginWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NHÓM 6- Beauty Store")
    app.setApplicationVersion("2.0")

    # Font mặc định
    font = QFont("Bahnschrift", 11)
    app.setFont(font)

    # Icon ứng dụng (nếu có)
    icon_path = BASE_DIR / "images" / "LOGO2.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Hiển thị màn hình đăng nhập
    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
