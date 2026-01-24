import streamlit as st
from passporteye import read_mrz
from PIL import Image, ImageDraw, ImageFont
import json
import io
from datetime import datetime
import numpy as np
import cv2

# إعدادات الصفحة
st.set_page_config(
    page_title="قارئ جوازات السفر - MRZ Reader",
    page_icon="🛂",
    layout="wide"
)

# دالة لرسم فريم توجيهي على الصورة
def draw_guide_frame(image, frame_type="passport"):
    """رسم فريم توجيهي على الصورة"""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # إنشاء نسخة من الصورة للرسم عليها
    overlay = img_array.copy()
    
    if frame_type == "passport":
        # فريم صفحة الجواز (مستطيل أفقي في المنتصف)
        frame_height = int(height * 0.7)
        frame_width = int(width * 0.85)
        x1 = (width - frame_width) // 2
        y1 = (height - frame_height) // 2
        x2 = x1 + frame_width
        y2 = y1 + frame_height
        
        # رسم إطار متقطع
        dash_length = 20
        gap_length = 10
        
        # الخطوط الأفقية
        for x in range(x1, x2, dash_length + gap_length):
            cv2.line(overlay, (x, y1), (min(x + dash_length, x2), y1), (102, 126, 234), 3)
            cv2.line(overlay, (x, y2), (min(x + dash_length, x2), y2), (102, 126, 234), 3)
        
        # الخطوط العمودية
        for y in range(y1, y2, dash_length + gap_length):
            cv2.line(overlay, (x1, y), (x1, min(y + dash_length, y2)), (102, 126, 234), 3)
            cv2.line(overlay, (x2, y), (x2, min(y + dash_length, y2)), (102, 126, 234), 3)
        
        # زوايا مميزة
        corner_length = 40
        cv2.line(overlay, (x1, y1), (x1 + corner_length, y1), (255, 215, 0), 5)
        cv2.line(overlay, (x1, y1), (x1, y1 + corner_length), (255, 215, 0), 5)
        cv2.line(overlay, (x2, y1), (x2 - corner_length, y1), (255, 215, 0), 5)
        cv2.line(overlay, (x2, y1), (x2, y1 + corner_length), (255, 215, 0), 5)
        cv2.line(overlay, (x1, y2), (x1 + corner_length, y2), (255, 215, 0), 5)
        cv2.line(overlay, (x1, y2), (x1, y2 - corner_length), (255, 215, 0), 5)
        cv2.line(overlay, (x2, y2), (x2 - corner_length, y2), (255, 215, 0), 5)
        cv2.line(overlay, (x2, y2), (x2, y2 - corner_length), (255, 215, 0), 5)
        
    elif frame_type == "mrz":
        # فريم منطقة MRZ (مستطيل أفقي في الأسفل)
        frame_height = int(height * 0.25)
        frame_width = int(width * 0.85)
        x1 = (width - frame_width) // 2
        y1 = height - frame_height - int(height * 0.1)
        x2 = x1 + frame_width
        y2 = y1 + frame_height
        
        # رسم إطار متقطع
        dash_length = 15
        gap_length = 8
        
        # الخطوط الأفقية
        for x in range(x1, x2, dash_length + gap_length):
            cv2.line(overlay, (x, y1), (min(x + dash_length, x2), y1), (46, 204, 113), 3)
            cv2.line(overlay, (x, y2), (min(x + dash_length, x2), y2), (46, 204, 113), 3)
        
        # الخطوط العمودية
        for y in range(y1, y2, dash_length + gap_length):
            cv2.line(overlay, (x1, y), (x1, min(y + dash_length, y2)), (46, 204, 113), 3)
            cv2.line(overlay, (x2, y), (x2, min(y + dash_length, y2)), (46, 204, 113), 3)
        
        # زوايا مميزة
        corner_length = 50
        cv2.line(overlay, (x1, y1), (x1 + corner_length, y1), (255, 69, 0), 6)
        cv2.line(overlay, (x1, y1), (x1, y1 + corner_length), (255, 69, 0), 6)
        cv2.line(overlay, (x2, y1), (x2 - corner_length, y1), (255, 69, 0), 6)
        cv2.line(overlay, (x2, y1), (x2, y1 + corner_length), (255, 69, 0), 6)
        cv2.line(overlay, (x1, y2), (x1 + corner_length, y2), (255, 69, 0), 6)
        cv2.line(overlay, (x1, y2), (x1, y2 - corner_length), (255, 69, 0), 6)
        cv2.line(overlay, (x2, y2), (x2 - corner_length, y2), (255, 69, 0), 6)
        cv2.line(overlay, (x2, y2), (x2, y2 - corner_length), (255, 69, 0), 6)
        
        # إضافة خطوط توجيهية للسطرين
        line1_y = y1 + int(frame_height * 0.35)
        line2_y = y1 + int(frame_height * 0.65)
        cv2.line(overlay, (x1 + 20, line1_y), (x2 - 20, line1_y), (52, 152, 219), 2)
        cv2.line(overlay, (x1 + 20, line2_y), (x2 - 20, line2_y), (52, 152, 219), 2)
    
    # دمج الصورة الأصلية مع الفريم
    alpha = 0.7
    result = cv2.addWeighted(overlay, alpha, img_array, 1 - alpha, 0)
    
    return Image.fromarray(result)

# دالة لقص منطقة MRZ من الصورة
def crop_mrz_region(image):
    """قص منطقة MRZ من الصورة"""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # تحديد منطقة MRZ (الربع السفلي من الصورة تقريباً)
    mrz_height = int(height * 0.35)
    y_start = height - mrz_height
    
    # قص المنطقة
    cropped = img_array[y_start:height, :]
    
    return Image.fromarray(cropped)

# دالة لتحسين جودة صورة MRZ
def enhance_mrz_image(image):
    """تحسين جودة صورة MRZ للقراءة الأفضل"""
    img_array = np.array(image)
    
    # تحويل لرمادي
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # تطبيق فلتر لتقليل الضوضاء
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # تحسين التباين
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # تطبيق threshold لتحسين الوضوح
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return Image.fromarray(binary)

# دالة لتنسيق التاريخ
def format_date(date_str):
    """تحويل التاريخ من YYMMDD إلى DD/MM/YYYY"""
    if not date_str or len(date_str) != 6:
        return date_str
    try:
        yy = int(date_str[0:2])
        mm = date_str[2:4]
        dd = date_str[4:6]
        current_year = datetime.now().year % 100
        if yy > current_year + 10:
            yyyy = 1900 + yy
        else:
            yyyy = 2000 + yy
        return f"{dd}/{mm}/{yyyy}"
    except:
        return date_str

# دالة لتنسيق الاسم
def format_name(names, surname):
    """تنسيق الاسم الكامل"""
    if not names and not surname:
        return "غير متوفر"
    
    names_clean = names.replace('<', ' ').strip() if names else ""
    surname_clean = surname.replace('<', ' ').strip() if surname else ""
    full_name = f"{names_clean} {surname_clean}".strip()
    
    return full_name if full_name else "غير متوفر"

# CSS مخصص لتحسين المظهر
st.markdown("""
<style>
    .big-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 10px 0;
    }
    .big-metric h1 {
        font-size: 3.5em;
        margin: 10px 0;
        font-weight: bold;
    }
    .big-metric p {
        font-size: 1.2em;
        margin: 5px 0;
    }
    .data-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 5px solid #667eea;
    }
    .data-card h3 {
        color: #667eea;
        margin-top: 0;
        font-size: 1.1em;
    }
    .data-card p {
        font-size: 1.8em;
        font-weight: bold;
        margin: 5px 0;
        color: #2c3e50;
    }
    .data-card small {
        color: #7f8c8d;
        font-size: 0.5em;
    }
    .validity-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
    }
    .valid-true {
        background-color: #d4edda;
        color: #155724;
    }
    .valid-false {
        background-color: #f8d7da;
        color: #721c24;
    }
    .guide-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 20px 0;
    }
    .step-indicator {
        display: inline-block;
        background: white;
        color: #667eea;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.title("🛂 قارئ بيانات جواز السفر")
st.markdown("**استخراج ذكي لبيانات جواز السفر باستخدام تقنية MRZ مع فريمات توجيهية**")

# شريط جانبي للمعلومات
with st.sidebar:
    st.header("ℹ️ معلومات")
    st.info("""
    هذا التطبيق يقرأ منطقة MRZ 
    (Machine Readable Zone) 
    من صور جوازات السفر مع:
    • فريمات توجيهية للتصوير
    • قص تلقائي لمنطقة MRZ
    • تحسين جودة الصورة
    """)
    
    st.header("📊 مقياس الدقة")
    st.success("✅ **ممتازة**: 80-100%")
    st.warning("⚠️ **جيدة**: 50-79%")
    st.error("❌ **ضعيفة**: أقل من 50%")
    
    st.markdown("---")
    
    st.header("🎯 خطوات التصوير")
    st.markdown("""
    **الخطوة 1: صفحة الجواز** 🟦
    - ضع الجواز داخل الإطار الأزرق
    - تأكد من ظهور كامل الصفحة
    
    **الخطوة 2: منطقة MRZ** 🟢
    - ركز على الإطار الأخضر
    - السطران السفليان واضحان
    
    **نصائح:**
    - إضاءة طبيعية جيدة
    - بدون ظلال أو انعكاسات
    - سطح مستوٍ
    - كاميرا مستقرة
    """)
    
    st.markdown("---")
    st.caption("💻 PassportEye + OpenCV")

# اختيار وضع التصوير
st.markdown("---")
st.subheader("📸 وضع التصوير")

capture_mode = st.radio(
    "اختر الوضع:",
    ["🔵 تصوير صفحة الجواز كاملة", "🟢 تصوير منطقة MRZ فقط", "📁 رفع صورة جاهزة"],
    horizontal=False
)

uploaded_file = None
show_guide = False

if capture_mode == "📁 رفع صورة جاهزة":
    uploaded_file = st.file_uploader(
        "اختر صورة جواز السفر",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="الصيغ المدعومة: JPG, PNG, BMP"
    )
    
    if uploaded_file:
        st.success("✅ تم رفع الصورة بنجاح!")

else:
    # عرض إرشادات حسب الوضع
    if capture_mode == "🔵 تصوير صفحة الجواز كاملة":
        st.markdown("""
        <div class="guide-box">
            <h3>🔵 الخطوة 1: تصوير صفحة الجواز</h3>
            <p>ضع جواز السفر داخل <strong>الإطار الأزرق المتقطع</strong></p>
            <p>تأكد من ظهور كامل الصفحة بما فيها منطقة MRZ السفلية</p>
            <div class="step-indicator">الزوايا الذهبية تساعدك في المحاذاة</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="guide-box">
            <h3>🟢 الخطوة 2: تصوير منطقة MRZ</h3>
            <p>ركز على <strong>الإطار الأخضر</strong> في أسفل الصورة</p>
            <p>السطران السفليان يجب أن يكونا بين <strong>الخطوط الزرقاء التوجيهية</strong></p>
            <div class="step-indicator">الزوايا البرتقالية للمحاذاة الدقيقة</div>
        </div>
        """, unsafe_allow_html=True)
    
    # عرض معاينة الفريم
    col_preview1, col_preview2 = st.columns(2)
    
    with col_preview1:
        st.markdown("**🔵 مثال: فريم صفحة الجواز**")
        # إنشاء صورة توضيحية
        sample_img = Image.new('RGB', (400, 250), color=(240, 240, 240))
        sample_with_frame = draw_guide_frame(sample_img, "passport")
        st.image(sample_with_frame, use_container_width=True)
    
    with col_preview2:
        st.markdown("**🟢 مثال: فريم منطقة MRZ**")
        sample_img2 = Image.new('RGB', (400, 250), color=(240, 240, 240))
        sample_with_frame2 = draw_guide_frame(sample_img2, "mrz")
        st.image(sample_with_frame2, use_container_width=True)
    
    st.markdown("---")
    
    # زر عرض الفريمات
    show_guide = st.checkbox("🎯 عرض الفريمات التوجيهية أثناء التصوير", value=True)
    
    # كاميرا التصوير
    camera_image = st.camera_input("📸 التقط الصورة الآن")
    
    if camera_image is not None:
        uploaded_file = camera_image
        st.success("✅ تم التقاط الصورة!")

# معالجة الصورة
if uploaded_file is not None:
    
    st.markdown("---")
    st.subheader("🔄 معالجة الصورة")
    
    # قراءة الصورة
    image = Image.open(uploaded_file)
    
    # عرض الصورة الأصلية
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("**📷 الصورة الأصلية**")
        st.image(image, use_container_width=True)
    
    # قص منطقة MRZ
    with st.spinner("✂️ جاري قص منطقة MRZ..."):
        mrz_cropped = crop_mrz_region(image)
    
    with col2:
        st.markdown("**✂️ منطقة MRZ المقصوصة**")
        st.image(mrz_cropped, use_container_width=True)
    
    # تحسين الصورة
    with st.spinner("✨ جاري تحسين جودة الصورة..."):
        mrz_enhanced = enhance_mrz_image(mrz_cropped)
    
    with col3:
        st.markdown("**✨ بعد التحسين**")
        st.image(mrz_enhanced, use_container_width=True)
    
    st.markdown("---")
    
    # زر المعالجة
    process_button = st.button("🔍 استخراج البيانات الآن", type="primary", use_container_width=True)
    
    if process_button:
        with st.spinner("⏳ جاري قراءة البيانات من MRZ..."):
            try:
                # حفظ الصورة المحسنة في buffer
                img_buffer = io.BytesIO()
                mrz_enhanced.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # قراءة MRZ
                mrz = read_mrz(img_buffer)
                
                if mrz is None:
                    st.error("❌ لم يتم العثور على منطقة MRZ في الصورة!")
                    st.warning("""
                    **يرجى المحاولة مرة أخرى مع:**
                    - تصوير أوضح لمنطقة MRZ
                    - إضاءة أفضل
                    - تجنب الظلال
                    - التأكد من استقرار الكاميرا
                    """)
                else:
                    mrz_data = mrz.to_dict()
                    
                    # عرض درجة الدقة
                    valid_score = mrz_data.get('valid_score', 0)
                    
                    if valid_score >= 80:
                        emoji = "🎉"
                        status = "ممتازة"
                    elif valid_score >= 50:
                        emoji = "👍"
                        status = "جيدة"
                    else:
                        emoji = "⚠️"
                        status = "ضعيفة"
                    
                    st.markdown(f"""
                    <div class="big-metric">
                        <p>{emoji} دقة الاستخراج</p>
                        <h1>{valid_score}%</h1>
                        <p>الحالة: {status}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # حفظ البيانات في session state
                    st.session_state['mrz_data'] = mrz_data
                    st.session_state['processed'] = True
                    st.session_state['mrz_image'] = mrz_enhanced
                    
            except Exception as e:
                st.error(f"❌ حدث خطأ: {str(e)}")
                st.info("""
                💡 **اقتراحات:**
                - جرب وضع التصوير الآخر
                - تأكد من وضوح السطرين السفليين
                - استخدم إضاءة أفضل
                - تجنب الانعكاسات على الجواز
                """)
    
    # عرض البيانات المستخرجة
    if st.session_state.get('processed', False):
        mrz_data = st.session_state['mrz_data']
        
        st.markdown("---")
        st.header("📋 البيانات المستخرجة")
        
        # تنسيق البيانات
        full_name = format_name(mrz_data.get('names'), mrz_data.get('surname'))
        birth_date = format_date(mrz_data.get('date_of_birth'))
        expiry_date = format_date(mrz_data.get('expiration_date'))
        passport_number = mrz_data.get('number', '').replace('<', '').strip()
        
        # البيانات الرئيسية
        main_col1, main_col2 = st.columns(2)
        
        with main_col1:
            st.markdown(f"""
            <div class="data-card">
                <h3>👤 الاسم الكامل</h3>
                <p>{full_name}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="data-card">
                <h3>📇 رقم جواز السفر</h3>
                <p>{passport_number}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="data-card">
                <h3>🎂 تاريخ الميلاد</h3>
                <p>{birth_date}</p>
                <small>التنسيق الأصلي: {mrz_data.get('date_of_birth', 'N/A')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with main_col2:
            st.markdown(f"""
            <div class="data-card">
                <h3>🌍 الدولة المصدرة</h3>
                <p>{mrz_data.get('country', 'غير متوفر')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="data-card">
                <h3>🏳️ الجنسية</h3>
                <p>{mrz_data.get('nationality', 'غير متوفر')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="data-card">
                <h3>📅 تاريخ انتهاء الصلاحية</h3>
                <p>{expiry_date}</p>
                <small>التنسيق الأصلي: {mrz_data.get('expiration_date', 'N/A')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # بيانات إضافية
        st.markdown("---")
        st.subheader("ℹ️ معلومات إضافية")
        
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        
        with info_col1:
            st.metric("⚧️ الجنس", mrz_data.get('sex', 'N/A'))
        with info_col2:
            st.metric("🆔 نوع الوثيقة", mrz_data.get('type', 'N/A'))
        with info_col3:
            st.metric("🔤 نوع MRZ", mrz_data.get('mrz_type', 'N/A'))
        with info_col4:
            walltime = mrz_data.get('walltime', 0)
            st.metric("⏱️ وقت المعالجة", f"{walltime:.2f}s")
        
        # حالة التحقق
        st.markdown("---")
        st.subheader("🔐 حالة التحقق من البيانات")
        
        validity_checks = [
            ("رقم الجواز", mrz_data.get('valid_number', False)),
            ("تاريخ الميلاد", mrz_data.get('valid_date_of_birth', False)),
            ("تاريخ الانتهاء", mrz_data.get('valid_expiration_date', False)),
            ("الرقم الشخصي", mrz_data.get('valid_personal_number', False)),
            ("التحقق المركب", mrz_data.get('valid_composite', False))
        ]
        
        validity_html = "<div style='text-align: center;'>"
        for check_name, is_valid in validity_checks:
            badge_class = "valid-true" if is_valid else "valid-false"
            icon = "✅" if is_valid else "❌"
            validity_html += f'<span class="validity-badge {badge_class}">{icon} {check_name}</span>'
        validity_html += "</div>"
        
        st.markdown(validity_html, unsafe_allow_html=True)
        
        # عرض صورة MRZ المستخدمة
        st.markdown("---")
        with st.expander("🔍 عرض صورة MRZ المستخدمة في القراءة"):
            st.image(st.session_state.get('mrz_image'), caption="صورة MRZ بعد القص والتحسين", use_container_width=True)
        
        # أزرار التحميل
        st.markdown("---")
        st.subheader("⬇️ تحميل البيانات")
        
        download_col1, download_col2 = st.columns(2)
        
        with download_col1:
            json_string = json.dumps(mrz_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 تحميل JSON",
                data=json_string,
                file_name="passport_data.json",
                mime="application/json",
                use_container_width=True
            )
        
        with download_col2:
            text_data = f"""
═══════════════════════════════════════
         بيانات جواز السفر
═══════════════════════════════════════

📊 دقة الاستخراج: {mrz_data.get('valid_score', 0)}%

👤 البيانات الشخصية:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الاسم الكامل: {full_name}
رقم الجواز: {passport_number}
الجنسية: {mrz_data.get('nationality', 'N/A')}
الدولة المصدرة: {mrz_data.get('country', 'N/A')}
تاريخ الميلاد: {birth_date}
تاريخ الانتهاء: {expiry_date}
الجنس: {mrz_data.get('sex', 'N/A')}
نوع الوثيقة: {mrz_data.get('type', 'N/A')}

⚙️ معلومات تقنية:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نوع MRZ: {mrz_data.get('mrz_type', 'N/A')}
طريقة المعالجة: {mrz_data.get('method', 'N/A')}
وقت المعالجة: {mrz_data.get('walltime', 0):.2f} ثانية

═══════════════════════════════════════
تم الإنشاء بواسطة MRZ Reader
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════
            """
            st.download_button(
                label="📝 تحميل TXT",
                data=text_data,
                file_name="passport_data.txt",
                mime="text/plain",
                use_container_width=True
            )

else:
    # شاشة الترحيب
    st.markdown("---")
    
    welcome_col1, welcome_col2, welcome_col3 = st.columns([1, 2, 1])
    
    with welcome_col2:
        st.markdown("""
        <div style='text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; color: white;'>
            <h2>👋 مرحباً بك في قارئ جوازات السفر المطور</h2>
            <p style='font-size: 18px; margin-top: 20px;'>
                اختر وضع التصوير من الأعلى للبدء
            </p>
            <div style='margin-top: 20px;'>
                <span class="step-indicator">فريمات توجيهية ذكية 🎯</span>
                <span class="step-indicator">قص تلقائي لـ MRZ ✂️</span>
                <span class="step-indicator">تحسين الجودة ✨</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # خطوات الاستخدام
        st.markdown("""
        ### 📝 الميزات الجديدة:
        
        #### 🎯 **فريمات توجيهية ذكية**
        - 🔵 **الإطار الأزرق**: لتصوير صفحة الجواز كاملة
        - 🟢 **الإطار الأخضر**: للتركيز على منطقة MRZ
        - 🟡 **زوايا ذهبية/برتقالية**: للمحاذاة الدقيقة
        - 🔵 **خطوط توجيهية**: لضبط موضع السطرين
        
        #### ✂️ **قص تلقائي ذكي**
        - استخراج منطقة MRZ تلقائياً من الصورة
        - تقليل حجم البيانات المعالجة
        - تحسين دقة القراءة
        
        #### ✨ **تحسين جودة متقدم**
        - تقليل الضوضاء في الصورة
        - تحسين التباين والوضوح
        - معالجة الصورة للقراءة المثلى
        
        #### 📊 **معاينة مراحل المعالجة**
        - عرض الصورة الأصلية
        - عرض المنطقة المقصوصة
        - عرض الصورة بعد التحسين
        
        ---
        
        ### 🚀 كيفية الاستخدام:
        
        **الطريقة الأولى (موصى بها):**
        1. اختر "🔵 تصوير صفحة الجواز كاملة"
        2. ضع الجواز داخل الإطار الأزرق
        3. التقط الصورة
        4. سيتم قص وتحسين MRZ تلقائياً
        
        **الطريقة الثانية:**
        1. اختر "🟢 تصوير منطقة MRZ فقط"
        2. ركز على الإطار الأخضر
        3. اجعل السطرين بين الخطوط الزرقاء
        4. التقط الصورة
        
        **الطريقة الثالثة:**
        1. اختر "📁 رفع صورة جاهزة"
        2. ارفع صورة من المعرض
        3. سيتم المعالجة تلقائياً
        
        ---
        
        ### 💡 نصائح للحصول على أفضل نتيجة:
        
        ✅ **إضاءة:**
        - استخدم إضاءة طبيعية أو مصباح أبيض
        - تجنب الإضاءة الصفراء
        - لا تستخدم الفلاش مباشرة
        
        ✅ **وضعية الجواز:**
        - ضعه على سطح مستوٍ
        - تجنب الميلان أو الانحناء
        - لا تقطع أي جزء من MRZ
        
        ✅ **الكاميرا:**
        - امسك الهاتف بثبات
        - صور من مسافة مناسبة (20-30 سم)
        - تأكد من الوضوح قبل الالتقاط
        
        ✅ **البيئة:**
        - تجنب الظلال على الجواز
        - لا تصور في مكان مظلم
        - تجنب الانعكاسات اللامعة
        """)

# تذييل
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 20px;'>
    <p>💻 تم التطوير باستخدام Streamlit + PassportEye + OpenCV</p>
    <p>🎯 مع فريمات توجيهية ذكية وقص تلقائي لـ MRZ</p>
    <p>🔒 جميع البيانات تتم معالجتها محلياً - لا يتم حفظ أي معلومات</p>
    <p style='font-size: 12px; margin-top: 10px;'>© 2024 MRZ Reader Pro - All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
