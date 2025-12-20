import streamlit as st
import json
import os
import time
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "orders.json"
KITCHEN_CAPACITY_PER_HOUR = 12  
AVG_PREP_TIME_MINS = 60 / KITCHEN_CAPACITY_PER_HOUR 
TOTAL_SEATS = 10 
WAIT_THRESHOLD_WARNING = 30     
WAIT_THRESHOLD_CRITICAL = 60    
REFRESH_INTERVAL = 5 

# --- DATABASE FUNCTIONS ---
def load_orders():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def save_order(new_order):
    orders = load_orders()
    orders.append(new_order)
    with open(DB_FILE, "w") as f: json.dump(orders, f, indent=4)

# --- ALGORITHM ---
def calculate_metrics():
    orders = load_orders()
    
    # 1. Kitchen Load (Only count PENDING orders for wait time)
    active_orders = [o for o in orders if o['status'] == 'Pending']
    total_items = sum(o['item_count'] for o in active_orders)
    estimated_wait_mins = total_items * AVG_PREP_TIME_MINS
    
    if estimated_wait_mins >= WAIT_THRESHOLD_CRITICAL:
        kitchen_status = "CRITICAL"
    elif estimated_wait_mins >= WAIT_THRESHOLD_WARNING:
        kitchen_status = "WARNING"
    else:
        kitchen_status = "NORMAL"
        
    # 2. Seating Logic (Count Pending + Ready Dine-In orders)
    dine_in_orders = [o for o in orders if o.get('type') == 'Dine-In' and o['status'] in ['Pending', 'Ready']]
    occupied_seats = len(dine_in_orders)
    
    # 3. Check for READY orders
    ready_orders_list = [o for o in orders if o['status'] == 'Ready']
    
    return total_items, estimated_wait_mins, kitchen_status, occupied_seats, ready_orders_list

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Student", layout="centered")

st.title("📱 BlueFlow Ordering")
st.markdown("Order from your room, skip the queue.")
st.caption(f"⚡ Live Status: Updating every {REFRESH_INTERVAL} seconds...")

# METRICS
queue_items, wait_time, status, occupied_seats, ready_list = calculate_metrics()

# --- NEW FEATURE: READY NOTIFICATION ---
# if ready_list:
st.info("### 🎉 ORDERS READY FOR PICKUP!")
    # Create a clean list of ready numbers
ready_numbers = [f"#{str(o['id'])[-4:]}" for o in ready_list]
st.markdown(f"**NOW SERVING:** {'  |  '.join(ready_numbers)}")
st.divider()

col1, col2 = st.columns(2)
col1.metric("Est. Wait Time", f"{int(wait_time)} mins")
col2.metric("Tables Occupied", f"{occupied_seats}/{TOTAL_SEATS}")

if status == "NORMAL":
    st.success("✅ Kitchen Running Smoothly")
    accepting_orders = True
elif status == "WARNING":
    st.warning("⚠️ High Kitchen Traffic - Expect Delays")
    accepting_orders = True
else:
    st.error("⛔ KITCHEN FULL: Orders Paused")
    accepting_orders = False

st.divider()

# ORDER FORM
with st.form("order_form", clear_on_submit=True):
    st.write("#### 🍔 Menu")
    dining_mode = st.radio("Dining Preference:", ["Dine-In 🍽️", "Takeaway 🛍️"], horizontal=True)
    
    if dining_mode == "Dine-In 🍽️" and occupied_seats >= (TOTAL_SEATS * 0.8):
        st.warning(f"⚠️ Warning: {occupied_seats}/{TOTAL_SEATS} tables are busy!", icon="🪑")

    c1, c2 = st.columns(2)
    burger_qty = c1.number_input("Blue Special Burger", min_value=0, max_value=5)
    fries_qty = c2.number_input("Peri Peri Fries", min_value=0, max_value=5)
    
    submit = st.form_submit_button("Confirm Order 💳")
    
    if submit:
        total_items = burger_qty + fries_qty
        order_type_str = "Dine-In" if "Dine-In" in dining_mode else "Takeaway"

        if not accepting_orders:
            st.error("🚫 Orders paused due to high wait times.")
        elif total_items == 0:
            st.warning("Please add at least one item.")
        else:
            new_order = {
                "id": int(time.time()),
                "items": f"Burger x{burger_qty}, Fries x{fries_qty}",
                "item_count": total_items,
                "type": order_type_str,
                "time": datetime.now().strftime("%H:%M"),
                "status": "Pending"  # Default status
            }
            save_order(new_order)
            st.success(f"Order Placed! ({order_type_str})")
            time.sleep(1)
            st.rerun()

time.sleep(REFRESH_INTERVAL)
st.rerun()
