"""
inventory.py - Quản lý kho hàng sản phẩm (CRUD)
"""
from modules.data_handler import load_products, save_products, generate_product_id
from datetime import date


def get_all_products():
    return load_products()


def get_product_by_id(product_id):
    products = load_products()
    return next((p for p in products if p.get("product_id") == product_id), None)


def search_products(keyword="", category="", brand=""):
    """Tìm kiếm sản phẩm theo từ khóa, danh mục, thương hiệu."""
    products = load_products()
    kw = keyword.lower().strip()
    cat = category.lower().strip()
    br = brand.lower().strip()

    result = []
    for p in products:
        if kw and kw not in p.get("name", "").lower() and kw not in p.get("product_id", "").lower():
            continue
        if cat and cat not in p.get("category", "").lower():
            continue
        if br and br not in p.get("brand", "").lower():
            continue
        result.append(p)
    return result


def add_product(product_data: dict):
    """Thêm sản phẩm mới. Tự sinh ID nếu chưa có."""
    products = load_products()
    if "product_id" not in product_data or not product_data["product_id"]:
        product_data["product_id"] = generate_product_id(products)
    products.append(product_data)
    save_products(products)
    return product_data["product_id"]


def update_product(product_id, updated_data: dict):
    """Cập nhật thông tin sản phẩm theo ID."""
    products = load_products()
    for i, p in enumerate(products):
        if p.get("product_id") == product_id:
            products[i].update(updated_data)
            save_products(products)
            return True
    return False


def delete_product(product_id):
    """Xóa sản phẩm theo ID."""
    products = load_products()
    new_list = [p for p in products if p.get("product_id") != product_id]
    if len(new_list) < len(products):
        save_products(new_list)
        return True
    return False


def deduct_stock(product_id, quantity):
    """Trừ số lượng tồn kho khi bán hàng."""
    products = load_products()
    for p in products:
        if p.get("product_id") == product_id:
            current = p.get("stock_quantity", 0)
            if current < quantity:
                return False, "Không đủ hàng trong kho"
            p["stock_quantity"] = current - quantity
            save_products(products)
            return True, "OK"
    return False, "Không tìm thấy sản phẩm"


def restore_stock(product_id, quantity):
    """Hoàn trả số lượng tồn kho (hủy đơn)."""
    products = load_products()
    for p in products:
        if p.get("product_id") == product_id:
            p["stock_quantity"] = p.get("stock_quantity", 0) + quantity
            save_products(products)
            return True
    return False


def check_low_stock(min_qty=10):
    """Lấy danh sách sản phẩm sắp hết hàng."""
    products = load_products()
    return [p for p in products if p.get("stock_quantity", 0) <= min_qty]


def check_expired():
    """Lấy danh sách sản phẩm hết hạn hoặc sắp hết hạn trong 30 ngày."""
    products = load_products()
    today = date.today()
    result = []
    for p in products:
        exp = p.get("exp_date", "")
        if exp:
            try:
                exp_date = date.fromisoformat(exp)
                days_left = (exp_date - today).days
                if days_left <= 30:
                    result.append({**p, "days_left": days_left})
            except ValueError:
                pass
    return result


def get_product_status(product):
    """Xác định trạng thái sản phẩm (còn hàng / sắp hết / hết hàng)."""
    qty = product.get("stock_quantity", 0)
    min_qty = product.get("min_quantity", 5)
    if qty == 0:
        return "Hết hàng"
    elif qty <= min_qty:
        return "Sắp hết"
    return "Còn hàng"
