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
    • قص تلقائي لمنطقة MRZ
    • تحسين جودة الصورة
    • استخراج ذكي للبيانات
    """)
    
    st.header("📊 مقياس الدقة")
    st.success("✅ **ممتازة**: 80-100%")
    st.warning("⚠️ **جيدة**: 50-79%")
    st.error("❌ **ضعيفة**: أقل من 50%")
    
    st.markdown("---")
    
    st.header("🎯 نصائح للتصوير")
    st.markdown("""
    **📸 التصوير:**
    - ضع الجواز على سطح مستوٍ
    - تأكد من ظهور كامل الصفحة
    - السطران السفليان واضحان
    
    **💡 الإضاءة:**
    - إضاءة طبيعية جيدة
    - بدون ظلال أو انعكاسات
    - تجنب الفلاش المباشر
    
    **✨ الجودة:**
    - كاميرا مستقرة
    - صورة واضحة غير ضبابية
    - بدون انعكاسات لامعة
    """)
    
    st.markdown("---")
    st.caption("💻 PassportEye + OpenCV")

# طريقة إدخال الصورة
st.markdown("---")
st.subheader("📸 طريقة إدخال الصورة")

input_method = st.radio(
    "اختر المصدر:",
    ["📁 رفع من المعرض", "📷 التقاط من الكاميرا"],
    horizontal=True
)

uploaded_file = None

if input_method == "📁 رفع من المعرض":
    uploaded_file = st.file_uploader(
        "اختر صورة جواز السفر",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="الصيغ المدعومة: JPG, PNG, BMP"
    )
    
    if uploaded_file:
        st.success("✅ تم رفع الصورة بنجاح!")

else:
    # عرض إرشادات التصوير
    st.markdown("""
    <div class="guide-box">
        <h3>📸 إرشادات التصوير</h3>
        <p>✅ تأكد من ظهور <strong>كامل صفحة الجواز</strong> في الصورة</p>
        <p>✅ السطران السفليان (<strong>منطقة MRZ</strong>) يجب أن يكونا واضحين تماماً</p>
        <p>✅ استخدم إضاءة جيدة وتجنب الظلال</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # كاميرا التصوير
    camera_image = st.camera_input("📸 التقط صورة واضحة لجواز السفر")
    
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
            <h2>👋 مرحباً بك في قارئ جوازات السفر</h2>
            <p style='font-size: 18px; margin-top: 20px;'>
                اختر طريقة إدخال الصورة من الأعلى للبدء
            </p>
            <div style='margin-top: 20px;'>
                <span class="step-indicator">قص تلقائي لـ MRZ ✂️</span>
                <span class="step-indicator">تحسين الجودة ✨</span>
                <span class="step-indicator">استخراج ذكي 🎯</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # خطوات الاستخدام
        st.markdown("""
        ### 📝 الميزات:
        
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
        
        1. **اختر طريقة الإدخال**: رفع من المعرض أو التقاط من الكاميرا
        2. **أدخل الصورة**: تأكد من وضوح منطقة MRZ (السطران السفليان)
        3. **انتظر المعالجة**: سيتم قص وتحسين MRZ تلقائياً
        4. **اضغط استخراج البيانات**: احصل على النتائج فوراً
        
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
    <p>✂️ مع قص تلقائي لمنطقة MRZ وتحسين ذكي للصور</p>
    <p>🔒 جميع البيانات تتم معالجتها محلياً - لا يتم حفظ أي معلومات</p>
    <p style='font-size: 12px; margin-top: 10px;'>© 2024 MRZ Reader - All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
