import streamlit as st
from passporteye import read_mrz
from PIL import Image
import json
import io

# إعدادات الصفحة
st.set_page_config(
    page_title="قارئ جوازات السفر - MRZ Reader",
    page_icon="🛂",
    layout="wide"
)

# CSS مخصص لتحسين المظهر
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .accuracy-high {
        color: #28a745;
        font-weight: bold;
    }
    .accuracy-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .accuracy-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.title("🛂 قارئ بيانات جواز السفر")
st.markdown("**قم برفع صورة جواز السفر لاستخراج البيانات تلقائياً**")

# شريط جانبي للمعلومات
with st.sidebar:
    st.header("ℹ️ معلومات")
    st.info("""
    هذا التطبيق يقرأ منطقة MRZ 
    (Machine Readable Zone) 
    من صور جوازات السفر
    
    **المتطلبات:**
    - صورة واضحة لجواز السفر
    - منطقة MRZ مرئية بوضوح
    """)
    
    st.header("📊 مقياس الدقة")
    st.success("✅ **عالية**: 80-100%")
    st.warning("⚠️ **متوسطة**: 50-79%")
    st.error("❌ **منخفضة**: أقل من 50%")
    
    st.markdown("---")
    st.caption("💻 PassportEye v2.2")

# خيارات إدخال الصورة
st.subheader("📸 اختر طريقة إدخال الصورة")

input_method = st.radio(
    "اختر المصدر:",
    ["📁 رفع من الاستوديو", "📷 التقاط من الكاميرا"],
    horizontal=True
)

uploaded_file = None

if input_method == "📁 رفع من الاستوديو":
    uploaded_file = st.file_uploader(
        "اختر صورة جواز السفر",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="الصيغ المدعومة: JPG, PNG, BMP"
    )
else:
    camera_image = st.camera_input("التقط صورة جواز السفر")
    if camera_image is not None:
        uploaded_file = camera_image

# معالجة الصورة
if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 الصورة المرفوعة")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
    
    with col2:
        st.subheader("📊 البيانات المستخرجة")
        
        # زر لمعالجة الصورة
        if st.button("🔍 استخراج البيانات", type="primary", use_container_width=True):
            with st.spinner("جاري معالجة الصورة..."):
                try:
                    # إعادة فتح الملف للقراءة
                    uploaded_file.seek(0)
                    mrz = read_mrz(uploaded_file)
                    
                    if mrz is None:
                        st.error("❌ لم يتم العثور على منطقة MRZ في الصورة!")
                        st.warning("تأكد من أن الصورة واضحة وتحتوي على منطقة MRZ كاملة")
                    else:
                        mrz_data = mrz.to_dict()
                        
                        st.success("✅ تم استخراج البيانات بنجاح!")
                        
                        # عرض درجة الدقة الإجمالية
                        st.markdown("---")
                        valid_score = mrz_data.get('valid_score', 0)
                        
                        # تحديد لون الدقة
                        if valid_score >= 80:
                            accuracy_class = "accuracy-high"
                            accuracy_emoji = "✅"
                            accuracy_text = "عالية"
                        elif valid_score >= 50:
                            accuracy_class = "accuracy-medium"
                            accuracy_emoji = "⚠️"
                            accuracy_text = "متوسطة"
                        else:
                            accuracy_class = "accuracy-low"
                            accuracy_emoji = "❌"
                            accuracy_text = "منخفضة"
                        
                        st.markdown(f"""
                        <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                            <h2>{accuracy_emoji} دقة الاستخراج</h2>
                            <h1 class='{accuracy_class}'>{valid_score}%</h1>
                            <p style='font-size: 18px;'>الدقة: <span class='{accuracy_class}'>{accuracy_text}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # معلومات تقنية
                        tech_col1, tech_col2, tech_col3 = st.columns(3)
                        with tech_col1:
                            st.metric("🔤 نوع MRZ", mrz_data.get('mrz_type', 'N/A'))
                        with tech_col2:
                            st.metric("⚙️ طريقة المعالجة", mrz_data.get('method', 'N/A'))
                        with tech_col3:
                            walltime = mrz_data.get('walltime', 0)
                            st.metric("⏱️ وقت المعالجة", f"{walltime:.2f}s")
                        
                        st.markdown("---")
                        
                        # البيانات الأساسية
                        st.subheader("📋 البيانات الشخصية")
                        info_col1, info_col2 = st.columns(2)
                        
                        with info_col1:
                            st.metric("🆔 نوع الوثيقة", mrz_data.get('type', 'غير متوفر'))
                            st.metric("🌍 الدولة المصدرة", mrz_data.get('country', 'غير متوفر'))
                            st.metric("📇 رقم الجواز", mrz_data.get('number', 'غير متوفر'))
                            st.metric("👤 الاسم الأول", mrz_data.get('names', 'غير متوفر'))
                            st.metric("👨‍👩‍👧‍👦 اسم العائلة", mrz_data.get('surname', 'غير متوفر'))
                        
                        with info_col2:
                            st.metric("🏳️ الجنسية", mrz_data.get('nationality', 'غير متوفر'))
                            st.metric("🎂 تاريخ الميلاد", mrz_data.get('date_of_birth', 'غير متوفر'))
                            st.metric("⚧️ الجنس", mrz_data.get('sex', 'غير متوفر'))
                            st.metric("📅 تاريخ الانتهاء", mrz_data.get('expiration_date', 'غير متوفر'))
                            st.metric("🔢 الرقم الشخصي", mrz_data.get('personal_number', 'غير متوفر'))
                        
                        # أرقام التحقق والصحة
                        st.markdown("---")
                        st.subheader("🔐 أرقام التحقق والصحة")
                        
                        check_col1, check_col2 = st.columns(2)
                        
                        with check_col1:
                            st.markdown("**أرقام التحقق:**")
                            st.write(f"• رقم التحقق: `{mrz_data.get('check_number', 'N/A')}`")
                            st.write(f"• تحقق تاريخ الميلاد: `{mrz_data.get('check_date_of_birth', 'N/A')}`")
                            st.write(f"• تحقق تاريخ الانتهاء: `{mrz_data.get('check_expiration_date', 'N/A')}`")
                            st.write(f"• التحقق المركب: `{mrz_data.get('check_composite', 'N/A')}`")
                            st.write(f"• تحقق الرقم الشخصي: `{mrz_data.get('check_personal_number', 'N/A')}`")
                        
                        with check_col2:
                            st.markdown("**حالة الصحة:**")
                            
                            def show_validity(label, is_valid):
                                icon = "✅" if is_valid else "❌"
                                color = "green" if is_valid else "red"
                                st.markdown(f"{icon} **{label}**: <span style='color: {color}'>{is_valid}</span>", unsafe_allow_html=True)
                            
                            show_validity("رقم الجواز صحيح", mrz_data.get('valid_number', False))
                            show_validity("تاريخ الميلاد صحيح", mrz_data.get('valid_date_of_birth', False))
                            show_validity("تاريخ الانتهاء صحيح", mrz_data.get('valid_expiration_date', False))
                            show_validity("التحقق المركب صحيح", mrz_data.get('valid_composite', False))
                            show_validity("الرقم الشخصي صحيح", mrz_data.get('valid_personal_number', False))
                        
                        # عرض البيانات الكاملة
                        st.markdown("---")
                        st.subheader("📄 البيانات الكاملة (JSON)")
                        
                        with st.expander("عرض البيانات الكاملة"):
                            st.json(mrz_data)
                        
                        # أزرار التحميل
                        download_col1, download_col2 = st.columns(2)
                        
                        with download_col1:
                            json_string = json.dumps(mrz_data, ensure_ascii=False, indent=2)
                            st.download_button(
                                label="⬇️ تحميل البيانات (JSON)",
                                data=json_string,
                                file_name="passport_data.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        with download_col2:
                            # تحويل البيانات إلى نص منسق
                            text_data = f"""
بيانات جواز السفر
==================
دقة الاستخراج: {valid_score}%

البيانات الشخصية:
- نوع الوثيقة: {mrz_data.get('type', 'N/A')}
- الدولة المصدرة: {mrz_data.get('country', 'N/A')}
- رقم الجواز: {mrz_data.get('number', 'N/A')}
- الاسم: {mrz_data.get('names', 'N/A')} {mrz_data.get('surname', 'N/A')}
- الجنسية: {mrz_data.get('nationality', 'N/A')}
- تاريخ الميلاد: {mrz_data.get('date_of_birth', 'N/A')}
- الجنس: {mrz_data.get('sex', 'N/A')}
- تاريخ الانتهاء: {mrz_data.get('expiration_date', 'N/A')}

معلومات تقنية:
- نوع MRZ: {mrz_data.get('mrz_type', 'N/A')}
- وقت المعالجة: {walltime:.2f}s
                            """
                            st.download_button(
                                label="⬇️ تحميل البيانات (TXT)",
                                data=text_data,
                                file_name="passport_data.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء معالجة الصورة: {str(e)}")
                    st.info("💡 نصائح لحل المشكلة:")
                    st.write("""
                    - تأكد من وضوح الصورة
                    - تأكد من ظهور منطقة MRZ بالكامل
                    - جرب التقاط صورة جديدة بإضاءة أفضل
                    - تأكد من أن الصورة ليست مقلوبة أو مائلة
                    - تأكد من استقرار الكاميرا عند التقاط الصورة
                    """)
else:
    # رسالة توضيحية
    st.info("👆 ابدأ باختيار طريقة إدخال الصورة من الأعلى")
    
    # عرض مثال توضيحي
    st.markdown("---")
    st.subheader("📌 ملاحظات مهمة:")
    
    note_col1, note_col2 = st.columns(2)
    
    with note_col1:
        st.markdown("""
        **جودة الصورة:**
        - ✅ صورة واضحة وذات دقة جيدة
        - ✅ منطقة MRZ ظاهرة بوضوح
        - ✅ إضاءة جيدة بدون ظلال
        - ✅ التقاط مستقيم (بدون زاوية)
        """)
    
    with note_col2:
        st.markdown("""
        **نصائح للتصوير:**
        - 📸 استخدم خلفية داكنة
        - 📸 تجنب الانعكاسات
        - 📸 ثبت الكاميرا جيداً
        - 📸 اجعل MRZ في منتصف الصورة
        """)

# تذييل
st.markdown("---")
st.caption("💻 تم التطوير باستخدام Streamlit و PassportEye | جميع البيانات تتم معالجتها محلياً ولا يتم حفظها")