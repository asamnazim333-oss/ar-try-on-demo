import streamlit as st
import json
import os
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp

# ------------------------------
# CONFIG
# ------------------------------
st.set_page_config(page_title="Fashion Store", layout="wide")

DATA_FILE = "products.json"

# ------------------------------
# LOAD / SAVE DATA
# ------------------------------
def load_products():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=4)

# ------------------------------
# SESSION STATE
# ------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

# ------------------------------
# HEADER
# ------------------------------
st.markdown("""
<style>
.floating-btn {
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #ff4b4b;
    color: white;
    padding: 12px 18px;
    border-radius: 50px;
    font-weight: bold;
    z-index: 1000;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# Floating AR Button
if st.button("🧥 Try AR", key="ar_btn"):
    st.session_state.page = "tryon"

# ------------------------------
# HOME PAGE
# ------------------------------
def home():
    st.title("🛍️ Fashion Store")
    st.image("https://images.unsplash.com/photo-1521335629791-ce4aec67dd53", use_container_width=True)

    st.subheader("Categories")
    cols = st.columns(3)
    categories = ["Men", "Women", "Kids"]

    for i, cat in enumerate(categories):
        if cols[i].button(cat):
            st.session_state.page = "shop"

    st.subheader("Featured Products")

    products = load_products()
    cols = st.columns(4)

    for i, product in enumerate(products[:4]):
        with cols[i % 4]:
            st.image(product["image"])
            st.write(product["name"])
            st.write(f"${product['price']}")
            if st.button("View", key=f"view_{i}"):
                st.session_state.selected_product = product
                st.session_state.page = "detail"

# ------------------------------
# SHOP PAGE
# ------------------------------
def shop():
    st.title("🛒 Shop")

    products = load_products()

    search = st.text_input("Search")
    category = st.selectbox("Category", ["All", "Men", "Women", "Kids"])

    filtered = []
    for p in products:
        if (search.lower() in p["name"].lower()) and (category == "All" or p["category"] == category):
            filtered.append(p)

    cols = st.columns(4)
    for i, product in enumerate(filtered):
        with cols[i % 4]:
            st.image(product["image"])
            st.write(product["name"])
            st.write(f"${product['price']}")

            if st.button("View", key=f"shop_{i}"):
                st.session_state.selected_product = product
                st.session_state.page = "detail"

# ------------------------------
# PRODUCT DETAIL
# ------------------------------
def product_detail():
    product = st.session_state.selected_product

    st.image(product["image"], width=300)
    st.title(product["name"])
    st.write(product["description"])
    st.write(f"Price: ${product['price']}")

    size = st.selectbox("Size", ["S", "M", "L"])
    color = st.selectbox("Color", ["Black", "White", "Blue"])

    if st.button("Add to Cart"):
        st.session_state.cart.append(product)

    if st.button("Try On"):
        st.session_state.page = "tryon"

# ------------------------------
# CART
# ------------------------------
def cart():
    st.title("🧺 Cart")

    total = 0
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([2,1,1])

        with col1:
            st.write(item["name"])
        with col2:
            st.write(f"${item['price']}")
        with col3:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()

        total += item["price"]

    st.subheader(f"Total: ${total}")

# ------------------------------
# ADMIN PANEL
# ------------------------------
def admin():
    st.title("⚙️ Admin Panel")

    name = st.text_input("Product Name")
    price = st.number_input("Price")
    image = st.text_input("Image URL")
    category = st.selectbox("Category", ["Men", "Women", "Kids"])
    desc = st.text_area("Description")

    if st.button("Add Product"):
        products = load_products()
        products.append({
            "name": name,
            "price": price,
            "image": image,
            "category": category,
            "description": desc
        })
        save_products(products)
        st.success("Product Added")

    st.subheader("All Products")
    products = load_products()

    for i, p in enumerate(products):
        st.write(p["name"])
        if st.button("Delete", key=f"del_{i}"):
            products.pop(i)
            save_products(products)
            st.rerun()

# ------------------------------
# VIRTUAL TRY-ON (AI)
# ------------------------------
def tryon():
    st.title("🧥 Virtual Try-On")

    st.info("Allow camera access")

    run = st.checkbox("Start Camera")

    FRAME_WINDOW = st.image([])

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(0)

    overlay_img = None
    products = load_products()

    if products:
        selected = st.selectbox("Select Clothing", products, format_func=lambda x: x["name"])
        overlay_img = cv2.imread(selected["image"]) if selected["image"].startswith("http") == False else None

    scale = st.slider("Scale", 0.5, 2.0, 1.0)
    x_offset = st.slider("X Position", -200, 200, 0)
    y_offset = st.slider("Y Position", -200, 200, 0)

    while run:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = pose.process(rgb)

        if result.pose_landmarks and overlay_img is not None:
            h, w, _ = frame.shape

            shoulder = result.pose_landmarks.landmark[11]
            x = int(shoulder.x * w)
            y = int(shoulder.y * h)

            resized = cv2.resize(overlay_img, None, fx=scale, fy=scale)

            h2, w2, _ = resized.shape

            y1 = max(0, y - h2//2 + y_offset)
            x1 = max(0, x - w2//2 + x_offset)

            try:
                frame[y1:y1+h2, x1:x1+w2] = resized
            except:
                pass

        FRAME_WINDOW.image(frame, channels="BGR")

    cap.release()

# ------------------------------
# NAVIGATION
# ------------------------------
menu = st.sidebar.radio("Menu", ["Home", "Shop", "Cart", "Admin"])

if menu == "Home":
    home()
elif menu == "Shop":
    shop()
elif menu == "Cart":
    cart()
elif menu == "Admin":
    admin()

if st.session_state.page == "detail":
    product_detail()

if st.session_state.page == "tryon":
    tryon()
