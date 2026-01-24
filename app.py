import streamlit as st
from passporteye import read_mrz
from PIL import Image, ImageDraw
import json
import io
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(
    page_title="قارئ جوازات السفر - MRZ Reader",
    page_icon="🛂",
    layout="wide"
)

# دالة لتنسيق التاريخ
def format_date(date_str):
    """تحويل التاريخ من YYMMDD إلى DD/MM/YYYY"""
    if not date_str or len(date_str) != 6:
        return date_str
    try:
        yy = int(date_str[0:2])
        mm = date_str[2:4]
        dd = date_str[4:6]
        # تحديد القرن (19xx أو 20xx)
        current_year = datetime.now().year % 100
        if yy > current_year + 10:  # إذا كان في المستقبل البعيد، يكون 19xx
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
    
    # تنظيف الاسماء
    names_clean = names.replace('<', ' ').strip() if names else ""
    surname_clean = surname.replace('<', ' ').strip() if surname else ""
    
    # دمج الاسم الكامل
    full_name = f"{names_clean} {surname_clean}".strip()
    
    return full_name if full_name else "غير متوفر"

# دالة لإنشاء إطار الكاميرا
def create_camera_guide():
    """إنشاء صورة إرشادية لإطار الكاميرا"""
    st.markdown("""
    <div style='position: relative; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 20px;'>
        <h3 style='color: white; margin: 0;'>📷 ضع جواز السفر داخل الإطار</h3>
        <p style='color: white; margin: 10px 0 0 0; font-size: 14px;'>تأكد من ظهور منطقة MRZ (السطور السفلية) بوضوح</p>
    </div>
    """, unsafe_allow_html=True)
    
    # إرشادات التصوير
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("✅ **إضاءة جيدة**")
    with col2:
        st.markdown("✅ **بدون ظلال**")
    with col3:
        st.markdown("✅ **MRZ واضح**")

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
    .camera-frame {
        border: 3px dashed #667eea;
        border-radius: 10px;
        padding: 10px;
        background-color: rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.title("🛂 قارئ بيانات جواز السفر")
st.markdown("**استخراج ذكي لبيانات جواز السفر باستخدام تقنية MRZ**")

# شريط جانبي للمعلومات
with st.sidebar:
    st.header("ℹ️ معلومات")
    st.info("""
    هذا التطبيق يقرأ منطقة MRZ 
    (Machine Readable Zone) 
    من صور جوازات السفر
    """)
    
    st.header("📊 مقياس الدقة")
    st.success("✅ **ممتازة**: 80-100%")
    st.warning("⚠️ **جيدة**: 50-79%")
    st.error("❌ **ضعيفة**: أقل من 50%")
    
    st.markdown("---")
    
    st.header("🎯 نصائح للحصول على أفضل نتيجة")
    st.markdown("""
    - استخدم إضاءة طبيعية
    - تجنب الظلال والانعكاسات
    - ضع الجواز على سطح مستوٍ
    - تأكد من وضوح السطرين السفليين
    - لا تقص أي جزء من MRZ
    """)
    
    st.markdown("---")
    st.caption("💻 PassportEye Engine")

# خيارات إدخال الصورة
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
    # عرض إرشادات الكاميرا
    create_camera_guide()
    
    # إطار الكاميرا
    st.markdown('<div class="camera-frame">', unsafe_allow_html=True)
    camera_image = st.camera_input("📸 التقط صورة واضحة لجواز السفر")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if camera_image is not None:
        uploaded_file = camera_image
        st.success("✅ تم التقاط الصورة!")

# معالجة الصورة
if uploaded_file is not None:
    
    # عرض الصورة
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 الصورة المُدخلة")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
        # زر المعالجة
        process_button = st.button("🔍 استخراج البيانات الآن", type="primary", use_container_width=True)
    
    with col2:
        if process_button:
            with st.spinner("⏳ جاري معالجة الصورة وقراءة البيانات..."):
                try:
                    # إعادة فتح الملف للقراءة
                    uploaded_file.seek(0)
                    mrz = read_mrz(uploaded_file)
                    
                    if mrz is None:
                        st.error("❌ لم يتم العثور على منطقة MRZ في الصورة!")
                        st.warning("""
                        **يرجى التأكد من:**
                        - الصورة واضحة وذات جودة عالية
                        - السطران السفليان (MRZ) ظاهران بالكامل
                        - لا توجد ظلال على منطقة MRZ
                        - الصورة غير مائلة
                        """)
                    else:
                        mrz_data = mrz.to_dict()
                        
                        # عرض درجة الدقة
                        valid_score = mrz_data.get('valid_score', 0)
                        
                        if valid_score >= 80:
                            emoji = "🎉"
                            status = "ممتازة"
                            color = "#28a745"
                        elif valid_score >= 50:
                            emoji = "👍"
                            status = "جيدة"
                            color = "#ffc107"
                        else:
                            emoji = "⚠️"
                            status = "ضعيفة"
                            color = "#dc3545"
                        
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
                        
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {str(e)}")
                    st.info("""
                    💡 **جرب:**
                    - التقاط صورة جديدة بإضاءة أفضل
                    - التأكد من استقرار الكاميرا
                    - استخدام صورة بدقة أعلى
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
        
        # البيانات الرئيسية في بطاقات كبيرة
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
        
        # البيانات التفصيلية
        st.markdown("---")
        with st.expander("📊 عرض جميع البيانات التفصيلية"):
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown("**أرقام التحقق:**")
                st.write(f"• رقم التحقق: `{mrz_data.get('check_number', 'N/A')}`")
                st.write(f"• تحقق تاريخ الميلاد: `{mrz_data.get('check_date_of_birth', 'N/A')}`")
                st.write(f"• تحقق تاريخ الانتهاء: `{mrz_data.get('check_expiration_date', 'N/A')}`")
                st.write(f"• التحقق المركب: `{mrz_data.get('check_composite', 'N/A')}`")
                st.write(f"• تحقق الرقم الشخصي: `{mrz_data.get('check_personal_number', 'N/A')}`")
            
            with detail_col2:
                st.markdown("**معلومات تقنية:**")
                st.write(f"• طريقة المعالجة: `{mrz_data.get('method', 'N/A')}`")
                st.write(f"• الرقم الشخصي: `{mrz_data.get('personal_number', 'N/A')}`")
                st.write(f"• اسم الملف: `{mrz_data.get('filename', 'N/A')}`")
            
            st.markdown("---")
            st.json(mrz_data)
        
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
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # خطوات الاستخدام
        st.markdown("""
        ### 📝 كيفية الاستخدام:
        
        1. **اختر مصدر الصورة** 📸
           - رفع من المعرض
           - التقاط من الكاميرا (مع إطار إرشادي)
        
        2. **تأكد من وضوح MRZ** 🔍
           - السطران السفليان يجب أن يكونا واضحين
           - بدون ظلال أو انعكاسات
        
        3. **اضغط على زر الاستخراج** ⚡
           - سيتم معالجة الصورة تلقائياً
           - ستظهر النتائج بشكل منسق
        
        4. **احفظ البيانات** 💾
           - حمّل بصيغة JSON أو TXT
        """)

# تذييل
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 20px;'>
    <p>💻 تم التطوير باستخدام Streamlit و PassportEye</p>
    <p>🔒 جميع البيانات تتم معالجتها محلياً - لا يتم حفظ أي معلومات</p>
    <p style='font-size: 12px; margin-top: 10px;'>© 2024 MRZ Reader - All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
