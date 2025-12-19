import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION ---
KITCHEN_CAPACITY_PER_HOUR = 60
AVG_PREP_TIME_MINS = 60 / KITCHEN_CAPACITY_PER_HOUR
WAIT_THRESHOLD_WARNING = 15
WAIT_THRESHOLD_CRITICAL = 30

# --- STATE MANAGEMENT ---
if 'orders' not in st.session_state:
    st.session_state.orders = []
if 'order_counter' not in st.session_state:
    st.session_state.order_counter = 100

# --- ALGORITHM ---
def calculate_queue_metrics():
    """Calculates load based on current session state."""
    active_orders = [o for o in st.session_state.orders if o['status'] == 'Pending']
    total_items = sum(o['item_count'] for o in active_orders)
    estimated_wait_mins = total_items * AVG_PREP_TIME_MINS
    
    if estimated_wait_mins >= WAIT_THRESHOLD_CRITICAL:
        status_level = "CRITICAL"
    elif estimated_wait_mins >= WAIT_THRESHOLD_WARNING:
        status_level = "WARNING"
    else:
        status_level = "NORMAL"
        
    return total_items, estimated_wait_mins, status_level

# --- CALLBACK FUNCTION (The Fix) ---
def place_order_callback():
    """
    Handles validation, DB update, and form reset.
    Runs BEFORE the script reruns, preventing the API Exception.
    """
    # 1. Check constraints again inside the callback
    _, _, status = calculate_queue_metrics()
    
    # 2. Get values directly from Session State
    burger_qty = st.session_state.burger_input
    fries_qty = st.session_state.fries_input
    total_items = burger_qty + fries_qty
    
    # 3. Validation Logic
    if status == "CRITICAL":
        st.toast("🚫 Order Blocked: High Wait Times!", icon="❌")
        return # Do not process
    
    if total_items == 0:
        st.toast("⚠️ Please add at least one item.", icon="⚠️")
        return # Do not process

    # 4. Success Logic: Add to Database
    new_order = {
        "id": st.session_state.order_counter,
        "items": f"Burger x{burger_qty}, Fries x{fries_qty}",
        "item_count": total_items,
        "time": datetime.now().strftime("%H:%M"),
        "status": "Pending"
    }
    st.session_state.orders.append(new_order)
    st.session_state.order_counter += 1
    
    # 5. THE FIX: Reset the widgets safely here
    st.session_state.burger_input = 0
    st.session_state.fries_input = 0
    
    st.toast(f"✅ Order #{new_order['id']} Placed Successfully!")

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Prototype", layout="wide")
st.title("🔥 BlueFlow: Dynamic Order Throttling")
st.markdown("### Solving the '1-2 Hour Wait' Problem")

tab_student, tab_kitchen = st.tabs(["📱 Student View (Ordering)", "👨‍🍳 Kitchen View (Processing)"])

# ==========================================
# TAB 1: STUDENT VIEW
# ==========================================
with tab_student:
    st.header("Place Your Order")
    
    # Run Algorithm for Display
    queue_items, wait_time, status = calculate_queue_metrics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Items in Queue", f"{queue_items} items")
    col2.metric("Est. Wait Time", f"{int(wait_time)} mins")
    
    if status == "NORMAL":
        col3.success("✅ Kitchen Running Smoothly")
    elif status == "WARNING":
        col3.warning("⚠️ High Traffic - Expect Delays")
    else:
        col3.error("⛔ ORDERING PAUSED: Kitchen Full")

    st.divider()

    # Form with Callback
    with st.form("order_form"):
        st.write("#### Menu")
        c1, c2 = st.columns(2)
        
        # We bind these inputs to keys, but we don't modify them manually anymore
        st.number_input("Blue Special Burger", 0, 5, key='burger_input')
        st.number_input("Peri Peri Fries", 0, 5, key='fries_input')
        
        # KEY CHANGE: logic moved to 'on_click=place_order_callback'
        st.form_submit_button("Confirm Order 💳", on_click=place_order_callback)

# ==========================================
# TAB 2: KITCHEN VIEW
# ==========================================
with tab_kitchen:
    st.header("Kitchen Display System (KDS)")
    st.info("Mark orders as 'Ready' to unblock the Student App.")
    
    pending_orders = [o for o in st.session_state.orders if o['status'] == 'Pending']
    
    if not pending_orders:
        st.success("All caught up!")
    else:
        for order in pending_orders:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                c1.write(f"**#{order['id']}**")
                c2.write(order['items'])
                c3.write(f"🕒 {order['time']}")
                
                # Callback for the "Ready" button
                def mark_ready(o_id=order['id']):
                    # Find order by ID and remove it (or update status)
                    st.session_state.orders = [o for o in st.session_state.orders if o['id'] != o_id]
                    st.toast(f"Order #{o_id} ready!")

                c4.button("✅ Ready", key=f"btn_{order['id']}", on_click=mark_ready)

# --- DEBUG TOOLS ---
with st.sidebar:
    st.write("### 🛠️ Developer Tools")
    
    if st.button("🟡 Simulate High Traffic (Warning)"):
        for i in range(4):
            st.session_state.orders.append({
                "id": st.session_state.order_counter + i,
                "items": "Simulated Crowd",
                "item_count": 5, 
                "time": datetime.now().strftime("%H:%M"),
                "status": "Pending"
            })
        st.session_state.order_counter += 4
        st.rerun()

    if st.button("🔴 Simulate Rush Hour (Blocked)"):
        for i in range(10):
            st.session_state.orders.append({
                "id": st.session_state.order_counter + i,
                "items": "Simulated Rush",
                "item_count": 5,
                "time": datetime.now().strftime("%H:%M"),
                "status": "Pending"
            })
        st.session_state.order_counter += 10
        st.rerun()
    
    if st.button("Clear All Orders"):
        st.session_state.orders = []
        st.rerun()
