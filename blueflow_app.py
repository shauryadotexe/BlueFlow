import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION (The "Brains" of the Algorithm) ---
KITCHEN_CAPACITY_PER_HOUR = 60  # The kitchen can make 60 items/hour
AVG_PREP_TIME_MINS = 60 / KITCHEN_CAPACITY_PER_HOUR  # 1 minute per item
WAIT_THRESHOLD_WARNING = 15     # Mins: Show yellow warning
WAIT_THRESHOLD_CRITICAL = 30    # Mins: STOP taking orders (Red state)

# --- STATE MANAGEMENT (Simulating a Database) ---
if 'orders' not in st.session_state:
    st.session_state.orders = []  # List to store active orders
if 'order_counter' not in st.session_state:
    st.session_state.order_counter = 100

# --- ALGORITHM: DYNAMIC THROTTLING LOGIC ---
def calculate_queue_metrics():
    """
    Calculates the real-time load on the kitchen.
    Returns: total_items, estimated_wait_mins, status_level
    """
    # Count total items currently in the queue (pending orders)
    active_orders = [o for o in st.session_state.orders if o['status'] == 'Pending']
    total_items = sum(o['item_count'] for o in active_orders)
    
    # Calculate Wait Time
    estimated_wait_mins = total_items * AVG_PREP_TIME_MINS
    
    # Determine Status Level
    if estimated_wait_mins >= WAIT_THRESHOLD_CRITICAL:
        status_level = "CRITICAL" # Stop Orders
    elif estimated_wait_mins >= WAIT_THRESHOLD_WARNING:
        status_level = "WARNING"  # Warn Students
    else:
        status_level = "NORMAL"   # All Good
        
    return total_items, estimated_wait_mins, status_level

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Prototype", layout="wide")

st.title("🔥 BlueFlow: Dynamic Order Throttling")
st.markdown("### Solving the '1-2 Hour Wait' Problem")

# Create two tabs to simulate two different users
tab_student, tab_kitchen = st.tabs(["📱 Student View (Ordering)", "👨‍🍳 Kitchen View (Processing)"])

# ==========================================
# TAB 1: STUDENT VIEW
# ==========================================
with tab_student:
    st.header("Place Your Order")
    
    # 1. RUN THE ALGORITHM
    queue_items, wait_time, status = calculate_queue_metrics()
    
    # 2. DISPLAY DYNAMIC STATUS (The Solution)
    col1, col2, col3 = st.columns(3)
    col1.metric("Items in Queue", f"{queue_items} items")
    col2.metric("Est. Wait Time", f"{int(wait_time)} mins")
    
    if status == "NORMAL":
        col3.success("✅ Kitchen Running Smoothly")
        accepting_orders = True
    elif status == "WARNING":
        col3.warning("⚠️ High Traffic - Expect Delays")
        accepting_orders = True
    else:
        col3.error("⛔ ORDERING PAUSED: Kitchen Full")
        accepting_orders = False

    st.divider()

    # 3. ORDERING FORM
    with st.form("order_form"):
        st.write("#### Menu")
        c1, c2 = st.columns(2)
        burger_qty = c1.number_input("Blue Special Burger", 0, 5, 0)
        fries_qty = c2.number_input("Peri Peri Fries", 0, 5, 0)
        
        total_items_in_cart = burger_qty + fries_qty
        
        # THE KILL SWITCH: Disable button if status is CRITICAL
        # Note: Streamlit form buttons can't be strictly 'disabled' via simple props, 
        # so we handle the logic inside the submit action.
        submit = st.form_submit_button("Confirm Order 💳")
        
        if submit:
            if not accepting_orders:
                st.error("🚫 Orders are currently paused due to high wait times. Please try again in 10 minutes.")
            elif total_items_in_cart == 0:
                st.warning("Please add at least one item.")
            else:
                # Add to "Database"
                new_order = {
                    "id": st.session_state.order_counter,
                    "items": f"Burger x{burger_qty}, Fries x{fries_qty}",
                    "item_count": total_items_in_cart,
                    "time": datetime.now().strftime("%H:%M"),
                    "status": "Pending"
                }
                st.session_state.orders.append(new_order)
                st.session_state.order_counter += 1
                st.success(f"Order #{new_order['id']} Placed! Estimated wait: {int(wait_time)} mins.")
                time.sleep(1)
                st.rerun()

# ==========================================
# TAB 2: KITCHEN VIEW
# ==========================================
with tab_kitchen:
    st.header("Kitchen Display System (KDS)")
    st.info("Mark orders as 'Ready' to reduce queue size and unblock the Student App.")
    
    if not st.session_state.orders:
        st.write("No active orders.")
    else:
        # Filter for pending orders
        pending_orders = [o for o in st.session_state.orders if o['status'] == 'Pending']
        
        if not pending_orders:
            st.success("All caught up! No pending orders.")
        
        for order in pending_orders:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                c1.write(f"**#{order['id']}**")
                c2.write(order['items'])
                c3.write(f"🕒 {order['time']}")
                
                # "Completing" an order reduces the queue math in Tab 1
                if c4.button("✅ Ready", key=f"btn_{order['id']}"):
                    # Update status (In real DB, we would update the row)
                    # Here we just remove it for the demo logic to work cleanly
                    st.session_state.orders.remove(order)
                    st.toast(f"Order #{order['id']} marked ready!")
                    time.sleep(0.5)
                    st.rerun()

# --- DEBUG SECTION (Optional: To test the limits quickly) ---
with st.sidebar:
    st.write("### 🛠️ Developer Tools")
    st.write("Use this to simulate a rush.")
    if st.button("Add 50 Fake Burgers (Simulate Rush)"):
        for i in range(10):
            fake_order = {
                "id": st.session_state.order_counter + i,
                "items": "Simulated Bulk Order",
                "item_count": 5, # 5 items per fake order
                "time": datetime.now().strftime("%H:%M"),
                "status": "Pending"
            }
            st.session_state.orders.append(fake_order)
        st.session_state.order_counter += 10
        st.rerun()
    
    if st.button("Clear All Orders"):
        st.session_state.orders = []
        st.rerun()