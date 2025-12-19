import streamlit as st
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

# --- ALGORITHM: DYNAMIC THROTTLING LOGIC ---
def calculate_queue_metrics():
    """Calculates the real-time load on the kitchen."""
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
    
    # 1. RUN THE ALGORITHM
    queue_items, wait_time, status = calculate_queue_metrics()
    
    # 2. DISPLAY DYNAMIC STATUS
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

    # 3. ORDERING FORM (THE FIX: clear_on_submit=True)
    # This automatically resets inputs to 0 after clicking Submit.
    # We removed the manual 'st.session_state.burger_input = 0' line to prevent the crash.
    with st.form("order_form", clear_on_submit=True):
        st.write("#### Menu")
        c1, c2 = st.columns(2)
        
        # We removed the 'key' argument to avoid session state conflicts
        burger_qty = c1.number_input("Blue Special Burger", min_value=0, max_value=5)
        fries_qty = c2.number_input("Peri Peri Fries", min_value=0, max_value=5)
        
        submit = st.form_submit_button("Confirm Order 💳")
        
        if submit:
            total_items_in_cart = burger_qty + fries_qty
            
            if not accepting_orders:
                st.error("🚫 Orders are currently paused due to high wait times.")
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
                
                # We force a rerun to update the 'Items in Queue' metric immediately
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
        pending_orders = [o for o in st.session_state.orders if o['status'] == 'Pending']
        
        if not pending_orders:
            st.success("All caught up! No pending orders.")
        
        for order in pending_orders:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                c1.write(f"**#{order['id']}**")
                c2.write(order['items'])
                c3.write(f"🕒 {order['time']}")
                
                # Using a callback for the button ensures smooth state updates
                def mark_ready(o_id=order['id']):
                     st.session_state.orders = [o for o in st.session_state.orders if o['id'] != o_id]
                
                c4.button("✅ Ready", key=f"btn_{order['id']}", on_click=mark_ready)

# --- DEBUG SECTION ---
with st.sidebar:
    st.write("### 🛠️ Developer Tools")
    
    if st.button("🟡 Simulate High Traffic (Warning)"):
        # Add 20 items -> Wait time approx 20 mins
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
        # Add 50 items -> Wait time approx 50 mins
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
