"""
chatbot.py - Chatbot tư vấn mỹ phẩm AI
Xử lý hội thoại, nhận diện intent, gợi ý sản phẩm theo da
"""
import re
from modules.data_handler import load_products
from modules.recommendation import recommendation

# ── Kiến thức về loại da ──────────────────────────────────────────────────────
SKIN_TYPES_INFO = {
    "da nhạy cảm/ kích ứng": {
        "description": [
            "Da dễ đỏ rát, châm chích khi dùng mỹ phẩm",
            "Phản ứng nhanh với môi trường và hoạt chất mạnh"],
        "tips": [
            "Test sản phẩm trước khi dùng toàn mặt",
            "Ưu tiên phục hồi da hơn treatment",
            "Giữ routine tối giản"],
        "avoid": ["Cồn", "Hương liệu", "Tinh dầu đậm đặc"],
        "ingredients": ["Centella Asiatica", "Panthenol", "Ceramide", "Madecassoside"]},

    "da dầu": {
        "description": ["Da tiết nhiều dầu, bóng nhờn", "Lỗ chân lông to, dễ nổi mụn"],
        "tips": ["Rửa mặt 2 lần/ngày với sản phẩm dịu nhẹ", "Dùng toner không cồn",
                 "Ưu tiên kem dưỡng dạng gel"],
        "avoid": ["Kem dưỡng quá đặc", "Dầu dừa", "Cồn mạnh"],
        "ingredients": ["Niacinamide", "Salicylic Acid (BHA)", "Zinc", "Tea Tree"]},

    "da mụn": {
        "description": ["Da dễ xuất hiện mụn viêm, mụn ẩn",
            "Da nhạy cảm với bít tắc lỗ chân lông"],
        "tips": [
            "Giữ da sạch nhưng không rửa quá nhiều",
            "Kết hợp trị mụn và phục hồi",
            "Không nặn mụn"],
        "avoid": ["Sản phẩm gây bít tắc", "Cồn cao", "Dầu khoáng nặng"],
        "ingredients": ["Salicylic Acid", "Niacinamide", "Azelaic Acid", "Tea Tree"]},

    "da khô": {
        "description": ["Da thiếu ẩm, dễ bong tróc", "Cảm giác căng rít sau khi rửa mặt"],
        "tips": ["Dưỡng ẩm đều đặn sáng và tối", "Dùng sữa rửa mặt dịu nhẹ",
                 "Khóa ẩm bằng kem dưỡng"],
        "avoid": ["Cồn", "Sản phẩm làm sạch mạnh"],
        "ingredients": ["Hyaluronic Acid", "Ceramide", "Shea Butter", "Squalane"]},

    "da yếu": {
        "description": ["Hàng rào bảo vệ da suy yếu", "Da dễ kích ứng và khó phục hồi"],
        "tips": ["Ưu tiên phục hồi da", "Giảm treatment mạnh", "Chống nắng đầy đủ"],
        "avoid": ["Retinol nồng độ cao", "Tẩy da chết thường xuyên"],
        "ingredients": ["Ceramide", "Panthenol", "B5", "Centella Asiatica"]},

    "da xỉn màu": {
        "description": ["Da thiếu sức sống, không đều màu", "Da trông mệt mỏi"],
        "tips": ["Tẩy tế bào chết hóa học nhẹ", "Bổ sung chất chống oxy hóa", "Chống nắng kỹ"],
        "avoid": ["Bỏ chống nắng", "Skincare thiếu dưỡng ẩm"],
        "ingredients": ["Vitamin C", "Niacinamide", "AHA", "Glutathione"]},

    "da thâm": {
        "description": ["Da có vết thâm sau mụn", "Màu da không đều"],
        "tips": ["Kiên trì làm sáng da", "Không cạy mụn", "Dùng kem chống nắng hằng ngày"],
        "avoid": ["Nặn mụn", "Không chống nắng"],
        "ingredients": ["Tranexamic Acid", "Alpha Arbutin", "Niacinamide", "Vitamin C"]},

    "da lão hóa": {
        "description": ["Da xuất hiện nếp nhăn", "Độ đàn hồi suy giảm"],
        "tips": ["Bổ sung hoạt chất chống lão hóa", "Dưỡng ẩm và chống nắng đều đặn",
                 "Dùng retinol phù hợp"],
        "avoid": ["Bỏ chống nắng", "Routine quá đơn giản"],
        "ingredients": ["Retinol", "Peptide", "Collagen", "Vitamin E"]},

    "da nám": {
        "description": ["Da có đốm nâu hoặc mảng nám", "Dễ sậm màu khi tiếp xúc ánh nắng"],
        "tips": ["Chống nắng nghiêm ngặt", "Dùng sản phẩm đặc trị nám", "Kiên trì lâu dài"],
        "avoid": ["Nắng gắt", "Treatment không kiểm soát"],
        "ingredients": ["Tranexamic Acid", "Arbutin", "Niacinamide", "Vitamin C"]},

    "da hỗn hợp": {
        "description": ["Vùng chữ T dầu, hai má khô hoặc thường",
                        "Mỗi vùng da có nhu cầu khác nhau"],
        "tips": ["Chăm sóc da theo từng vùng", "Dùng sản phẩm cân bằng dầu – ẩm",
                 "Không layer quá dày"],
        "avoid": ["Kem dưỡng quá nặng mặt"],
        "ingredients": ["Niacinamide", "Hyaluronic Acid", "Green Tea"]},

    "viêm da cơ địa": {
        "description": ["Da dễ viêm, ngứa, bong tróc theo đợt", "Cần chăm sóc cẩn thận"],
        "tips": ["Dùng sản phẩm chuyên biệt", "Giữ ẩm liên tục", "Tránh yếu tố kích ứng"],
        "avoid": ["Hương liệu", "Cồn", "Tinh dầu"],
        "ingredients": ["Ceramide", "Colloidal Oatmeal", "Panthenol", "Shea Butter"]},
}

# ── Vấn đề về da ─────────────────────────────────────────────────────────────
SKIN_CONCERNS_INFO = {
    "thâm mụn": {
        "cause": ["Viêm da sau mụn", "Melanin tăng sinh"],
        "tips": ["Kiên trì dùng sản phẩm mờ thâm", "Bắt buộc chống nắng", "Không nặn mụn"],
        "ingredients": ["Tranexamic Acid", "Alpha Arbutin", "Niacinamide", "Vitamin C"]},
    "làm sạch": {
        "cause": ["Bụi bẩn, dầu thừa tích tụ", "Trang điểm không được làm sạch kỹ"],
        "tips": ["Làm sạch da 2 bước vào buổi tối", "Chọn sản phẩm làm sạch dịu nhẹ"],
        "ingredients": ["Micellar", "Glycerin", "Coco-Glucoside"]},
    "dưỡng ẩm": {
        "cause": ["Da thiếu nước", "Hàng rào bảo vệ da suy yếu"],
        "tips": ["Dưỡng ẩm đều đặn sáng và tối", "Cấp ẩm ngay sau khi rửa mặt"],
        "ingredients": ["Hyaluronic Acid", "Glycerin", "Ceramide"]},
    "kiểm soát dầu": {
        "cause": ["Tuyến bã nhờn hoạt động mạnh", "Da thiếu nước gây tiết dầu bù"],
        "tips": ["Cấp ẩm đầy đủ cho da", "Dùng sản phẩm oil-free"],
        "ingredients": ["Niacinamide", "Zinc", "Green Tea"]},
    "giảm mụn": {
        "cause": ["Tắc nghẽn lỗ chân lông", "Vi khuẩn gây mụn"],
        "tips": ["Giữ da sạch nhưng nhẹ nhàng", "Không nặn mụn"],
        "ingredients": ["Salicylic Acid", "Niacinamide", "Tea Tree"]},
    "làm dịu da": {
        "cause": ["Kích ứng mỹ phẩm", "Tác động môi trường"],
        "tips": ["Ngưng sản phẩm gây kích ứng", "Ưu tiên routine tối giản"],
        "ingredients": ["Centella Asiatica", "Panthenol", "Madecassoside"]},
    "phục hồi da": {
        "cause": ["Da yếu sau treatment", "Hàng rào bảo vệ da bị tổn thương"],
        "tips": ["Giảm hoạt chất mạnh", "Dưỡng ẩm và phục hồi liên tục"],
        "ingredients": ["Ceramide", "Panthenol", "B5"]},
    "làm sáng da": {
        "cause": ["Tế bào chết tích tụ", "Da thiếu sức sống"],
        "tips": ["Tẩy tế bào chết định kỳ", "Bổ sung chất chống oxy hóa"],
        "ingredients": ["Vitamin C", "Niacinamide", "AHA"]},
    "giảm thâm": {
        "cause": ["Viêm da sau mụn", "Không chống nắng"],
        "tips": ["Kiên trì dùng sản phẩm làm sáng", "Bắt buộc chống nắng"],
        "ingredients": ["Tranexamic Acid", "Alpha Arbutin", "Niacinamide"]},
    "chống lão hóa": {
        "cause": ["Tuổi tác", "Tác động tia UV"],
        "tips": ["Bổ sung hoạt chất chống lão hóa", "Duy trì routine lâu dài"],
        "ingredients": ["Retinol", "Peptide", "Vitamin E"]},
    "chống nắng": {
        "cause": ["Tia UV gây tổn thương da", "Nguyên nhân chính gây lão hóa sớm"],
        "tips": ["Dùng kem chống nắng mỗi ngày", "Thoa đủ lượng, thoa lại sau 2–3 tiếng"],
        "ingredients": ["Zinc Oxide", "Titanium Dioxide", "Uvinul", "Tinosorb"]},
}

# ── Loại sản phẩm ─────────────────────────────────────────────────────────────
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

# ── Intent patterns ───────────────────────────────────────────────────────────
INTENT_PATTERNS = {
    "greeting": [r"xin chào", r"hello", r"hi", r"chào", r"hey", r"ê", r"alo"],
    "skin_type": [r"da dầu", r"da khô", r"da hỗn hợp", r"da nhạy cảm|da kích ứng",
                  r"da mụn", r"da yếu", r"da xỉn màu", r"da thâm", r"da lão hóa",
                  r"da nám", r"da sần", r"viêm da cơ địa"],
    "skin_concern": [r"\b(mụn|mụn viêm|mụn ẩn|acne)\b", r"\b(thâm mụn|thâm|vết thâm)\b",
                     r"\b(nám|tàn nhang|đốm nâu)\b", r"\b(khô|khô da|bong tróc)\b",
                     r"\b(dầu|nhờn|bóng dầu)\b", r"\b(lão hóa|nếp nhăn)\b",
                     r"\b(nhạy cảm|kích ứng|đỏ da)\b", r"\b(xỉn màu|tối da)\b"],
    "confirm_yes": [r"\b(có|ok|oke|yes|ừ|uh|đồng ý)\b"],
    "confirm_no": [r"\b(không|ko|không cần|thôi|no)\b"],
    "routine": [r"routine", r"quy trình", r"các bước", r"skincare như thế nào"],
    "ingredient": [r"thành phần", r"ingredient", r"niacinamide", r"retinol",
                   r"vitamin c", r"bha", r"aha", r"có gì trong đó"],
    "product_query": [r"mua", r"tìm", r"tư vấn", r"gợi ý", r"recommend",
                      r"serum", r"mặt nạ", r"sữa rửa mặt", r"toner", r"kem dưỡng",
                      r"chống nắng", r"tẩy da chết", r"tẩy trang", r"son dưỡng"],
    "thanks": [r"cảm ơn", r"thanks", r"thank you", r"tks"],
    "bye": [r"tạm biệt", r"bye", r"goodbye", r"kết thúc", r"bái bai"],
}


def detect_intents(message):
    message = message.lower()
    intents = []
    for intent, patterns in INTENT_PATTERNS.items():
        for p in patterns:
            if re.search(p, message):
                intents.append(intent)
                break
    return intents or ["general"]


def extract_skin_type(message):
    message = message.lower()
    mapping = {
        "da dầu": "da dầu",
        "da khô": "da khô",
        "da hỗn hợp": "da hỗn hợp",
        "da nhạy cảm": "da nhạy cảm/ kích ứng",
        "da kích ứng": "da nhạy cảm/ kích ứng",
        "da mụn": "da mụn",
        "da yếu": "da yếu",
        "da xỉn màu": "da xỉn màu",
        "da thâm": "da thâm",
        "da lão hóa": "da lão hóa",
        "da nám": "da nám",
        "da sần": "da sần",
        "da hỗn hợp thiên dầu": "da hỗn hợp",
        "da hỗn hợp thiên khô": "da hỗn hợp",
        "viêm da cơ địa": "viêm da cơ địa",
    }
    for k, v in mapping.items():
        if k in message:
            return v
    return None


def extract_concerns(message):
    message = message.lower()
    found = []
    concern_map = {
        "làm sạch": ["dầu", "nhờn", "bóng dầu", "bụi bẩn", "mụn ẩn", "tắc lỗ chân lông"],
        "giảm thâm": ["thâm", "bị thâm", "vết thâm", "thâm mụn"],
        "dưỡng ẩm": ["da khô", "khô", "bong tróc", "căng da", "thiếu nước"],
        "kiểm soát dầu": ["da dầu", "tiết dầu", "bóng dầu", "nhờn"],
        "giảm mụn": ["mụn", "mụn viêm", "mụn ẩn", "acne", "nổi mụn"],
        "làm dịu da": ["nhạy cảm", "kích ứng", "đỏ da", "ngứa", "rát"],
        "phục hồi da": ["da yếu", "da tổn thương", "sau treatment"],
        "làm sáng da": ["xỉn màu", "tối da", "không đều màu"],
        "chống lão hóa": ["lão hóa", "nếp nhăn", "chống già"],
        "chống nắng": ["sợ nắng", "dị ứng nắng"],
    }
    for concern, keywords in concern_map.items():
        for kw in keywords:
            if kw in message:
                found.append(concern)
                break
    return found


def extract_effects(concerns):
    effects = set()
    concern_to_effect = {
        "giảm mụn": ["giảm mụn", "kháng viêm", "kháng khuẩn", "làm dịu"],
        "thâm mụn": ["mờ thâm", "làm sáng", "đều màu da"],
        "kiểm soát dầu": ["kiểm soát dầu", "giảm bã nhờn"],
        "làm sạch": ["làm sạch", "thông thoáng lỗ chân lông"],
        "dưỡng ẩm": ["cấp ẩm", "giữ ẩm", "phục hồi"],
        "phục hồi da": ["phục hồi", "làm dịu", "tăng hàng rào bảo vệ da"],
        "làm dịu da": ["làm dịu", "giảm kích ứng"],
        "giảm thâm": ["mờ thâm", "làm sáng"],
        "làm sáng da": ["làm sáng", "đều màu da"],
        "chống lão hóa": ["chống lão hóa", "tăng đàn hồi", "giảm nếp nhăn"],
        "chống nắng": ["chống nắng", "bảo vệ da"],
    }
    for c in concerns:
        effects.update(concern_to_effect.get(c, []))
    return list(effects)


def detect_product_type_from_message(message):
    message = message.lower()
    for ptype, keywords in PRODUCT_TYPES.items():
        for kw in keywords:
            if kw in message:
                return ptype
    return None


def explain_ingredient(message):
    message = message.lower()
    if "niacinamide" in message:
        return ("💊 **NIACINAMIDE (Vitamin B3)**\n\n"
                "• Kiểm soát dầu, se lỗ chân lông\n"
                "• Làm sáng da, mờ thâm\n"
                "• Tăng cường hàng rào bảo vệ da\n\n"
                "Phù hợp: Mọi loại da | Nồng độ: 2–10%")
    elif "hyaluronic acid" in message or " ha " in message:
        return ("💧 **HYALURONIC ACID (HA)**\n\n"
                "• Cấp nước sâu, giữ ẩm, làm da căng mịn\n\n"
                "Phù hợp: Mọi loại da | Nồng độ: 0.1–2%")
    elif "bha" in message or "salicylic" in message:
        return ("🌿 **BHA (Salicylic Acid)**\n\n"
                "• Làm sạch sâu lỗ chân lông\n"
                "• Giảm mụn, giảm viêm, kiểm soát dầu\n\n"
                "Phù hợp: Da dầu, da mụn | Nồng độ: 0.5–2%")
    elif "retinol" in message:
        return ("✨ **RETINOL (Vitamin A)**\n\n"
                "• Chống lão hóa, kích thích tái tạo da\n"
                "• Giảm nếp nhăn, làm đều màu da\n\n"
                "Phù hợp: Da lão hóa | Bắt đầu với nồng độ thấp 0.025%")
    elif "vitamin c" in message:
        return ("🍋 **VITAMIN C**\n\n"
                "• Làm sáng da, mờ thâm nám\n"
                "• Chống oxy hóa mạnh\n\n"
                "Phù hợp: Mọi loại da | Nồng độ: 5–20%")
    elif "ceramide" in message:
        return ("🛡️ **CERAMIDE**\n\n"
                "• Phục hồi hàng rào bảo vệ da\n"
                "• Giữ ẩm, chống kích ứng\n\n"
                "Phù hợp: Da khô, da yếu, da nhạy cảm")
    else:
        return ("🤔 Mình chưa có dữ liệu về thành phần này.\n"
                "Bạn có thể hỏi về: niacinamide, HA, BHA, retinol, vitamin C, ceramide…")


def new_context():
    """Tạo context mới cho phiên chat."""
    return {
        "product_type": None,
        "skin_type": None,
        "concerns": [],
        "effects": [],
        "step": "ask_skin_type",
    }


def generate_response(message, context):
    """Sinh phản hồi chatbot từ tin nhắn và context hiện tại."""
    msg = message.lower()

    # Cập nhật context từ tin nhắn
    skin_type = extract_skin_type(msg)
    if skin_type and skin_type != context.get("skin_type"):
        context["skin_type"] = skin_type
        context["concerns"] = []
        context["effects"] = []

    product_type = detect_product_type_from_message(msg)
    if product_type:
        context["product_type"] = product_type

    concerns = extract_concerns(msg)
    if concerns:
        context["concerns"] = concerns
        context["effects"] = extract_effects(concerns)

    intents = detect_intents(msg)

    # Greeting
    if "greeting" in intents:
        context["step"] = "ask_skin_type"
        return ("Xin chào! 👋 Tôi là trợ lý tư vấn mỹ phẩm AI.\n\n"
                "Tôi có thể giúp bạn 😊:\n"
                "• Tư vấn sản phẩm theo loại da\n"
                "• Giải thích thành phần skincare\n"
                "• Gợi ý routine chăm sóc da\n\n"
                "Bạn có thể cho tôi biết **loại da** của bạn không?\n"
                "(VD: da dầu, da khô, da nhạy cảm, da hỗn hợp...)")

    # Thanks
    if "thanks" in intents:
        return "Không có gì ạ! 😊 Nếu còn thắc mắc gì, đừng ngại hỏi nhé!"

    # Bye
    if "bye" in intents:
        return "Tạm biệt bạn! 👋 Chúc bạn có làn da đẹp! Hẹn gặp lại!"

    # Ingredient
    if "ingredient" in intents:
        return explain_ingredient(msg)

    # Routine
    if "routine" in intents:
        resp = "🌟 **SKINCARE ROUTINE CƠ BẢN**\n\n"
        resp += "**Buổi sáng:**\n1. Sữa rửa mặt\n2. Toner\n3. Serum (Vitamin C)\n"
        resp += "4. Kem dưỡng ẩm\n5. Kem chống nắng SPF50+\n\n"
        resp += "**Buổi tối:**\n1. Tẩy trang\n2. Sữa rửa mặt\n3. Toner\n"
        resp += "4. Serum (Retinol/Niacinamide)\n5. Kem dưỡng ẩm\n\n"
        resp += "💡 Cho tôi biết loại da để gợi ý sản phẩm cụ thể hơn!"
        return resp

    # Xử lý theo step
    step = context.get("step", "ask_skin_type")

    if step == "ask_skin_type":
        if not skin_type:
            return ("💡 Bạn thuộc loại da nào?\n\n"
                    "• Da dầu / Da khô / Da hỗn hợp\n"
                    "• Da nhạy cảm / Da mụn / Da thường\n"
                    "• Da lão hóa / Da nám / Da thâm")
        context["step"] = "confirm_have_concern"
        info = SKIN_TYPES_INFO.get(skin_type, {})
        resp = f"📋 **Thông tin về {skin_type.upper()}**\n\n"
        if info.get("description"):
            resp += "💡 **Đặc điểm:**\n"
            for d in info["description"]:
                resp += f" • {d}\n"
        if info.get("tips"):
            resp += "\n💡 **Tips chăm sóc:**\n"
            for tip in info["tips"]:
                resp += f" • {tip}\n"
        if info.get("ingredients"):
            resp += f"\n✅ **Nên dùng:** {', '.join(info['ingredients'])}"
        if info.get("avoid"):
            resp += f"\n❌ **Nên tránh:** {', '.join(info['avoid'])}"
        resp += "\n\n💬 Bạn có đang gặp vấn đề gì về da không? (có / không)"
        return resp

    if step == "confirm_have_concern":
        if "confirm_yes" in intents or concerns:
            if concerns:
                context["step"] = "done"
                return _give_concern_advice(context)
            context["step"] = "ask_concern"
            return ("Bạn đang gặp vấn đề gì về da?\n"
                    "Ví dụ: mụn, thâm, khô, dầu, lão hóa, nhạy cảm...")
        if "confirm_no" in intents:
            context["step"] = "done"
            return "Bạn có muốn mình gợi ý sản phẩm phù hợp với loại da không?"
        return "Bạn trả lời giúp mình: **có** hoặc **không** nhé 😊"

    if step == "ask_concern":
        if not concerns:
            return ("Bạn đang gặp vấn đề gì?\n"
                    "Ví dụ: mụn, thâm mụn, da khô, da dầu, lão hóa...")
        context["step"] = "done"
        return _give_concern_advice(context)

    # Gợi ý sản phẩm
    if "product_query" in intents or "confirm_yes" in intents:
        products = recommendation(
            skin_type=context.get("skin_type"),
            effects=context.get("effects"),
            product_type=context.get("product_type"),
        )
        if products:
            resp = "🛍️ **Sản phẩm gợi ý cho bạn:**\n"
            for i, p in enumerate(products[:5], 1):
                resp += (f"\n{i}. **{p['name']}** ({p.get('brand','')})\n"
                         f"   💰 {p['price']:,}đ | 📦 Còn {p['stock_quantity']} sản phẩm\n"
                         f"   ✨ {', '.join(p.get('effects', []))}\n")
            return resp
        return "😢 Hiện chưa có sản phẩm phù hợp. Bạn muốn thay đổi tiêu chí không?"

    if "confirm_no" in intents:
        return "Ok nè 😊 Nếu muốn hỏi về thành phần, routine hay vấn đề da khác thì cứ nói nhé!"

    # Default
    return ("Tôi hiểu bạn đang quan tâm về skincare. 🤔\n\n"
            "Để tư vấn chính xác hơn, cho tôi biết:\n"
            "• Loại da của bạn? (da dầu/khô/hỗn hợp/nhạy cảm)\n"
            "• Vấn đề da đang gặp? (mụn/thâm/khô/lão hóa...)\n\n"
            "Ví dụ: 'Tôi có da dầu và hay bị mụn'")


def _give_concern_advice(context):
    concerns = context.get("concerns", [])
    resp = "📋 **Giải pháp cho vấn đề da của bạn:**\n\n"
    for concern in concerns[:2]:
        info = SKIN_CONCERNS_INFO.get(concern, {})
        resp += f"🔸 **{concern.upper()}**\n"
        if info.get("tips"):
            resp += "Tips:\n"
            for tip in info["tips"][:2]:
                resp += f"• {tip}\n"
        if info.get("ingredients"):
            resp += f"Nên dùng: {', '.join(info['ingredients'][:3])}\n\n"
    resp += "💬 Bạn có muốn mình gợi ý sản phẩm phù hợp không?"
    return resp
