"""
staff.py - Quản lý nhân viên và ca làm
"""
from modules.data_handler import load_staffs, save_staffs, load_json, save_json, generate_staff_id


def get_all_staffs():
    return load_staffs()


def get_staff_by_id(staff_id):
    staffs = load_staffs()
    return next((s for s in staffs if s.get("staff_id") == staff_id), None)


def search_staffs(keyword="", role=""):
    staffs = load_staffs()
    kw = keyword.lower().strip()
    rol = role.lower().strip()
    result = []
    for s in staffs:
        if kw and kw not in s.get("name", "").lower() and kw not in s.get("phone", ""):
            continue
        if rol and rol not in s.get("role", "").lower():
            continue
        result.append(s)
    return result


def add_staff(data: dict):
    staffs = load_staffs()
    if "staff_id" not in data or not data["staff_id"]:
        data["staff_id"] = generate_staff_id(staffs)
    if "status" not in data:
        data["status"] = "Đang làm"
    staffs.append(data)
    save_staffs(staffs)
    return data["staff_id"]


def update_staff(staff_id, updated_data: dict):
    staffs = load_staffs()
    for i, s in enumerate(staffs):
        if s.get("staff_id") == staff_id:
            staffs[i].update(updated_data)
            save_staffs(staffs)
            return True
    return False


def delete_staff(staff_id):
    staffs = load_staffs()
    new_list = [s for s in staffs if s.get("staff_id") != staff_id]
    if len(new_list) < len(staffs):
        save_staffs(new_list)
        return True
    return False


def assign_shift(staff_id, shift_id):
    return update_staff(staff_id, {"shift_id": shift_id})


def get_shifts():
    return load_json("shifts.json")
