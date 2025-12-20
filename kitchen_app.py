import streamlit as st
import json
import os
import time

DB_FILE = "orders.json"

# --- DATABASE FUNCTIONS ---
def load_orders():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def update_order_status(order_id, new_status):
    """Updates status from Pending -> Ready"""
    orders = load_orders()
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            break
    with open(DB_FILE, "w") as f: json.dump(orders, f, indent=4)

def delete_order(order_id):
    """Final step: Remove from DB when served"""
    orders = load_orders()
    updated_orders = [o for o in orders if o['id'] != order_id]
    with open(DB_FILE, "w") as f: json.dump(updated_orders, f, indent=4)

# --- NEW HELPER: BATCH COUNTING ---
def get_batch_counts(orders):
    """Parses order strings to calculate total burgers and fries needed."""
    total_burgers = 0
    total_fries = 0
    
    for order in orders:
        # String format is: "Burger x{qty}, Fries x{qty}"
        # We parse this string to get the integers back
        try:
            items_str = order['items']
            parts = items_str.split(',') # ['Burger x2', ' Fries x1']
            
            for part in parts:
                if "Burger" in part:
                    # Split by 'x' and take the second part (the number)
                    qty = int(part.lower().split('x')[1].strip())
                    total_burgers += qty
                elif "Fries" in part:
                    qty = int(part.lower().split('x')[1].strip())
                    total_fries += qty
        except:
            continue
            
    return total_burgers, total_fries

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Kitchen", layout="wide")
st.title("👨‍🍳 Kitchen Display System")
st.info("Live Feed: Updates every 3 seconds...")

orders = load_orders()

# Filter by Status
pending_orders = [o for o in orders if o['status'] == 'Pending']
ready_orders = [o for o in orders if o['status'] == 'Ready']

placeholder = st.empty()

with placeholder.container():
    
    # --- NEW: BATCH DASHBOARD ---
    if pending_orders:
        t_burgers, t_fries = get_batch_counts(pending_orders)
        
        st.markdown("### 🍳 Production View (Total Needed)")
        # Display large metrics for the chef
        m1, m2, m3 = st.columns(3)
        m1.metric("🍔 Burgers to Grill", f"{t_burgers}", delta_color="inverse")
        m2.metric("🍟 Fries to Fry", f"{t_fries}", delta_color="inverse")
        m3.metric("📝 Active Tickets", f"{len(pending_orders)}")
        st.divider()

    # SECTION 1: INDIVIDUAL TICKETS
    st.subheader(f"🔥 Ticket Queue")
    
    if not pending_orders and not ready_orders:
        st.success("All caught up! No active orders.")

    if pending_orders:
        # Display newest first? Or oldest first? 
        # Kitchens usually want Oldest First (FIFO) to keep wait times fair.
        for order in pending_orders:
            o_type = order.get('type', 'Dine-In')
            icon = "🍽️" if o_type == "Dine-In" else "🛍️"
            
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 4, 2, 2])
                c1.markdown(f"### #{str(order['id'])[-4:]}")
                c2.markdown(f"**{order['items']}**")
                c2.caption(f"{icon} **{o_type}**")
                c3.write(f"🕒 {order['time']}")
                
                # MARK READY BUTTON
                if c4.button("✅ MARK READY", key=f"ready_{order['id']}"):
                    update_order_status(order['id'], "Ready")
                    st.toast(f"Order #{str(order['id'])[-4:]} is Ready!")
                    time.sleep(0.5)
                    st.rerun()

    if ready_orders:
        st.divider()
        # SECTION 2: READY FOR PICKUP
        st.subheader(f"🔔 Ready for Pickup ({len(ready_orders)})")
        
        for order in ready_orders:
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 5, 2])
                col1.success(f"#{str(order['id'])[-4:]}")
                col2.write(f"**{order['items']}** ({order.get('type', 'Dine-In')})")
                
                # FINAL SERVED BUTTON
                if col3.button("👋 SERVED", key=f"served_{order['id']}"):
                    delete_order(order['id'])
                    st.toast("Order Served & Closed!")
                    time.sleep(0.5)
                    st.rerun()

time.sleep(3)
st.rerun()
