"""
login_window.py - Logic màn hình đăng nhập và đăng ký
"""
import sys
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

from ui.login_ui import Ui_LoginWindow
from modules.data_handler import load_accounts, save_accounts, load_customers, save_customers, generate_account_id, generate_customer_id


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        self._connect_signals()
        # Mặc định hiện trang đăng nhập
        self.ui.stackedWidget.setCurrentIndex(0)

    # ── Kết nối sự kiện ──────────────────────────────────────────────────────
    def _connect_signals(self):
        self.ui.btnLogin.clicked.connect(self.handle_login)
        self.ui.btnRegisterSwitch.clicked.connect(self.show_register)
        self.ui.btnBackToLogin.clicked.connect(self.show_login)
        self.ui.btnRegister.clicked.connect(self.handle_register)
        # Enter để đăng nhập
        self.ui.txtPassword.returnPressed.connect(self.handle_login)
        self.ui.txtUsername.returnPressed.connect(self.handle_login)

    def show_login(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.lblLoginError.setText("")

    def show_register(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.lblRegError.setText("")

    # ── Xử lý đăng nhập ──────────────────────────────────────────────────────
    def handle_login(self):
        username = self.ui.txtUsername.text().strip()
        password = self.ui.txtPassword.text().strip()

        if not username or not password:
            self.ui.lblLoginError.setText("⚠ Vui lòng nhập đầy đủ thông tin!")
            return

        accounts = load_accounts()
        account = next(
            (a for a in accounts
             if a.get("username") == username and a.get("password") == password),
            None
        )

        if not account:
            self.ui.lblLoginError.setText("❌ Tên đăng nhập hoặc mật khẩu không đúng!")
            self.ui.txtPassword.clear()
            return

        self.ui.lblLoginError.setText("")
        role = account.get("role", "customer")

        if role == "admin":
            self._open_admin(account)
        else:
            self._open_customer(account)

    def _open_admin(self, account):
        from admin_window import AdminWindow
        self.admin_win = AdminWindow(account)
        self.admin_win.show()
        self.close()

    def _open_customer(self, account):
        from customer_window import CustomerWindow
        self.customer_win = CustomerWindow(account)
        self.customer_win.show()
        self.close()

    # ── Xử lý đăng ký ────────────────────────────────────────────────────────
    def handle_register(self):
        name = self.ui.txtRegName.text().strip()
        phone = self.ui.txtRegPhone.text().strip()
        username = self.ui.txtRegUsername.text().strip()
        password = self.ui.txtRegPassword.text().strip()

        # Validate
        if not all([name, phone, username, password]):
            self.ui.lblRegError.setText("⚠ Vui lòng điền đầy đủ thông tin!")
            return
        if len(password) < 4:
            self.ui.lblRegError.setText("⚠ Mật khẩu phải có ít nhất 4 ký tự!")
            return
        if not phone.isdigit() or len(phone) < 9:
            self.ui.lblRegError.setText("⚠ Số điện thoại không hợp lệ!")
            return

        accounts = load_accounts()
        # Kiểm tra trùng username
        if any(a.get("username") == username for a in accounts):
            self.ui.lblRegError.setText("❌ Tên đăng nhập đã tồn tại!")
            return
        # Kiểm tra trùng SĐT trong customers
        customers = load_customers()
        if any(c.get("phone") == phone for c in customers):
            self.ui.lblRegError.setText("❌ Số điện thoại đã được đăng ký!")
            return

        # Tạo khách hàng mới
        customer_id = generate_customer_id(customers)
        new_customer = {
            "customer_id": customer_id,
            "name": name,
            "phone": phone,
            "email": "",
            "skin-type": "",
            "skin_concern": [],
            "rank": "Đồng",
            "loyalty_points": 0,
        }
        customers.append(new_customer)
        save_customers(customers)

        # Tạo account mới
        account_id = generate_account_id(accounts)
        new_account = {
            "account_id": account_id,
            "username": username,
            "password": password,
            "role": "customer",
            "customer_id": customer_id,
            "full_name": name,
        }
        accounts.append(new_account)
        save_accounts(accounts)

        QMessageBox.information(
            self, "Đăng ký thành công",
            f"✅ Tài khoản đã được tạo!\n\nTên đăng nhập: {username}\nMã KH: {customer_id}\n\n"
            "Bạn có thể đăng nhập ngay bây giờ."
        )
        # Xóa form và quay về trang đăng nhập
        for field in [self.ui.txtRegName, self.ui.txtRegPhone,
                      self.ui.txtRegUsername, self.ui.txtRegPassword]:
            field.clear()
        self.ui.txtUsername.setText(username)
        self.show_login()
