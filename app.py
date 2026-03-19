import streamlit as st
import json
import os
import numpy as np
from PIL import Image
import requests
import tempfile

# SAFE IMPORTS (NO CRASH ON CLOUD)
try:
    import cv2
    import mediapipe as mp
    CV2_AVAILABLE = True
except:
    CV2_AVAILABLE = False

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Fashion Store", layout="wide")

DATA_FILE = "products.json"

# ---------------------------
# DATA FUNCTIONS
# ---------------------------
def load_products():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=4)

# ---------------------------
# SESSION STATE
# ---------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

# ---------------------------
# FLOATING AR BUTTON
# ---------------------------
st.markdown("""
<style>
div.stButton > button:first-child {
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #ff4b4b;
    color: white;
    border-radius: 50px;
    padding: 10px 18px;
    z-index: 9999;
}
</style>
""", unsafe_allow_html=True)

if st.button("🧥 AR Try-On"):
    st.session_state.page = "tryon"

# ---------------------------
# HOME
# ---------------------------
def home():
    st.title("🛍️ Fashion Store")

    st.image(
        "https://images.unsplash.com/photo-1521335629791-ce4aec67dd53",
        use_container_width=True
    )

    st.subheader("Categories")
    cols = st.columns(3)

    for i, cat in enumerate(["Men", "Women", "Kids"]):
        if cols[i].button(cat):
            st.session_state.page = "shop"

    st.subheader("Featured Products")
    products = load_products()

    cols = st.columns(4)
    for i, p in enumerate(products[:4]):
        with cols[i % 4]:
            st.image(p["image"])
            st.write(p["name"])
            st.write(f"${p['price']}")

            if st.button("View", key=f"home_{i}"):
                st.session_state.selected_product = p
                st.session_state.page = "detail"

# ---------------------------
# SHOP
# ---------------------------
def shop():
    st.title("🛒 Shop")

    products = load_products()

    search = st.text_input("Search")
    category = st.selectbox("Category", ["All", "Men", "Women", "Kids"])

    filtered = [
        p for p in products
        if search.lower() in p["name"].lower()
        and (category == "All" or p["category"] == category)
    ]

    cols = st.columns(4)
    for i, p in enumerate(filtered):
        with cols[i % 4]:
            st.image(p["image"])
            st.write(p["name"])
            st.write(f"${p['price']}")

            if st.button("View", key=f"shop_{i}"):
                st.session_state.selected_product = p
                st.session_state.page = "detail"

# ---------------------------
# PRODUCT DETAIL
# ---------------------------
def detail():
    p = st.session_state.selected_product

    st.image(p["image"], width=300)
    st.title(p["name"])
    st.write(p["description"])
    st.write(f"Price: ${p['price']}")

    if st.button("Add to Cart"):
        st.session_state.cart.append(p)
        st.success("Added to cart")

    if st.button("Try On"):
        st.session_state.page = "tryon"

# ---------------------------
# CART
# ---------------------------
def cart():
    st.title("🧺 Cart")

    total = 0

    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([2,1,1])

        col1.write(item["name"])
        col2.write(f"${item['price']}")

        if col3.button("Remove", key=f"remove_{i}"):
            st.session_state.cart.pop(i)
            st.rerun()

        total += item["price"]

    st.subheader(f"Total: ${total}")

# ---------------------------
# ADMIN
# ---------------------------
def admin():
    st.title("⚙️ Admin Panel")

    name = st.text_input("Product Name")
    price = st.number_input("Price")
    image = st.text_input("Image URL (PNG recommended)")
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
        st.success("Product added")

# ---------------------------
# TRY-ON SYSTEM
# ---------------------------
def tryon():
    st.title("🧥 AI Virtual Try-On")

    products = load_products()

    if not products:
        st.warning("No products available")
        return

    selected = st.selectbox(
        "Select Clothing",
        products,
        format_func=lambda x: x["name"]
    )

    mode = st.radio(
        "Mode",
        ["Cloud (Photo)", "Real-Time AI (Local Only)"]
    )

    # -----------------------
    # CLOUD MODE (SAFE)
    # -----------------------
    if mode == "Cloud (Photo)":
        img_file = st.camera_input("Take a photo")

        if img_file:
            user_img = Image.open(img_file).convert("RGBA")

            cloth = Image.open(
                requests.get(selected["image"], stream=True).raw
            ).convert("RGBA")

            cloth = cloth.resize((250, 250))

            user_img.paste(cloth, (120, 100), cloth)

            st.image(user_img)
            st.success("Try-On Applied")

    # -----------------------
    # REAL AI MODE (LOCAL)
    # -----------------------
    else:
        st.warning("⚠️ Works only on LOCAL machine")

        if not CV2_AVAILABLE:
            st.error("OpenCV not available")
            return

        run = st.checkbox("Start Camera")

        FRAME_WINDOW = st.image([])

        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose()

        cap = cv2.VideoCapture(0)

        cloth = Image.open(
            requests.get(selected["image"], stream=True).raw
        ).convert("RGBA")

        cloth = np.array(cloth)

        scale = st.slider("Scale", 0.5, 2.0, 1.0)

        while run:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            result = pose.process(rgb)

            if result.pose_landmarks:
                h, w, _ = frame.shape

                l = result.pose_landmarks.landmark[11]
                r = result.pose_landmarks.landmark[12]

                x1, y1 = int(l.x*w), int(l.y*h)
                x2, y2 = int(r.x*w), int(r.y*h)

                width = abs(x2 - x1)

                cloth_w = int(width * 1.8 * scale)
                cloth_h = int(cloth.shape[0] * (cloth_w / cloth.shape[1]))

                resized = cv2.resize(cloth, (cloth_w, cloth_h))

                x = int((x1 + x2)/2 - cloth_w/2)
                y = int(y1 - cloth_h/3)

                for i in range(cloth_h):
                    for j in range(cloth_w):
                        if resized[i, j][3] > 0:
                            if 0 <= y+i < h and 0 <= x+j < w:
                                frame[y+i, x+j] = resized[i, j][:3]

            FRAME_WINDOW.image(frame, channels="BGR")

        cap.release()

# ---------------------------
# NAVIGATION
# ---------------------------
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
    detail()

if st.session_state.page == "tryon":
    tryon()
