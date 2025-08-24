# حساب استهلاكات السواقط (Streamlit)

تطبيق ويب بـ **Streamlit** يحاكي منطق الـ VBA لحساب وتوزيع استهلاك الغاز على شهور الفترة (بدون حد أقصى لعدد الشهور)،
مع نفس قواعد الأسعار والدمغة والرسوم الشهرية، وإظهار **الكمية المستهدفة** و**القيمة المستهدفة**.

## تشغيل محليًا
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## نشر على Streamlit Cloud
- ارفع الريبو على GitHub.
- من Streamlit Community Cloud، اعمل New app واختَر `app/streamlit_app.py` كملف أساسي.
- لو فيه أسرار/مفاتيح، استخدم **App Settings → Secrets**.

## هيكل المشروع
```
app/streamlit_app.py     # واجهة المستخدم
src/swaqat/core.py       # منطق الحساب والتوزيع
requirements.txt
.streamlit/config.toml
.gitignore
README.md
```
