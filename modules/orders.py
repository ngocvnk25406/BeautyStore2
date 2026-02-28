"""
orders.py - Xử lý đơn hàng, giỏ hàng, thanh toán
"""
from datetime import datetime
from modules.data_handler import load_orders, save_orders, load_customers, generate_order_id
from modules.inventory import deduct_stock

DISCOUNT_MAP = {
    "Vàng": 0.10,
    "Bạc": 0.08,
    "Đồng": 0.05,
}

LOYALTY_RATE = 10_000  # 1 điểm / 10,000đ


def get_all_orders():
    return load_orders()


def get_order_by_id(order_id):
    orders = load_orders()
    return next((o for o in orders if o.get("order_id") == order_id), None)


def get_orders_by_customer(customer_id):
    orders = load_orders()
    return [o for o in orders if o.get("customer_id") == customer_id]


def find_customer_by_phone(phone):
    customers = load_customers()
    return next((c for c in customers if c.get("phone") == phone.strip()), None)


def calculate_total(items, discount_rate=0.0):
    """Tính tổng tiền sau khi áp dụng giảm giá."""
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    discount = subtotal * discount_rate
    return subtotal, discount, subtotal - discount


def create_order(customer_id, items, staff_id="S01"):
    """Tạo đơn hàng mới và trừ kho."""
    orders = load_orders()
    customers = load_customers()

    customer = next((c for c in customers if c.get("customer_id") == customer_id), None)
    discount_rate = DISCOUNT_MAP.get(customer.get("rank", ""), 0.0) if customer else 0.0

    subtotal, discount, total = calculate_total(items, discount_rate)

    # Trừ kho
    failed = []
    for item in items:
        ok, msg = deduct_stock(item["product_id"], item["quantity"])
        if not ok:
            failed.append(f"{item.get('name', item['product_id'])}: {msg}")
    if failed:
        return None, "\n".join(failed)

    order_id = generate_order_id(orders)
    order = {
        "order_id": order_id,
        "datetime": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "customer_id": customer_id or "",
        "staff_id": staff_id,
        "items": [{"product_id": it["product_id"], "quantity": it["quantity"],
                   "price": it["price"], "name": it.get("name", "")} for it in items],
        "subtotal": subtotal,
        "discount_rate": discount_rate,
        "discount": discount,
        "total": total,
        "status": "Hoàn thành",
    }
    orders.append(order)
    save_orders(orders)

    # Cộng điểm tích lũy
    if customer:
        points_earned = int(total // LOYALTY_RATE)
        _update_loyalty(customer_id, points_earned, total)

    return order, None


def _update_loyalty(customer_id, points_earned, total_spent):
    from modules.data_handler import save_customers
    customers = load_customers()
    for c in customers:
        if c.get("customer_id") == customer_id:
            c["loyalty_points"] = c.get("loyalty_points", 0) + points_earned
            pts = c["loyalty_points"]
            if pts >= 5000:
                c["rank"] = "Vàng"
            elif pts >= 2000:
                c["rank"] = "Bạc"
            else:
                c["rank"] = "Đồng"
            break
    save_customers(customers)


def cancel_order(order_id):
    """Hủy đơn hàng (hoàn trả kho)."""
    from modules.inventory import restore_stock
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            if o.get("status") == "Đã hủy":
                return False, "Đơn hàng đã hủy rồi"
            for item in o.get("items", []):
                restore_stock(item["product_id"], item["quantity"])
            o["status"] = "Đã hủy"
            save_orders(orders)
            return True, "Hủy thành công"
    return False, "Không tìm thấy đơn hàng"


def get_revenue_by_period(orders=None):
    """Tổng hợp doanh thu từ danh sách đơn hàng."""
    if orders is None:
        orders = load_orders()
    active = [o for o in orders if o.get("status") != "Đã hủy"]
    total = sum(o.get("total", 0) for o in active)
    return total, len(active)
