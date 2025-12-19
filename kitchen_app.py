import streamlit as st
import json
import os
import time

# --- CONFIGURATION ---
DB_FILE = "orders.json"

# --- DATABASE FUNCTIONS ---
def load_orders():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def complete_order(order_id):
    orders = load_orders()
    updated_orders = [o for o in orders if o['id'] != order_id]
    with open(DB_FILE, "w") as f:
        json.dump(updated_orders, f, indent=4)

# --- UI LAYOUT ---
st.set_page_config(page_title="BlueFlow Kitchen", layout="wide")

st.title("👨‍🍳 Kitchen Display System (KDS)")
st.info("Live Feed: Updates every 3 seconds...")

st.divider()

# LOAD DATA
orders = load_orders()
pending_orders = [o for o in orders if o['status'] == 'Pending']

# 1. EMPTY CONTAINER FOR CONTENT
# We use a container so we can overwrite it if needed, though reruns handle this mostly.
placeholder = st.empty()

with placeholder.container():
    if not pending_orders:
        st.success("All caught up! No pending orders.")
    else:
        for order in pending_orders:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 4, 2, 2])
                c1.markdown(f"### #{str(order['id'])[-4:]}")
                c2.markdown(f"**{order['items']}**")
                c3.write(f"🕒 {order['time']}")
                
                # Button Logic
                if c4.button("✅ READY", key=f"btn_{order['id']}"):
                    complete_order(order['id'])
                    st.toast(f"Order #{str(order['id'])[-4:]} Completed!")
                    time.sleep(0.5)
                    st.rerun()

# 2. THE AUTO-REFRESH "HACK"
# This simple line makes the script wait 3 seconds, then restart from the top.
time.sleep(3) 
st.rerun()
