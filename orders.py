import uuid
from datetime import datetime

orders_db = []

def create_order(username, student_name, year, branch, section, roll_number,
                 order_description, total_pages, copies, print_type, binding,
                 payment_method, file_paths):
    order = {
        "id": str(uuid.uuid4()),
        "username": username,
        "created_at": datetime.utcnow().isoformat(),
        "status": "received",
        "student_name": student_name,
        "year": year,
        "branch": branch,
        "section": section,
        "roll_number": roll_number,
        "order_description": order_description,
        "total_pages": total_pages,
        "copies": copies,
        "print_type": print_type,
        "binding": binding,
        "payment_method": payment_method,
        "file_paths": file_paths
    }
    orders_db.append(order)
    return order

def get_orders_by_user(username):
    return [o for o in orders_db if o["username"] == username]