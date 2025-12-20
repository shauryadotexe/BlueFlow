import streamlit as st
import json
import os
import time

DB_FILE = "orders.json"

def load_orders():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return []

def complete_order(order_id):
    orders = load_orders()
    updated_orders = [o for o in orders if o['id'] != order_id]
    with open(DB_FILE, "w") as f: json.dump(updated_orders, f, indent=4)

st.set_page_config(page_title="BlueFlow Kitchen", layout="wide")
st.title("👨‍🍳 Kitchen Display System")
st.info("Live Feed: Updates every 3 seconds...")
st.divider()

orders = load_orders()
pending_orders = [o for o in orders if o['status'] == 'Pending']
placeholder = st.empty()

with placeholder.container():
    if not pending_orders:
        st.success("All caught up!")
    else:
        # Display Cards
        for order in pending_orders:
            # Check order type (Default to Dine-In if missing)
            o_type = order.get('type', 'Dine-In')
            
            # Visual Cue: Blue for Dine-In, Orange for Takeaway
            border_color = "blue" if o_type == "Dine-In" else "orange"
            icon = "🍽️" if o_type == "Dine-In" else "🛍️"

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 4, 2, 2])
                c1.markdown(f"### #{str(order['id'])[-4:]}")
                
                # Show Type prominently
                c2.markdown(f"**{order['items']}**")
                c2.caption(f"{icon} **{o_type}**") 
                
                c3.write(f"🕒 {order['time']}")
                
                if c4.button("✅ READY", key=f"btn_{order['id']}"):
                    complete_order(order['id'])
                    st.toast("Order Completed!")
                    time.sleep(0.5)
                    st.rerun()

time.sleep(3)
st.rerun()
