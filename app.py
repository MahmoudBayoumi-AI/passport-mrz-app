import streamlit as st
import cv2
import numpy as np
from PIL import Image
from passporteye import read_mrz
import pytesseract

# =========================
# إعداد الصفحة
# =========================
st.set_page_config(page_title="Passport MRZ Scanner", layout="centered")
st.title("🛂 Passport MRZ Scanner")
st.write("📷 ضع الجواز داخل الإطار السفلي ثم التقط الصورة")

# =========================
# ثوابت الفريم (MRZ Area)
# =========================
FRAME_HEIGHT_RATIO = 0.25   # نسبة ارتفاع MRZ من الصورة
FRAME_MARGIN = 40           # هامش جانبي

# =========================
# فتح الكاميرا
# =========================
camera_image = st.camera_input("📸 Camera")

if camera_image:

    # =========================
    # قراءة الصورة
    # =========================
    image = Image.open(camera_image)
    image_np = np.array(image)
    h, w, _ = image_np.shape

    # =========================
    # تحديد منطقة MRZ (أسفل الصورة)
    # =========================
    mrz_height = int(h * FRAME_HEIGHT_RATIO)

    x1 = FRAME_MARGIN
    x2 = w - FRAME_MARGIN
    y1 = h - mrz_height
    y2 = h - FRAME_MARGIN

    # =========================
    # رسم الفريم على الصورة
    # =========================
    framed_image = image_np.copy()
    cv2.rectangle(
        framed_image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        3
    )

    st.image(framed_image, caption="📐 MRZ Frame", channels="RGB")

    # =========================
    # قص MRZ
    # =========================
    mrz_crop = image_np[y1:y2, x1:x2]

    st.image(mrz_crop, caption="✂️ Cropped MRZ", channels="RGB")

    # =========================
    # Preprocessing
    # =========================
    gray = cv2.cvtColor(mrz_crop, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    st.image(thresh, caption="⚙️ Preprocessed MRZ", clamp=True)

    # =========================
    # OCR باستخدام PassportEye
    # =========================
    try:
        mrz = read_mrz(Image.fromarray(thresh))

        if mrz is not None:
            mrz_data = mrz.to_dict()

            st.success("✅ MRZ Detected Successfully")

            st.subheader("📄 Extracted Passport Data")

            st.write(f"**Document Type:** {mrz_data.get('type')}")
            st.write(f"**Country:** {mrz_data.get('country')}")
            st.write(f"**Surname:** {mrz_data.get('surname')}")
            st.write(f"**Given Names:** {mrz_data.get('names')}")
            st.write(f"**Passport Number:** {mrz_data.get('number')}")
            st.write(f"**Nationality:** {mrz_data.get('nationality')}")
            st.write(f"**Date of Birth:** {mrz_data.get('date_of_birth')}")
            st.write(f"**Sex:** {mrz_data.get('sex')}")
            st.write(f"**Expiration Date:** {mrz_data.get('expiration_date')}")

            st.subheader("🧾 Raw MRZ Lines")
            for line in mrz_data.get("raw_text", []):
                st.code(line)

        else:
            st.error("❌ MRZ not detected. Try adjusting the passport position.")

    except Exception as e:
        st.error("⚠️ OCR Error")
        st.code(str(e))
