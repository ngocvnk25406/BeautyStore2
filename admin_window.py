"""
admin_window.py - Logic cửa sổ quản lý Admin
Tích hợp: kho hàng, khách hàng, đơn hàng, gợi ý, chatbot, thống kê, nhân viên
+ Xuất PDF hóa đơn, xuất Excel báo cáo
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QTableWidgetItem, QHeaderView, QInputDialog, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt

from ui.admin_ui import Ui_AdminWindow
from modules import (
    data_handler as dh,
    inventory as inv,
    orders as ord_mod,
    customers as cust_mod,
    staff as staff_mod,
    analytics as ana,
    chatbot as bot,
    recommendation as rec,
    excel_export,
)

BASE_DIR = Path(__file__).resolve().parent


class AdminWindow(QMainWindow):
    def __init__(self, account: dict):
        super().__init__()
        self.account = account
        self.ui = Ui_AdminWindow()
        self.ui.setupUi(self)
        self._cart = []          # [{"product_id", "name", "price", "quantity"}]
        self._current_customer = None
        self._chat_context = bot.new_context()
        self._connect_signals()
        self._load_all()

    # ── Kết nối sự kiện ──────────────────────────────────────────────────────
    def _connect_signals(self):
        u = self.ui
        # Kho hàng
        u.btnSearchProduct.clicked.connect(self.search_products)
        u.btnRefreshProduct.clicked.connect(self.load_products)
        u.btnAddProduct.clicked.connect(self.add_product)
        u.btnEditProduct.clicked.connect(self.edit_product)
        u.btnDeleteProduct.clicked.connect(self.delete_product)
        u.btnLowStock.clicked.connect(self.show_low_stock)
        u.btnExpired.clicked.connect(self.show_expired)
        u.txtSearchProduct.returnPressed.connect(self.search_products)
        # Khách hàng
        u.btnSearchCustomer.clicked.connect(self.search_customers)
        u.btnRefreshCustomer.clicked.connect(self.load_customers)
        u.btnAddCustomer.clicked.connect(self.add_customer)
        u.btnEditCustomer.clicked.connect(self.edit_customer)
        u.btnViewCustomer.clicked.connect(self.view_customer)
        u.txtSearchCustomer.returnPressed.connect(self.search_customers)
        # Đơn hàng
        u.btnNewOrder.clicked.connect(self.new_order)
        u.btnViewOrder.clicked.connect(self.view_order)
        u.btnPrintInvoice.clicked.connect(self.print_invoice)
        u.btnExportPDF.clicked.connect(self.export_excel)
        u.btnFindCustomer.clicked.connect(self.find_customer)
        u.btnAddToCart.clicked.connect(self.add_to_cart)
        u.btnRemoveFromCart.clicked.connect(self.remove_from_cart)
        u.btnCheckout.clicked.connect(self.checkout)
        # Gợi ý
        u.btnGetRecommend.clicked.connect(self.get_recommendations)
        u.btnGetRoutine.clicked.connect(self.get_routine)
        # Chatbot
        u.btnSendChat.clicked.connect(self.send_chat)
        u.btnClearChat.clicked.connect(self.clear_chat)
        u.txtChatInput.returnPressed.connect(self.send_chat)
        # Thống kê
        u.btnRefreshStats.clicked.connect(self.load_analytics)
        u.btnExportExcel.clicked.connect(self.export_excel)
        # Nhân viên
        u.btnSearchStaff.clicked.connect(self.search_staffs)
        u.btnRefreshStaff.clicked.connect(self.load_staffs)
        u.btnAddStaff.clicked.connect(self.add_staff)
        u.btnEditStaff.clicked.connect(self.edit_staff)
        u.btnDeleteStaff.clicked.connect(self.delete_staff)
        u.btnAssignShift.clicked.connect(self.assign_shift)
        u.txtSearchStaff.returnPressed.connect(self.search_staffs)

    def _load_all(self):
        self.load_products()
        self.load_customers()
        self.load_orders()
        self.load_analytics()
        self.load_staffs()
        name = self.account.get("full_name", "Admin")
        self.ui.statusbar.showMessage(f"  👤 Đăng nhập: {name} (Quản lý)  |  🕐 {datetime.now().strftime('%H:%M %d/%m/%Y')}")

    # ── HELPER: điền table ────────────────────────────────────────────────────
    @staticmethod
    def _fill_table(table, rows, headers):
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        if len(headers) > 1:
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for r, row_data in enumerate(rows):
            table.insertRow(r)
            for c, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)

    # ══════════════════════════════════════════════════════════════════════════
    #  KHO HÀNG
    # ══════════════════════════════════════════════════════════════════════════
    def load_products(self):
        products = inv.get_all_products()
        self._show_products(products)

    def _show_products(self, products):
        rows = []
        for p in products:
            status = inv.get_product_status(p)
            rows.append([
                p.get("product_id", ""), p.get("name", ""),
                p.get("category", ""), p.get("brand", ""),
                f"{p.get('price', 0):,.0f}đ",
                p.get("stock_quantity", 0), status,
            ])
        self._fill_table(self.ui.tblProducts, rows,
                         ["ID", "Tên sản phẩm", "Danh mục", "Thương hiệu", "Giá", "SL", "Trạng thái"])

    def search_products(self):
        kw = self.ui.txtSearchProduct.text().strip()
        cat_text = self.ui.cboCategory.currentText()
        cat = "" if cat_text in ("Tất cả danh mục", "") else cat_text
        products = inv.search_products(keyword=kw, category=cat)
        self._show_products(products)

    def add_product(self):
        data = self._product_dialog()
        if data:
            pid = inv.add_product(data)
            QMessageBox.information(self, "Thành công", f"✅ Đã thêm sản phẩm {pid}")
            self.load_products()

    def edit_product(self):
        row = self.ui.tblProducts.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm cần sửa!")
            return
        pid = self.ui.tblProducts.item(row, 0).text()
        product = inv.get_product_by_id(pid)
        if not product:
            return
        data = self._product_dialog(product)
        if data:
            inv.update_product(pid, data)
            QMessageBox.information(self, "Thành công", "✅ Đã cập nhật sản phẩm!")
            self.load_products()

    def delete_product(self):
        row = self.ui.tblProducts.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm cần xóa!")
            return
        pid = self.ui.tblProducts.item(row, 0).text()
        name = self.ui.tblProducts.item(row, 1).text()
        reply = QMessageBox.question(self, "Xác nhận", f"Xóa sản phẩm '{name}'?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            inv.delete_product(pid)
            self.load_products()

    def show_low_stock(self):
        products = inv.check_low_stock()
        rows = [(p.get("product_id", ""), p.get("name", ""),
                 p.get("stock_quantity", 0), p.get("min_quantity", 5),
                 "⚠ Cần nhập") for p in products]
        self._fill_table(self.ui.tblProducts, rows,
                         ["ID", "Tên sản phẩm", "Tồn kho", "Tối thiểu", "Ghi chú"])
        self.ui.statusbar.showMessage(f"  ⚠ Có {len(products)} sản phẩm sắp hết hàng")

    def show_expired(self):
        products = inv.check_expired()
        rows = [(p.get("product_id", ""), p.get("name", ""),
                 p.get("exp_date", ""), p.get("days_left", ""),
                 "🔴 Hết hạn" if p.get("days_left", 1) <= 0 else "🟡 Sắp hết hạn")
                for p in products]
        self._fill_table(self.ui.tblProducts, rows,
                         ["ID", "Tên sản phẩm", "Ngày HH", "Còn (ngày)", "Trạng thái"])

    def _product_dialog(self, product=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm sản phẩm" if not product else "Sửa sản phẩm")
        dialog.resize(500, 480)
        layout = QFormLayout(dialog)
        fields = {}
        defaults = product or {}
        for label, key, default in [
            ("Tên sản phẩm *", "name", ""),
            ("Thương hiệu", "brand", ""),
            ("Danh mục", "category", "Skincare"),
            ("Giá (đ) *", "price", "0"),
            ("Số lượng *", "stock_quantity", "0"),
            ("Số lượng tối thiểu", "min_quantity", "5"),
            ("Loại da (cách nhau ;)", "skin-type", ""),
            ("Công dụng (cách nhau ;)", "effects", ""),
            ("Thành phần (cách nhau ;)", "ingredients", ""),
        ]:
            val = defaults.get(key, default)
            if isinstance(val, list):
                val = "; ".join(val)
            le = QLineEdit(str(val))
            layout.addRow(label + ":", le)
            fields[key] = le
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        data = {}
        for key, le in fields.items():
            val = le.text().strip()
            if key in ("skin-type", "effects", "ingredients"):
                data[key] = [v.strip() for v in val.split(";") if v.strip()]
            elif key in ("price", "stock_quantity", "min_quantity"):
                try:
                    data[key] = int(float(val.replace(",", "")))
                except ValueError:
                    data[key] = 0
            else:
                data[key] = val
        if not data.get("name"):
            QMessageBox.warning(self, "Lỗi", "Tên sản phẩm không được để trống!")
            return None
        return data

    # ══════════════════════════════════════════════════════════════════════════
    #  KHÁCH HÀNG
    # ══════════════════════════════════════════════════════════════════════════
    def load_customers(self):
        customers = cust_mod.get_all_customers()
        self._show_customers(customers)

    def _show_customers(self, customers):
        rows = [(c.get("customer_id", ""), c.get("name", ""), c.get("phone", ""),
                 c.get("email", ""), c.get("skin-type", ""),
                 c.get("loyalty_points", 0), c.get("rank", "Đồng")) for c in customers]
        self._fill_table(self.ui.tblCustomers, rows,
                         ["ID", "Họ tên", "SĐT", "Email", "Loại da", "Điểm", "Hạng"])

    def search_customers(self):
        kw = self.ui.txtSearchCustomer.text().strip()
        customers = cust_mod.search_customers(kw)
        self._show_customers(customers)

    def add_customer(self):
        data = self._customer_dialog()
        if data:
            cid = cust_mod.add_customer(data)
            QMessageBox.information(self, "Thành công", f"✅ Đã thêm khách hàng {cid}")
            self.load_customers()

    def edit_customer(self):
        row = self.ui.tblCustomers.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn khách hàng!")
            return
        cid = self.ui.tblCustomers.item(row, 0).text()
        customer = cust_mod.get_customer_by_id(cid)
        data = self._customer_dialog(customer)
        if data:
            cust_mod.update_customer(cid, data)
            self.load_customers()

    def view_customer(self):
        row = self.ui.tblCustomers.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn khách hàng!")
            return
        cid = self.ui.tblCustomers.item(row, 0).text()
        c = cust_mod.get_customer_by_id(cid)
        if not c:
            return
        concerns = ", ".join(c.get("skin_concern", []))
        msg = (f"👤 {c.get('name', '')} ({cid})\n"
               f"📞 SĐT: {c.get('phone', '')}\n"
               f"📧 Email: {c.get('email', '')}\n"
               f"🌸 Loại da: {c.get('skin-type', '')}\n"
               f"⚠ Vấn đề da: {concerns}\n"
               f"🏆 Hạng: {c.get('rank', '')} | Điểm: {c.get('loyalty_points', 0)}")
        QMessageBox.information(self, "Chi tiết khách hàng", msg)

    def _customer_dialog(self, customer=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm khách hàng" if not customer else "Sửa thông tin")
        dialog.resize(440, 400)
        layout = QFormLayout(dialog)
        fields = {}
        defaults = customer or {}
        for label, key, default in [
            ("Họ tên *", "name", ""),
            ("SĐT *", "phone", ""),
            ("Email", "email", ""),
            ("Loại da", "skin-type", ""),
            ("Vấn đề da (cách nhau ;)", "skin_concern", ""),
            ("Hạng (Đồng/Bạc/Vàng)", "rank", "Đồng"),
        ]:
            val = defaults.get(key, default)
            if isinstance(val, list):
                val = "; ".join(val)
            le = QLineEdit(str(val))
            layout.addRow(label + ":", le)
            fields[key] = le
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        data = {}
        for key, le in fields.items():
            val = le.text().strip()
            if key == "skin_concern":
                data[key] = [v.strip() for v in val.split(";") if v.strip()]
            else:
                data[key] = val
        return data if data.get("name") else None

    # ══════════════════════════════════════════════════════════════════════════
    #  ĐƠN HÀNG
    # ══════════════════════════════════════════════════════════════════════════
    def load_orders(self):
        orders = ord_mod.get_all_orders()
        self._show_orders(orders)

    def _show_orders(self, orders):
        customers = cust_mod.get_all_customers()
        cmap = {c["customer_id"]: c["name"] for c in customers}
        rows = []
        for o in reversed(orders):
            cid = o.get("customer_id", "")
            rows.append([
                o.get("order_id", ""),
                cmap.get(cid, cid) or "Khách lẻ",
                o.get("datetime", ""),
                f"{o.get('total', 0):,.0f}đ",
                o.get("status", "Hoàn thành"),
            ])
        self._fill_table(self.ui.tblOrders, rows,
                         ["Mã ĐH", "Khách hàng", "Ngày", "Tổng tiền", "Trạng thái"])

    def find_customer(self):
        phone = self.ui.txtOrderPhone.text().strip()
        if not phone:
            QMessageBox.warning(self, "Chú ý", "Nhập SĐT khách hàng!")
            return
        c = ord_mod.find_customer_by_phone(phone)
        if c:
            self._current_customer = c
            self.ui.txtOrderCustomerName.setText(c.get("name", ""))
            rank = c.get("rank", "")
            discount = ord_mod.DISCOUNT_MAP.get(rank, 0)
            self.ui.lineEdit.setText(f"Giỏ hàng | Hạng: {rank} | Giảm: {int(discount*100)}%")
        else:
            self._current_customer = None
            self.ui.txtOrderCustomerName.setText("Không tìm thấy")
            self.ui.lineEdit.setText("Giỏ hàng: (Khách lẻ)")

    def add_to_cart(self):
        products = inv.get_all_products()
        names = [f"{p.get('product_id','')} - {p.get('name','')} ({p.get('price',0):,.0f}đ)"
                 for p in products if p.get("stock_quantity", 0) > 0]
        if not names:
            QMessageBox.warning(self, "Thông báo", "Không có sản phẩm còn hàng!")
            return
        name, ok = QInputDialog.getItem(self, "Chọn sản phẩm", "Sản phẩm:", names, 0, False)
        if not ok:
            return
        pid = name.split(" - ")[0]
        product = inv.get_product_by_id(pid)
        if not product:
            return
        qty, ok2 = QInputDialog.getInt(self, "Số lượng", f"Số lượng ({product.get('stock_quantity',0)} còn lại):",
                                        1, 1, product.get("stock_quantity", 1))
        if not ok2:
            return
        # Thêm vào giỏ
        for item in self._cart:
            if item["product_id"] == pid:
                item["quantity"] += qty
                self._refresh_cart()
                return
        self._cart.append({
            "product_id": pid,
            "name": product.get("name", pid),
            "price": product.get("price", 0),
            "quantity": qty,
        })
        self._refresh_cart()

    def remove_from_cart(self):
        row = self.ui.tblCart.currentRow()
        if row < 0:
            return
        if row < len(self._cart):
            self._cart.pop(row)
        self._refresh_cart()

    def _refresh_cart(self):
        self.ui.tblCart.setRowCount(0)
        self.ui.tblCart.setColumnCount(3)
        self.ui.tblCart.setHorizontalHeaderLabels(["Sản phẩm", "SL", "Giá"])
        total = 0
        for r, item in enumerate(self._cart):
            self.ui.tblCart.insertRow(r)
            self.ui.tblCart.setItem(r, 0, QTableWidgetItem(item["name"]))
            self.ui.tblCart.setItem(r, 1, QTableWidgetItem(str(item["quantity"])))
            line_total = item["price"] * item["quantity"]
            self.ui.tblCart.setItem(r, 2, QTableWidgetItem(f"{line_total:,.0f}đ"))
            total += line_total
        discount_rate = ord_mod.DISCOUNT_MAP.get(
            self._current_customer.get("rank", "") if self._current_customer else "", 0)
        final = total * (1 - discount_rate)
        self.ui.lblTotal.setText(
            f"💰 Tạm tính: {total:,.0f}đ  |  Giảm ({int(discount_rate*100)}%): -{total*discount_rate:,.0f}đ  |  TỔNG: {final:,.0f}đ")

    def checkout(self):
        if not self._cart:
            QMessageBox.warning(self, "Chú ý", "Giỏ hàng trống!")
            return
        cid = self._current_customer.get("customer_id") if self._current_customer else ""
        order, err = ord_mod.create_order(cid, self._cart)
        if err:
            QMessageBox.warning(self, "Lỗi", f"Không thể tạo đơn hàng:\n{err}")
            return
        self._cart = []
        self._refresh_cart()
        self._current_customer = None
        self.ui.txtOrderPhone.clear()
        self.ui.txtOrderCustomerName.clear()
        self.ui.lineEdit.setText("Giỏ hàng:")
        QMessageBox.information(self, "Thành công",
                                 f"✅ Đơn hàng {order['order_id']} đã được tạo!\n"
                                 f"💰 Tổng: {order['total']:,.0f}đ")
        self.load_orders()
        self.load_products()

    def new_order(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tabOrders)
        self._cart = []
        self._refresh_cart()
        self.ui.txtOrderPhone.setFocus()

    def view_order(self):
        row = self.ui.tblOrders.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn đơn hàng!")
            return
        oid = self.ui.tblOrders.item(row, 0).text()
        order = ord_mod.get_order_by_id(oid)
        if not order:
            return
        items_str = "\n".join(
            f"  • {it.get('name', it['product_id'])} x{it['quantity']} = {it['price']*it['quantity']:,.0f}đ"
            for it in order.get("items", []))
        msg = (f"📋 Đơn hàng: {oid}\n"
               f"📅 Ngày: {order.get('datetime','')}\n"
               f"👤 Khách: {order.get('customer_id','')}\n\n"
               f"📦 Sản phẩm:\n{items_str}\n\n"
               f"💰 Tổng: {order.get('total',0):,.0f}đ\n"
               f"🔖 Trạng thái: {order.get('status','')}")
        QMessageBox.information(self, "Chi tiết đơn hàng", msg)

    def print_invoice(self):
        """In hóa đơn dạng text ra màn hình."""
        row = self.ui.tblOrders.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn đơn hàng!")
            return
        oid = self.ui.tblOrders.item(row, 0).text()
        order = ord_mod.get_order_by_id(oid)
        if not order:
            return
        products = inv.get_all_products()
        pmap = {p["product_id"]: p for p in products}
        lines = [
            "=" * 50,
            "     🧴 NHÓM 6 - BEAUTY STORE",
            "         Hóa đơn bán hàng",
            "=" * 50,
            f"Mã ĐH: {order.get('order_id','')}",
            f"Ngày: {order.get('datetime','')}",
            "-" * 50,
        ]
        for it in order.get("items", []):
            p = pmap.get(it["product_id"], {})
            lines.append(f"  {p.get('name', it['product_id'])}")
            lines.append(f"    {it['quantity']} x {it['price']:,.0f}đ = {it['price']*it['quantity']:,.0f}đ")
        lines += [
            "-" * 50,
            f"  Tổng:  {order.get('total',0):,.0f}đ",
            "=" * 50,
            "  Cảm ơn bạn đã mua hàng! 💖",
        ]
        QMessageBox.information(self, "Hóa đơn", "\n".join(lines))

    def export_excel(self):
        """Xuất hóa đơn Excel."""
        row = self.ui.tblOrders.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn đơn hàng để xuất Excel!")
            return
        oid = self.ui.tblOrders.item(row, 0).text()
        order = ord_mod.get_order_by_id(oid)
        if not order:
            return
        customer = cust_mod.get_customer_by_id(order.get("customer_id", ""))
        products = inv.get_all_products()
        pmap = {p["product_id"]: p for p in products}
        try:
            path = excel_export.export_invoice_excel(order, customer, pmap)
            QMessageBox.information(self, "Xuất Excel thành công",
                                     f"✅ Hóa đơn đã được xuất:\n{path}")
            os.startfile(path) if sys.platform == "win32" else None
        except RuntimeError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất Excel:\n{str(e)}")

    # ══════════════════════════════════════════════════════════════════════════
    #  GỢI Ý SẢN PHẨM
    # ══════════════════════════════════════════════════════════════════════════
    def get_recommendations(self):
        skin_type = self.ui.cboSkinType.currentText().lower()
        concerns_text = self.ui.txtSkinConcerns.text().strip()
        concerns = [c.strip() for c in concerns_text.split(",") if c.strip()]
        from modules.chatbot import extract_effects
        effects = extract_effects(concerns) if concerns else []
        products = rec.recommendation(skin_type=skin_type, effects=effects, limit=10)
        self._show_recommend(products)

    def get_routine(self):
        skin_type = self.ui.cboSkinType.currentText().lower()
        concerns_text = self.ui.txtSkinConcerns.text().strip()
        concerns = [c.strip() for c in concerns_text.split(",") if c.strip()]
        routine = rec.recommend_skincare_routine(skin_type, concerns)
        rows = []
        for step in routine:
            p = step.get("product", {})
            rows.append([
                p.get("product_id", ""),
                f"[{step['step']}] {p.get('name', '')}",
                p.get("category", ""),
                f"{p.get('price',0):,.0f}đ",
                ", ".join(p.get("effects", [])),
            ])
        self._fill_table(self.ui.tblRecommend, rows,
                         ["ID", "Bước - Sản phẩm", "Danh mục", "Giá", "Công dụng"])

    def _show_recommend(self, products):
        rows = [(p.get("product_id",""), p.get("name",""), p.get("category",""),
                 f"{p.get('price',0):,.0f}đ", ", ".join(p.get("effects",[])))
                for p in products]
        self._fill_table(self.ui.tblRecommend, rows,
                         ["ID", "Tên sản phẩm", "Danh mục", "Giá", "Công dụng"])

    # ══════════════════════════════════════════════════════════════════════════
    #  CHATBOT
    # ══════════════════════════════════════════════════════════════════════════
    def send_chat(self):
        msg = self.ui.txtChatInput.text().strip()
        if not msg:
            return
        self.ui.txtChatInput.clear()
        self.ui.txtChatHistory.append(f'<p><b style="color:#e91e63;">👤 Bạn:</b> {msg}</p>')
        response = bot.generate_response(msg, self._chat_context)
        html_resp = response.replace("\n", "<br/>")
        self.ui.txtChatHistory.append(
            f'<p><b style="color:#7b1fa2;">🤖 Bot:</b> {html_resp}</p>')
        sb = self.ui.txtChatHistory.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_chat(self):
        self._chat_context = bot.new_context()
        self.ui.txtChatHistory.setHtml(
            '<p><b style="color:#7b1fa2;">🤖 Bot:</b> Cuộc trò chuyện đã được xóa. '
            'Xin chào! Tôi là trợ lý tư vấn mỹ phẩm AI. '
            'Bạn có thể cho tôi biết loại da không?</p>')

    # ══════════════════════════════════════════════════════════════════════════
    #  THỐNG KÊ & XUẤT EXCEL
    # ══════════════════════════════════════════════════════════════════════════
    def load_analytics(self):
        summary = ana.get_summary()
        self.ui.lblTotalProducts.setText(f"📦 Tổng sản phẩm: {summary['total_products']}")
        self.ui.lblTotalCustomers.setText(f"👥 Tổng khách hàng: {summary['total_customers']}")
        self.ui.lblTotalOrders.setText(f"🛒 Tổng đơn hàng: {summary['total_orders']}")
        self.ui.lblTotalRevenue.setText(f"💰 Tổng doanh thu: {summary['total_revenue']:,.0f}đ")

        top = ana.get_top_products()
        rows = [(i + 1, p["name"], p["sold"], f"{p['revenue']:,.0f}đ")
                for i, p in enumerate(top)]
        self._fill_table(self.ui.tblTopProducts, rows,
                         ["Hạng", "Sản phẩm", "Đã bán", "Doanh thu"])

        low = ana.get_low_stock_products()
        rows2 = [("⚠ Sắp hết", p.get("name", ""),
                  p.get("stock_quantity", 0), p.get("min_quantity", 5),
                  max(0, p.get("min_quantity", 5) * 3 - p.get("stock_quantity", 0)))
                 for p in low]
        self._fill_table(self.ui.tblLowStock, rows2,
                         ["Trạng thái", "Sản phẩm", "Tồn kho", "Tối thiểu", "Đề xuất nhập"])

    def export_excel(self):
        """Xuất báo cáo doanh thu Excel."""
        try:
            orders = ord_mod.get_all_orders()
            products = inv.get_all_products()
            pmap = {p["product_id"]: p for p in products}
            customers = cust_mod.get_all_customers()
            cmap = {c["customer_id"]: c for c in customers}
            path = excel_export.export_revenue_excel(orders, pmap, cmap)
            QMessageBox.information(self, "Xuất Excel thành công",
                                     f"✅ Báo cáo đã được lưu:\n{path}")
            os.startfile(path) if sys.platform == "win32" else None
        except RuntimeError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất Excel:\n{str(e)}")

    # ══════════════════════════════════════════════════════════════════════════
    #  NHÂN VIÊN
    # ══════════════════════════════════════════════════════════════════════════
    def load_staffs(self):
        staffs = staff_mod.get_all_staffs()
        self._show_staffs(staffs)

    def _show_staffs(self, staffs):
        rows = [(s.get("staff_id",""), s.get("name",""), s.get("phone",""),
                 s.get("role",""), s.get("shift_id",""), s.get("salary",0),
                 s.get("status","")) for s in staffs]
        self._fill_table(self.ui.tblStaff, rows,
                         ["ID", "Họ tên", "SĐT", "Chức vụ", "Ca làm", "Lương", "Trạng thái"])

    def search_staffs(self):
        kw = self.ui.txtSearchStaff.text().strip()
        role_text = self.ui.cboStaffRole.currentText()
        role = "" if role_text == "Tất cả chức vụ" else role_text
        staffs = staff_mod.search_staffs(kw, role)
        self._show_staffs(staffs)

    def add_staff(self):
        data = self._staff_dialog()
        if data:
            sid = staff_mod.add_staff(data)
            QMessageBox.information(self, "Thành công", f"✅ Đã thêm nhân viên {sid}")
            self.load_staffs()

    def edit_staff(self):
        row = self.ui.tblStaff.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn nhân viên!")
            return
        sid = self.ui.tblStaff.item(row, 0).text()
        staff = staff_mod.get_staff_by_id(sid)
        data = self._staff_dialog(staff)
        if data:
            staff_mod.update_staff(sid, data)
            self.load_staffs()

    def delete_staff(self):
        row = self.ui.tblStaff.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn nhân viên!")
            return
        sid = self.ui.tblStaff.item(row, 0).text()
        name = self.ui.tblStaff.item(row, 1).text()
        reply = QMessageBox.question(self, "Xác nhận", f"Xóa nhân viên '{name}'?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            staff_mod.delete_staff(sid)
            self.load_staffs()

    def assign_shift(self):
        row = self.ui.tblStaff.currentRow()
        if row < 0:
            return
        sid = self.ui.tblStaff.item(row, 0).text()
        shifts = ["Ca sáng (6h-14h)", "Ca chiều (14h-22h)", "Ca đêm (22h-6h)"]
        shift, ok = QInputDialog.getItem(self, "Phân ca", "Chọn ca làm:", shifts, 0, False)
        if ok:
            staff_mod.assign_shift(sid, shift)
            self.load_staffs()

    def _staff_dialog(self, staff=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm nhân viên" if not staff else "Sửa nhân viên")
        layout = QFormLayout(dialog)
        fields = {}
        defaults = staff or {}
        for label, key, default in [
            ("Họ tên *", "name", ""),
            ("SĐT", "phone", ""),
            ("Chức vụ", "role", "Sales"),
            ("Lương", "salary", "0"),
            ("Trạng thái", "status", "Đang làm"),
        ]:
            le = QLineEdit(str(defaults.get(key, default)))
            layout.addRow(label + ":", le)
            fields[key] = le
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        data = {k: le.text().strip() for k, le in fields.items()}
        try:
            data["salary"] = int(data.get("salary", 0))
        except ValueError:
            data["salary"] = 0
        return data if data.get("name") else None
