"""
data_handler.py - Tiện ích đọc/ghi JSON và sinh ID tự động
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    """Đọc file JSON từ thư mục data."""
    path = DATA_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(filename, data):
    """Ghi dữ liệu vào file JSON trong thư mục data."""
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_products():
    return load_json("products.json")


def save_products(data):
    save_json("products.json", data)


def load_customers():
    return load_json("customers.json")


def save_customers(data):
    save_json("customers.json", data)


def load_orders():
    return load_json("orders.json")


def save_orders(data):
    save_json("orders.json", data)


def load_staffs():
    return load_json("staffs.json")


def save_staffs(data):
    save_json("staffs.json", data)


def load_accounts():
    return load_json("accounts.json")


def save_accounts(data):
    save_json("accounts.json", data)


def next_id(items, id_key, prefix, digits):
    """Sinh ID tiếp theo theo định dạng PREFIX + số."""
    nums = []
    for item in items:
        val = item.get(id_key, "")
        try:
            nums.append(int(str(val).replace(prefix, "", 1)))
        except (ValueError, AttributeError):
            pass
    n = max(nums) + 1 if nums else 1
    return f"{prefix}{n:0{digits}d}"


def generate_product_id(products):
    return next_id(products, "product_id", "P", 4)


def generate_customer_id(customers):
    return next_id(customers, "customer_id", "C", 3)


def generate_order_id(orders):
    return next_id(orders, "order_id", "O", 5)


def generate_staff_id(staffs):
    return next_id(staffs, "staff_id", "S", 2)


def generate_account_id(accounts):
    return next_id(accounts, "account_id", "ACC", 3)
