"""
customer_window.py - Logic cửa sổ khách hàng
Tính năng: xem SP, tìm kiếm, chi tiết SP, gợi ý theo da, chatbot,
           giỏ hàng, đặt hàng, lịch sử đơn hàng
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QDialog, QVBoxLayout, QLabel,
    QTableWidgetItem, QHeaderView, QInputDialog, QTextEdit
)
from PyQt6.QtCore import Qt

from ui.customer_ui import Ui_CustomerWindow
from modules import (
    inventory as inv,
    orders as ord_mod,
    customers as cust_mod,
    chatbot as bot,
    recommendation as rec,
)


class CustomerWindow(QMainWindow):
    def __init__(self, account: dict):
        super().__init__()
        self.account = account
        self.customer_id = account.get("customer_id", "")
        self.customer = cust_mod.get_customer_by_id(self.customer_id) if self.customer_id else {}
        self.ui = Ui_CustomerWindow()
        self.ui.setupUi(self)
        self._cart = []          # [{"product_id", "name", "price", "quantity"}]
        self._chat_context = bot.new_context()
        self._selected_product = None   # sản phẩm đang xem chi tiết
        self._connect_signals()
        self._load_all()

    # ── Kết nối sự kiện ──────────────────────────────────────────────────────
    def _connect_signals(self):
        u = self.ui
        # Tab Sản phẩm
        u.btnViewDetail.clicked.connect(self.view_product_detail)
        u.btnAddToCartFromList.clicked.connect(self.add_to_cart_from_list)
        u.btnRefreshProducts.clicked.connect(self.load_products)
        u.tblProductList.doubleClicked.connect(self.view_product_detail)
        # Tab Tìm kiếm
        u.btnSearch.clicked.connect(self.search_products)
        u.txtSearchKeyword.returnPressed.connect(self.search_products)
        u.btnSearchViewDetail.clicked.connect(self.search_view_detail)
        u.btnSearchAddCart.clicked.connect(self.search_add_cart)
        # Tab Chi tiết SP
        u.btnDetailAddCart.clicked.connect(self.detail_add_cart)
        # Tab Gợi ý theo da
        u.btnGetMyRecommend.clicked.connect(self.get_my_recommend)
        u.btnGetMyRoutine.clicked.connect(self.get_my_routine)
        u.btnRecAddCart.clicked.connect(self.rec_add_cart)
        # Tab Chatbot
        u.btnSendChat.clicked.connect(self.send_chat)
        u.btnClearChat.clicked.connect(self.clear_chat)
        u.txtChatInput.returnPressed.connect(self.send_chat)
        # Quick buttons
        for btn in u.tabChatbot.findChildren(__import__("PyQt6.QtWidgets", fromlist=["QPushButton"]).QPushButton):
            if btn.objectName().startswith("quickBtn_"):
                text = btn.objectName().replace("quickBtn_", "").replace("_", " ")
                btn.clicked.connect(lambda checked, t=text: self._quick_chat(t))
        # Tab Giỏ hàng
        u.btnCartRemove.clicked.connect(self.cart_remove)
        u.btnCartClear.clicked.connect(self.cart_clear)
        u.btnPlaceOrder.clicked.connect(self.place_order)
        # Tab Lịch sử
        u.btnViewHistoryDetail.clicked.connect(self.view_history_detail)
        u.btnRefreshHistory.clicked.connect(self.load_order_history)

    def _load_all(self):
        self.load_products()
        self.load_order_history()
        self._prefill_skin_info()
        name = self.account.get("full_name", "Khách hàng")
        rank = self.customer.get("rank", "Đồng") if self.customer else ""
        points = self.customer.get("loyalty_points", 0) if self.customer else 0
        self.ui.statusbar.showMessage(
            f"  👤 Xin chào, {name}!  |  🏆 Hạng: {rank}  |  ⭐ Điểm: {points}")
        self.ui.lblTitle.setText(
            f'<div style="text-align:center; font-size:20px; font-weight:bold; color:#e91e63;">'
            f'🧴 NHÓM 6 - BEAUTY STORE - Xin chào, {name}! 💖</div>')

    # ── HELPER ───────────────────────────────────────────────────────────────
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

    def _get_selected_product_from_table(self, table):
        row = table.currentRow()
        if row < 0:
            return None
        pid_item = table.item(row, 0)
        if not pid_item:
            return None
        return inv.get_product_by_id(pid_item.text())

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB SẢN PHẨM
    # ══════════════════════════════════════════════════════════════════════════
    def load_products(self):
        products = inv.get_all_products()
        rows = [(p.get("product_id",""), p.get("name",""), p.get("brand",""),
                 p.get("category",""), f"{p.get('price',0):,.0f}đ",
                 "Còn hàng" if p.get("stock_quantity",0) > 0 else "Hết hàng")
                for p in products]
        self._fill_table(self.ui.tblProductList, rows,
                         ["ID", "Tên sản phẩm", "Thương hiệu", "Danh mục", "Giá", "Tình trạng"])

    def view_product_detail(self):
        p = self._get_selected_product_from_table(self.ui.tblProductList)
        if not p:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm!")
            return
        self._show_product_detail(p)
        self.ui.tabWidget.setCurrentWidget(self.ui.tabProductDetail)

    def add_to_cart_from_list(self):
        p = self._get_selected_product_from_table(self.ui.tblProductList)
        if not p:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm!")
            return
        self._add_product_to_cart(p, 1)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB TÌM KIẾM
    # ══════════════════════════════════════════════════════════════════════════
    def search_products(self):
        kw = self.ui.txtSearchKeyword.text().strip()
        cat_text = self.ui.cboSearchCategory.currentText()
        cat = "" if cat_text == "Tất cả" else cat_text

        # Lọc giá
        price_text = self.ui.cboSearchPrice.currentText()
        products = inv.search_products(keyword=kw, category=cat)

        if "Dưới 200,000đ" in price_text:
            products = [p for p in products if p.get("price", 0) < 200_000]
        elif "200,000 - 400,000đ" in price_text:
            products = [p for p in products if 200_000 <= p.get("price", 0) <= 400_000]
        elif "Trên 400,000đ" in price_text:
            products = [p for p in products if p.get("price", 0) > 400_000]

        rows = [(p.get("product_id",""), p.get("name",""), p.get("brand",""),
                 p.get("category",""), f"{p.get('price',0):,.0f}đ",
                 "Còn hàng" if p.get("stock_quantity",0) > 0 else "Hết hàng")
                for p in products]
        self._fill_table(self.ui.tblSearchResult, rows,
                         ["ID", "Tên sản phẩm", "Thương hiệu", "Danh mục", "Giá", "Tình trạng"])
        self.ui.lblSearchCount.setText(f"Kết quả: {len(products)} sản phẩm")

    def search_view_detail(self):
        p = self._get_selected_product_from_table(self.ui.tblSearchResult)
        if not p:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm!")
            return
        self._show_product_detail(p)
        self.ui.tabWidget.setCurrentWidget(self.ui.tabProductDetail)

    def search_add_cart(self):
        p = self._get_selected_product_from_table(self.ui.tblSearchResult)
        if not p:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm!")
            return
        self._add_product_to_cart(p, 1)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB CHI TIẾT SẢN PHẨM
    # ══════════════════════════════════════════════════════════════════════════
    def _show_product_detail(self, product):
        self._selected_product = product
        u = self.ui
        u.lblProductName.setText(product.get("name", ""))
        u.lblDetailBrand.setText(product.get("brand", ""))
        u.lblDetailCategory.setText(product.get("category", ""))
        u.lblDetailPrice.setText(f"{product.get('price', 0):,.0f}đ")
        stock = product.get("stock_quantity", 0)
        u.lblDetailStock.setText(f"{stock} sản phẩm" + (" (Hết hàng)" if stock == 0 else ""))
        u.lblDetailSkinType.setText(", ".join(product.get("skin-type", [])))
        u.lblDetailEffects.setText(", ".join(product.get("effects", [])))
        u.lblDetailIngredients.setText(", ".join(product.get("ingredients", [])))
        u.spinDetailQty.setMaximum(max(1, stock))
        u.btnDetailAddCart.setEnabled(stock > 0)

        # Sản phẩm tương tự
        related = rec.recommend_by_skin_type(
            (product.get("skin-type") or ["mọi loại da"])[0], limit=6)
        related = [p for p in related if p.get("product_id") != product.get("product_id")][:5]
        rows = [(p.get("name",""), p.get("brand",""),
                 f"{p.get('price',0):,.0f}đ", ", ".join(p.get("effects",[])))
                for p in related]
        self._fill_table(u.tblRelated, rows, ["Tên", "Thương hiệu", "Giá", "Công dụng"])

    def detail_add_cart(self):
        if not self._selected_product:
            return
        qty = self.ui.spinDetailQty.value()
        self._add_product_to_cart(self._selected_product, qty)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB GỢI Ý THEO DA
    # ══════════════════════════════════════════════════════════════════════════
    def _prefill_skin_info(self):
        """Điền thông tin da sẵn từ hồ sơ khách hàng."""
        if not self.customer:
            return
        skin_type = self.customer.get("skin-type", "")
        concerns = self.customer.get("skin_concern", [])
        # Tìm và set combobox
        cbo = self.ui.cboMySkinType
        for i in range(cbo.count()):
            if skin_type.lower() in cbo.itemText(i).lower():
                cbo.setCurrentIndex(i)
                break
        self.ui.txtMySkinConcerns.setText(", ".join(concerns))

    def get_my_recommend(self):
        skin_type = self.ui.cboMySkinType.currentText()
        if skin_type.startswith("--"):
            skin_type = ""
        concerns_text = self.ui.txtMySkinConcerns.text().strip()
        concerns = [c.strip() for c in concerns_text.split(",") if c.strip()]
        from modules.chatbot import extract_effects
        effects = extract_effects(concerns)
        products = rec.recommendation(skin_type=skin_type.lower(), effects=effects, limit=10)
        self._show_my_recommend(products)

    def get_my_routine(self):
        skin_type = self.ui.cboMySkinType.currentText()
        if skin_type.startswith("--"):
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn loại da trước!")
            return
        concerns_text = self.ui.txtMySkinConcerns.text().strip()
        concerns = [c.strip() for c in concerns_text.split(",") if c.strip()]
        routine = rec.recommend_skincare_routine(skin_type.lower(), concerns)
        rows = []
        for step in routine:
            p = step.get("product", {})
            rows.append([
                p.get("product_id", ""),
                f"[{step['step']}] {p.get('name', '')}",
                p.get("brand",""),
                f"{p.get('price',0):,.0f}đ",
                ", ".join(p.get("effects", [])),
            ])
        self._fill_table(self.ui.tblMyRecommend, rows,
                         ["ID", "Bước - Sản phẩm", "Thương hiệu", "Giá", "Công dụng"])

    def _show_my_recommend(self, products):
        rows = [(p.get("product_id",""), p.get("name",""), p.get("brand",""),
                 f"{p.get('price',0):,.0f}đ", ", ".join(p.get("effects",[])))
                for p in products]
        self._fill_table(self.ui.tblMyRecommend, rows,
                         ["ID", "Tên sản phẩm", "Thương hiệu", "Giá", "Công dụng"])

    def rec_add_cart(self):
        p = self._get_selected_product_from_table(self.ui.tblMyRecommend)
        if not p:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn sản phẩm!")
            return
        self._add_product_to_cart(p, 1)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB CHATBOT
    # ══════════════════════════════════════════════════════════════════════════
    def send_chat(self):
        msg = self.ui.txtChatInput.text().strip()
        if not msg:
            return
        self._process_chat(msg)

    def _quick_chat(self, text):
        self.ui.txtChatInput.setText(text)
        self._process_chat(text)

    def _process_chat(self, msg):
        self.ui.txtChatInput.clear()
        self.ui.txtChatHistory.append(
            f'<p><b style="color:#e91e63;">👤 Bạn:</b> {msg}</p>')
        response = bot.generate_response(msg, self._chat_context)
        html = response.replace("\n", "<br/>")
        self.ui.txtChatHistory.append(
            f'<p><b style="color:#7b1fa2;">🤖 Bot:</b> {html}</p>')
        sb = self.ui.txtChatHistory.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_chat(self):
        self._chat_context = bot.new_context()
        self.ui.txtChatHistory.setHtml(
            '<p><b style="color:#7b1fa2;">🤖 Bot:</b> '
            'Cuộc trò chuyện đã được làm mới! 😊<br/>'
            'Hãy cho tôi biết loại da của bạn để bắt đầu tư vấn nhé!</p>')

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB GIỎ HÀNG
    # ══════════════════════════════════════════════════════════════════════════
    def _add_product_to_cart(self, product, quantity):
        pid = product.get("product_id", "")
        stock = product.get("stock_quantity", 0)
        if stock == 0:
            QMessageBox.warning(self, "Thông báo", "Sản phẩm này đã hết hàng!")
            return
        for item in self._cart:
            if item["product_id"] == pid:
                new_qty = item["quantity"] + quantity
                if new_qty > stock:
                    QMessageBox.warning(self, "Thông báo",
                                         f"Chỉ còn {stock} sản phẩm trong kho!")
                    return
                item["quantity"] = new_qty
                self._refresh_cart()
                self.ui.statusbar.showMessage(f"  ✅ Đã cập nhật giỏ hàng: {product.get('name','')}")
                return
        self._cart.append({
            "product_id": pid,
            "name": product.get("name", pid),
            "price": product.get("price", 0),
            "quantity": quantity,
        })
        self._refresh_cart()
        self.ui.statusbar.showMessage(f"  ✅ Đã thêm vào giỏ: {product.get('name','')}")
        # Chuyển sang tab giỏ hàng sau khi thêm lần đầu (optional)

    def _refresh_cart(self):
        u = self.ui
        u.tblCart.setRowCount(0)
        u.tblCart.setColumnCount(5)
        u.tblCart.setHorizontalHeaderLabels(["ID", "Tên sản phẩm", "Đơn giá", "SL", "Thành tiền"])
        u.tblCart.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        subtotal = 0
        for r, item in enumerate(self._cart):
            u.tblCart.insertRow(r)
            line = item["price"] * item["quantity"]
            subtotal += line
            for c, val in enumerate([
                item["product_id"], item["name"],
                f"{item['price']:,.0f}đ", str(item["quantity"]),
                f"{line:,.0f}đ"
            ]):
                wi = QTableWidgetItem(val)
                wi.setFlags(wi.flags() & ~Qt.ItemFlag.ItemIsEditable)
                u.tblCart.setItem(r, c, wi)

        discount_rate = ord_mod.DISCOUNT_MAP.get(self.customer.get("rank", "") if self.customer else "", 0)
        discount = subtotal * discount_rate
        total = subtotal - discount
        u.lblCartSubtotal.setText(f"Tạm tính: {subtotal:,.0f}đ")
        u.lblCartDiscount.setText(f"Giảm giá ({int(discount_rate*100)}%): -{discount:,.0f}đ")
        u.lblCartTotal.setText(f"💰 TỔNG: {total:,.0f}đ")

    def cart_remove(self):
        row = self.ui.tblCart.currentRow()
        if row < 0:
            return
        if row < len(self._cart):
            self._cart.pop(row)
        self._refresh_cart()

    def cart_clear(self):
        if self._cart:
            reply = QMessageBox.question(self, "Xác nhận", "Xóa tất cả sản phẩm trong giỏ?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._cart = []
                self._refresh_cart()

    def place_order(self):
        if not self._cart:
            QMessageBox.warning(self, "Thông báo", "Giỏ hàng đang trống!")
            return
        reply = QMessageBox.question(
            self, "Xác nhận đặt hàng",
            f"Bạn muốn đặt {len(self._cart)} sản phẩm?\n"
            f"Tổng tiền sẽ được tính sau khi xác nhận.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        order, err = ord_mod.create_order(self.customer_id, self._cart)
        if err:
            QMessageBox.warning(self, "Lỗi đặt hàng", f"❌ {err}")
            return
        self._cart = []
        self._refresh_cart()
        # Cập nhật thông tin khách hàng
        self.customer = cust_mod.get_customer_by_id(self.customer_id) or self.customer
        QMessageBox.information(
            self, "Đặt hàng thành công!",
            f"✅ Đơn hàng {order['order_id']} đã được tạo!\n\n"
            f"💰 Tổng thanh toán: {order['total']:,.0f}đ\n"
            f"📅 Ngày đặt: {order['datetime']}\n\n"
            "Cảm ơn bạn đã mua sắm ! 💖"
        )
        self.load_order_history()
        self.ui.tabWidget.setCurrentWidget(self.ui.tabOrderHistory)
        self.ui.statusbar.showMessage(
            f"  ✅ Đặt hàng thành công!  |  🏆 Hạng: {self.customer.get('rank','')}  |  "
            f"⭐ Điểm: {self.customer.get('loyalty_points', 0)}")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB LỊCH SỬ ĐƠN HÀNG
    # ══════════════════════════════════════════════════════════════════════════
    def load_order_history(self):
        if not self.customer_id:
            return
        orders = ord_mod.get_orders_by_customer(self.customer_id)
        orders = list(reversed(orders))
        rows = [(o.get("order_id",""), o.get("datetime",""),
                 len(o.get("items",[])), f"{o.get('total',0):,.0f}đ",
                 o.get("status","Hoàn thành"))
                for o in orders]
        self._fill_table(self.ui.tblOrderHistory, rows,
                         ["Mã đơn", "Ngày đặt", "Số SP", "Tổng tiền", "Trạng thái"])
        total_spent = sum(o.get("total", 0) for o in orders if o.get("status") != "Đã hủy")
        self.ui.lblHistoryTotal.setText(
            f"Tổng chi tiêu: {total_spent:,.0f}đ  |  Số đơn: {len(orders)}")

    def view_history_detail(self):
        row = self.ui.tblOrderHistory.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn đơn hàng!")
            return
        oid = self.ui.tblOrderHistory.item(row, 0).text()
        order = ord_mod.get_order_by_id(oid)
        if not order:
            return
        products = inv.get_all_products()
        pmap = {p["product_id"]: p for p in products}
        items_str = "\n".join(
            f"  • {pmap.get(it['product_id'],{}).get('name', it['product_id'])}"
            f"  x{it['quantity']}  =  {it['price']*it['quantity']:,.0f}đ"
            for it in order.get("items", []))
        discount = order.get("discount", 0)
        msg = (f"📋 ĐƠN HÀNG: {oid}\n"
               f"📅 Ngày: {order.get('datetime','')}\n"
               f"🔖 Trạng thái: {order.get('status','')}\n\n"
               f"📦 Sản phẩm:\n{items_str}\n\n"
               f"Tạm tính: {order.get('subtotal', order.get('total',0)):,.0f}đ\n"
               f"Giảm giá: -{discount:,.0f}đ\n"
               f"💰 Tổng: {order.get('total',0):,.0f}đ")
        QMessageBox.information(self, "Chi tiết đơn hàng", msg)
