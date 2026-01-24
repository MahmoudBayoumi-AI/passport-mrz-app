import streamlit as st
from passporteye import read_mrz
from PIL import Image, ImageDraw
import json
from datetime import datetime

# ==============================
# إعدادات الصفحة
# ==============================
st.set_page_config(
    page_title="قارئ جوازات السفر - MRZ Reader",
    page_icon="🛂",
    layout="wide"
)

# ==============================
# دوال مساعدة
# ==============================
def format_date(date_str):
    if not date_str or len(date_str) != 6:
        return date_str
    try:
        yy = int(date_str[:2])
        mm = date_str[2:4]
        dd = date_str[4:6]
        current_year = datetime.now().year % 100
        yyyy = 1900 + yy if yy > current_year + 10 else 2000 + yy
        return f"{dd}/{mm}/{yyyy}"
    except:
        return date_str


def format_name(names, surname):
    if not names and not surname:
        return "غير متوفر"
    names_clean = names.replace('<', ' ').strip() if names else ""
    surname_clean = surname.replace('<', ' ').strip() if surname else ""
    return f"{names_clean} {surname_clean}".strip() or "غير متوفر"


def draw_passport_frames(image: Image.Image):
    """
    🟦 إطار صفحة الجواز
    🟩 إطار MRZ
    """
    img = image.copy()
    draw = ImageDraw.Draw(img)

    w, h = img.size

    # ----- إطار صفحة الجواز -----
    margin_x = int(w * 0.05)
    margin_y = int(h * 0.05)

    page_x1 = margin_x
    page_y1 = margin_y
    page_x2 = w - margin_x
    page_y2 = h - margin_y

    draw.rectangle(
        [(page_x1, page_y1), (page_x2, page_y2)],
        outline="blue",
        width=5
    )

    # ----- إطار MRZ (الجزء السفلي) -----
    mrz_height = int(h * 0.18)

    mrz_x1 = page_x1
    mrz_y1 = h - mrz_height - margin_y
    mrz_x2 = page_x2
    mrz_y2 = h - margin_y

    draw.rectangle(
        [(mrz_x1, mrz_y1), (mrz_x2, mrz_y2)],
        outline="green",
        width=5
    )

    return img


def create_camera_guide():
    st.markdown("""
    <div style='text-align:center;padding:20px;
    background:linear-gradient(135deg,#667eea,#764ba2);
    border-radius:15px;margin-bottom:20px;color:white;'>
        <h3>📷 ضع جواز السفر داخل الإطار</h3>
        <p>تأكد من وضوح السطرين السفليين (MRZ)</p>
    </div>
    """, unsafe_allow_html=True)


# ==============================
# العنوان
# ==============================
st.title("🛂 قارئ بيانات جواز السفر")
st.markdown("**استخراج بيانات جواز السفر باستخدام MRZ**")

# ==============================
# اختيار الإدخال
# ==============================
st.subheader("📸 إدخال الصورة")

input_method = st.radio(
    "اختر الطريقة:",
    ["📁 رفع صورة", "📷 استخدام الكاميرا"],
    horizontal=True
)

uploaded_file = None

if input_method == "📁 رفع صورة":
    uploaded_file = st.file_uploader(
        "اختر صورة الجواز",
        type=["jpg", "jpeg", "png", "bmp"]
    )
else:
    create_camera_guide()
    camera_image = st.camera_input("📷 التقط صورة للجواز")
    if camera_image:
        uploaded_file = camera_image

# ==============================
# معالجة الصورة
# ==============================
if uploaded_file:
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 الصورة مع الإطار الإرشادي")

        image = Image.open(uploaded_file)
        framed_image = draw_passport_frames(image)

        st.image(framed_image, use_container_width=True)
        st.caption("🟦 صفحة الجواز | 🟩 منطقة MRZ")

        process_button = st.button(
            "🔍 استخراج البيانات",
            type="primary",
            use_container_width=True
        )

    with col2:
        if process_button:
            with st.spinner("⏳ جاري قراءة MRZ ..."):
                try:
                    uploaded_file.seek(0)
                    mrz = read_mrz(uploaded_file)

                    if mrz is None:
                        st.error("❌ لم يتم العثور على MRZ")
                    else:
                        mrz_data = mrz.to_dict()
                        st.session_state["mrz_data"] = mrz_data
                        st.session_state["processed"] = True
                except Exception as e:
                    st.error(str(e))

# ==============================
# عرض النتائج
# ==============================
if st.session_state.get("processed"):
    mrz_data = st.session_state["mrz_data"]

    st.markdown("---")
    st.header("📋 البيانات المستخرجة")

    full_name = format_name(mrz_data.get("names"), mrz_data.get("surname"))
    birth_date = format_date(mrz_data.get("date_of_birth"))
    expiry_date = format_date(mrz_data.get("expiration_date"))
    passport_number = mrz_data.get("number", "").replace("<", "")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("👤 الاسم", full_name)
        st.metric("📇 رقم الجواز", passport_number)
        st.metric("🎂 تاريخ الميلاد", birth_date)

    with c2:
        st.metric("🌍 الدولة", mrz_data.get("country"))
        st.metric("🏳️ الجنسية", mrz_data.get("nationality"))
        st.metric("📅 الانتهاء", expiry_date)

    st.markdown("---")
    st.subheader("⬇️ تحميل البيانات")

    json_data = json.dumps(mrz_data, ensure_ascii=False, indent=2)
    st.download_button(
        "📄 تحميل JSON",
        json_data,
        "passport_data.json",
        "application/json"
    )

# ==============================
# تذييل
# ==============================
st.markdown("""
<hr>
<div style="text-align:center;color:gray">
💻 Streamlit + PassportEye<br>
🔒 لا يتم حفظ أي بيانات
</div>
""", unsafe_allow_html=True)
