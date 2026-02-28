"""
customers.py - Quản lý khách hàng (CRUD + loyalty)
"""
from modules.data_handler import load_customers, save_customers, generate_customer_id

DISCOUNT_MAP = {"Vàng": 0.10, "Bạc": 0.08, "Đồng": 0.05}


def get_all_customers():
    return load_customers()


def get_customer_by_id(customer_id):
    customers = load_customers()
    return next((c for c in customers if c.get("customer_id") == customer_id), None)


def get_customer_by_phone(phone):
    customers = load_customers()
    return next((c for c in customers if c.get("phone") == phone.strip()), None)


def search_customers(keyword=""):
    """Tìm theo tên hoặc SĐT."""
    customers = load_customers()
    kw = keyword.lower().strip()
    if not kw:
        return customers
    return [
        c for c in customers
        if kw in c.get("name", "").lower() or kw in c.get("phone", "")
    ]


def add_customer(data: dict):
    """Thêm khách hàng mới."""
    customers = load_customers()
    if "customer_id" not in data or not data["customer_id"]:
        data["customer_id"] = generate_customer_id(customers)
    if "loyalty_points" not in data:
        data["loyalty_points"] = 0
    if "rank" not in data:
        data["rank"] = "Đồng"
    customers.append(data)
    save_customers(customers)
    return data["customer_id"]


def update_customer(customer_id, updated_data: dict):
    """Cập nhật thông tin khách hàng."""
    customers = load_customers()
    for i, c in enumerate(customers):
        if c.get("customer_id") == customer_id:
            customers[i].update(updated_data)
            save_customers(customers)
            return True
    return False


def delete_customer(customer_id):
    customers = load_customers()
    new_list = [c for c in customers if c.get("customer_id") != customer_id]
    if len(new_list) < len(customers):
        save_customers(new_list)
        return True
    return False


def get_discount_rate(customer_id):
    """Lấy % giảm giá theo hạng khách hàng."""
    c = get_customer_by_id(customer_id)
    if not c:
        return 0.0
    return DISCOUNT_MAP.get(c.get("rank", ""), 0.0)
