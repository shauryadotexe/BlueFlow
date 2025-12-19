import streamlit as st
import json
import os
import time
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "orders.json"
KITCHEN_CAPACITY_PER_HOUR = 60
AVG_PREP_TIME_MINS = 60 / KITCHEN_CAPACITY_PER_HOUR
WAIT_THRESHOLD_WARNING = 15
WAIT_THRESHOLD_CRITICAL = 30

# --- DATABASE FUNCTIONS (Shared Logic) ---
def load_orders():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def save_order(new_order):
    orders = load_orders()
    orders.append(new_order)
    with open(DB_FILE, "w") as f:
        json.dump(orders, f, indent=4)

# --- ALGORITHM ---
def calculate_queue_metrics():
    orders = load_orders()
    active_orders = [o for o in orders if o['status'] == 'Pending']
    total_items = sum(o['item_count'] for o in active_orders)
    estimated_wait_mins = total_items * AVG_PREP_TIME_MINS
    
    if estimated_wait_mins >= WAIT_THRESHOLD_CRITICAL:
        status_level = "CRITICAL"
    elif estimated_wait_mins >= WAIT_THRESHOLD_WARNING:
        status_level = "WARNING"
    else:
        status_level = "NORMAL"
        
    return total_items, estimated_wait_mins, status_level

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Student", layout="centered")

st.title("📱 BlueFlow Ordering")
st.markdown("Order from your room, skip the queue.")

# 1. RUN ALGORITHM & DISPLAY STATUS
queue_items, wait_time, status = calculate_queue_metrics()

col1, col2 = st.columns(2)
col1.metric("Items in Queue", f"{queue_items}")
col2.metric("Est. Wait Time", f"{int(wait_time)} mins")

if status == "NORMAL":
    st.success("✅ Kitchen Running Smoothly")
    accepting_orders = True
elif status == "WARNING":
    st.warning("⚠️ High Traffic - Expect Delays")
    accepting_orders = True
else:
    st.error("⛔ ORDERING PAUSED: Kitchen Full")
    accepting_orders = False

st.divider()

# 2. ORDER FORM
with st.form("order_form", clear_on_submit=True):
    st.write("#### 🍔 Menu")
    burger_qty = st.number_input("Blue Special Burger", min_value=0, max_value=5)
    fries_qty = st.number_input("Peri Peri Fries", min_value=0, max_value=5)
    
    submit = st.form_submit_button("Confirm Order 💳")
    
    if submit:
        total_items = burger_qty + fries_qty
        
        if not accepting_orders:
            st.error("🚫 Orders paused due to high wait times.")
        elif total_items == 0:
            st.warning("Please add at least one item.")
        else:
            # Create Order Object
            new_order = {
                "id": int(time.time()), # Simple ID using timestamp
                "items": f"Burger x{burger_qty}, Fries x{fries_qty}",
                "item_count": total_items,
                "time": datetime.now().strftime("%H:%M"),
                "status": "Pending"
            }
            save_order(new_order)
            st.success(f"Order Placed! Wait Time: {int(wait_time)} mins.")
            time.sleep(1)
            st.rerun()

# Auto-refresh button for students checking status
if st.button("🔄 Refresh Status"):
    st.rerun()