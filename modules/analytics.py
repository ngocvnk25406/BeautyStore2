"""
analytics.py - Thống kê doanh thu, sản phẩm, khách hàng
"""
from collections import Counter
from modules.data_handler import load_orders, load_products, load_customers


def get_summary():
    """Trả về dict tổng quan: tổng SP, KH, đơn hàng, doanh thu."""
    products = load_products()
    customers = load_customers()
    orders = load_orders()
    active_orders = [o for o in orders if o.get("status") != "Đã hủy"]
    total_revenue = sum(o.get("total", 0) for o in active_orders)
    return {
        "total_products": len(products),
        "total_customers": len(customers),
        "total_orders": len(active_orders),
        "total_revenue": total_revenue,
    }


def get_top_products(top_n=10):
    """Sản phẩm bán chạy nhất."""
    orders = load_orders()
    products = load_products()
    product_map = {p["product_id"]: p for p in products}

    counter = Counter()
    revenue = Counter()
    for o in orders:
        if o.get("status") == "Đã hủy":
            continue
        for item in o.get("items", []):
            pid = item.get("product_id", "")
            qty = item.get("quantity", 0)
            price = item.get("price", 0)
            counter[pid] += qty
            revenue[pid] += price * qty

    result = []
    for pid, qty in counter.most_common(top_n):
        p = product_map.get(pid, {})
        result.append({
            "product_id": pid,
            "name": p.get("name", pid),
            "brand": p.get("brand", ""),
            "sold": qty,
            "revenue": revenue[pid],
        })
    return result


def get_revenue_by_month():
    """Doanh thu theo tháng (dict {YYYY-MM: amount})."""
    orders = load_orders()
    monthly = {}
    for o in orders:
        if o.get("status") == "Đã hủy":
            continue
        dt_str = o.get("datetime", "")
        try:
            # format: DD/MM/YYYY HH:MM
            parts = dt_str.split(" ")[0].split("/")
            month_key = f"{parts[2]}-{parts[1]}"
        except (IndexError, ValueError):
            month_key = "unknown"
        monthly[month_key] = monthly.get(month_key, 0) + o.get("total", 0)
    return dict(sorted(monthly.items()))


def get_low_stock_products(min_qty=10):
    """Sản phẩm tồn kho thấp."""
    products = load_products()
    return [p for p in products if p.get("stock_quantity", 0) <= min_qty]


def get_customer_stats():
    """Thống kê khách hàng theo hạng."""
    customers = load_customers()
    stats = {"Vàng": 0, "Bạc": 0, "Đồng": 0}
    for c in customers:
        rank = c.get("rank", "Đồng")
        stats[rank] = stats.get(rank, 0) + 1
    return stats
