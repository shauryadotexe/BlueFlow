import streamlit as st
import json
import os
import time
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "orders.json"
# Kitchen Speed: 12 items/hour = 5 mins per item
KITCHEN_CAPACITY_PER_HOUR = 12  
AVG_PREP_TIME_MINS = 60 / KITCHEN_CAPACITY_PER_HOUR 

# Seating Capacity (Demo: Assume 10 tables available)
TOTAL_SEATS = 10 

# Thresholds
WAIT_THRESHOLD_WARNING = 30     
WAIT_THRESHOLD_CRITICAL = 60    
REFRESH_INTERVAL = 5 

# --- DATABASE FUNCTIONS ---
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

# --- ALGORITHM: QUEUE & SEATING ---
def calculate_metrics():
    orders = load_orders()
    
    # 1. Kitchen Load Logic
    active_orders = [o for o in orders if o['status'] == 'Pending']
    total_items = sum(o['item_count'] for o in active_orders)
    estimated_wait_mins = total_items * AVG_PREP_TIME_MINS
    
    if estimated_wait_mins >= WAIT_THRESHOLD_CRITICAL:
        kitchen_status = "CRITICAL"
    elif estimated_wait_mins >= WAIT_THRESHOLD_WARNING:
        kitchen_status = "WARNING"
    else:
        kitchen_status = "NORMAL"
        
    # 2. Seating Logic (New Feature)
    # We assume 1 active "Dine-In" order occupies 1 table/seat slot
    dine_in_orders = [o for o in active_orders if o.get('type') == 'Dine-In']
    occupied_seats = len(dine_in_orders)
    
    return total_items, estimated_wait_mins, kitchen_status, occupied_seats

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Student", layout="centered")

st.title("📱 BlueFlow Ordering")
st.markdown("Order from your room, skip the queue.")

st.caption(f"⚡ Live Status: Updating every {REFRESH_INTERVAL} seconds...")

# 1. METRICS & ALERTS
queue_items, wait_time, status, occupied_seats = calculate_metrics()

col1, col2 = st.columns(2)
col1.metric("Est. Wait Time", f"{int(wait_time)} mins")
col2.metric("Tables Occupied", f"{occupied_seats}/{TOTAL_SEATS}")

# Kitchen Status Alert
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

# 2. ORDER FORM
with st.form("order_form", clear_on_submit=True):
    st.write("#### 🍔 Menu")
    
    # NEW: Dining Preference
    dining_mode = st.radio("Dining Preference:", ["Dine-In 🍽️", "Takeaway 🛍️"], horizontal=True)
    
    # NEW: Seating Warning Logic
    # If user selects Dine-In AND seats are > 80% full, warn them!
    if dining_mode == "Dine-In 🍽️" and occupied_seats >= (TOTAL_SEATS * 0.8):
        st.warning(f"⚠️ Warning: {occupied_seats}/{TOTAL_SEATS} tables are busy. You might not find a seat!", icon="🪑")

    c1, c2 = st.columns(2)
    burger_qty = c1.number_input("Blue Special Burger", min_value=0, max_value=5)
    fries_qty = c2.number_input("Peri Peri Fries", min_value=0, max_value=5)
    
    submit = st.form_submit_button("Confirm Order 💳")
    
    if submit:
        total_items = burger_qty + fries_qty
        
        # Determine strict type string for DB
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
                "type": order_type_str, # Save the preference
                "time": datetime.now().strftime("%H:%M"),
                "status": "Pending"
            }
            save_order(new_order)
            st.success(f"Order Placed! ({order_type_str})")
            time.sleep(1)
            st.rerun()

time.sleep(REFRESH_INTERVAL)
st.rerun()
