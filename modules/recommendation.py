"""
recommendation.py - Engine gợi ý sản phẩm theo loại da và vấn đề da
"""
from modules.data_handler import load_products, load_customers

PRODUCT_TYPES = {
    "serum": ["serum", "retinol"],
    "mask": ["mặt nạ", "mask", "sleeping mask"],
    "cleanser": ["sữa rửa mặt", "gel rửa mặt", "cleanser"],
    "toner": ["toner", "nước hoa hồng", "nước cân bằng", "xịt khoáng"],
    "moisturizer": ["kem dưỡng", "gel dưỡng", "cream", "dưỡng ẩm", "thạch"],
    "sunscreen": ["chống nắng", "sunscreen", "spf"],
    "exfoliant": ["tẩy da chết", "aha", "bha"],
    "cleansing": ["tẩy trang", "micellar"],
    "lipcare": ["son dưỡng", "dưỡng môi"],
}


def recommendation(skin_type=None, effects=None, product_type=None, limit=5):
    """Gợi ý sản phẩm theo loại da, hiệu ứng và loại sản phẩm."""
    products = load_products()
    if not products:
        return []

    scored = []
    for p in products:
        if p.get("stock_quantity", 0) == 0:
            continue

        # Lọc theo loại sản phẩm
        if product_type:
            name = p.get("name", "").lower()
            cat = p.get("category", "").lower()
            matched = any(
                kw in name or kw in cat
                for kw in PRODUCT_TYPES.get(product_type, [])
            )
            if not matched:
                continue

        score = 0
        # Chấm điểm theo loại da
        if skin_type:
            for st in p.get("skin-type", []):
                if skin_type in st.lower() or st.lower() in skin_type or "mọi loại da" in st.lower():
                    score += 2
                    break

        # Chấm điểm theo hiệu ứng
        if effects:
            for ef in effects:
                for pe in p.get("effects", []):
                    if ef.lower() in pe.lower() or pe.lower() in ef.lower():
                        score += 1
                        break

        if score > 0 or (not skin_type and not effects and product_type):
            scored.append({"product": p, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return [item["product"] for item in scored[:limit]]


def recommend_by_skin_type(skin_type, limit=5):
    """Gợi ý sản phẩm theo loại da."""
    products = load_products()
    skin_type = skin_type.lower().strip()
    available = [p for p in products if p.get("stock_quantity", 0) > 0]
    matches = [
        p for p in available
        if any(skin_type in s.lower() or "mọi loại da" in s.lower()
               for s in p.get("skin-type", []))
    ]
    return (matches if matches else available)[:limit]


def recommend_by_concern(concerns, limit=5):
    """Gợi ý sản phẩm theo vấn đề da."""
    products = load_products()
    if isinstance(concerns, str):
        concerns = [concerns]
    concerns = [c.lower().strip() for c in concerns]

    scored = []
    for p in products:
        if p.get("stock_quantity", 0) <= 0:
            continue
        effects = [e.lower() for e in p.get("effects", [])]
        score = sum(1 for c in concerns if any(c in ef for ef in effects))
        if score > 0:
            scored.append((p, score))

    if not scored:
        return [p for p in products if p.get("stock_quantity", 0) > 0][:limit]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored[:limit]]


def recommend_skincare_routine(skin_type, concerns):
    """Tạo skincare routine 6 bước gợi ý sản phẩm cụ thể."""
    products = load_products()
    skin_type = skin_type.lower().strip()
    if isinstance(concerns, str):
        concerns = [concerns]
    concerns = [c.lower().strip() for c in concerns]

    routine_keywords = {
        "Tẩy trang": ["tẩy trang", "micellar"],
        "Sữa rửa mặt": ["sữa rửa mặt", "gel rửa mặt", "cleanser"],
        "Toner": ["toner", "nước hoa hồng", "nước cân bằng", "xịt khoáng"],
        "Serum": ["serum"],
        "Kem dưỡng": ["kem dưỡng", "thạch", "gel dưỡng"],
        "Kem chống nắng": ["chống nắng", "sunscreen", "spf"],
    }

    routine = []
    for step_name, keywords in routine_keywords.items():
        candidates = [
            p for p in products
            if any(k in p.get("name", "").lower() for k in keywords)
            and p.get("stock_quantity", 0) > 0
        ]
        if not candidates:
            continue

        best, best_score = None, -1
        for p in candidates:
            score = 0
            if any(skin_type in s.lower() for s in p.get("skin-type", [])):
                score += 2
            effects = [e.lower() for e in p.get("effects", [])]
            score += sum(1 for c in concerns if any(c in ef for ef in effects))
            if score > best_score:
                best_score, best = score, p

        if best:
            routine.append({"step": step_name, "product": best})

    return routine


def recommend_for_customer(customer_id):
    """Gợi ý sản phẩm cá nhân hóa cho khách hàng."""
    customers = load_customers()
    customer = next((c for c in customers if c.get("customer_id") == customer_id), None)
    if not customer:
        return []

    products = load_products()
    skin_type = customer.get("skin-type", "").lower().strip()
    concerns = [c.lower() for c in customer.get("skin_concern", [])]

    scored = []
    for p in products:
        if p.get("stock_quantity", 0) <= 0:
            continue
        score = 0
        if any(skin_type in s.lower() for s in p.get("skin-type", [])):
            score += 2
        effects = [e.lower() for e in p.get("effects", [])]
        score += sum(1 for c in concerns if any(c in ef for ef in effects))
        if score > 0:
            scored.append((p, score))

    if not scored:
        return [p for p in products if p.get("stock_quantity", 0) > 0][:10]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored[:10]]
