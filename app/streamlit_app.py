# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from src.swaqat.core import Inputs, distribute, tiers_from_p1

st.set_page_config(page_title="حساب استهلاكات السواقط", layout="wide")

# ----------- CSS تحسينات زر احسب وتنسيقات عامة -----------
st.markdown("""
<style>
/* حاوية الكروت العلوية */
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
.target-card{background:#0F766E;color:#fff;padding:14px;border-radius:14px;text-align:center;font-weight:700}
.target-card.blue{background:#0E7490}
/* زر احسب */
.stButton>button {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color:#fff; font-size:20px; font-weight:800; padding:14px 24px;
  border-radius:14px; border:0; box-shadow:0 6px 16px rgba(16,185,129,.35);
}
.stButton>button:hover {filter:brightness(1.05)}
/* تصغير حقول الإدخال المجمعة */
.compact .stNumberInput input, .compact .stTextInput input {height:34px; padding:4px 8px; font-size:14px}
.compact label {font-size:13px}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>حساب استهلاكات السواقط</h2>", unsafe_allow_html=True)

# ----------- الكمية المستهدفة والقيمة المستهدفة جنب بعض -----------
col_t1, col_t2 = st.columns(2)
target_q_placeholder = col_t1.empty()
target_v_placeholder = col_t2.empty()

st.write("")

# ----------- تقسيم الشاشة: المعطيات (يمين) والمخرجات (يسار) -----------
col_outputs, col_inputs = st.columns([1.1, 1.2])  # outputs يسار، inputs يمين

with col_inputs:
    st.markdown("### **المعطيات**")
    right, left = st.columns(2)  # يمين/يسار داخل المعطيات
    with right:
        st.markdown("#### بداية الفترة")
        sdate = st.date_input("تاريخ قراءة بداية الفترة", datetime.today().replace(day=1))
        b2 = st.text_input("الاستهلاك الكلي (بداية)", value="", placeholder="")
        c2 = st.text_input("استهلاك الشهر السابق (بداية)", value="", placeholder="")
        d2 = st.text_input("الاستهلاك الحالي (بداية)", value="", placeholder="")
        e2 = st.text_input("الرصيد الحالي (بداية)", value="", placeholder="")
        c7 = st.text_input("قيمة الشحنة (الأولى)", value="", placeholder="")
        p1_options = [2.35, 2.50, 2.60, 3.00, 4.00]
        p1 = st.selectbox("سعر الشريحة (الأولى)", p1_options, index=1)
    with left:
        st.markdown("#### نهاية الفترة")
        edate = st.date_input("تاريخ قراءة نهاية الفترة", datetime.today())
        b3 = st.text_input("الاستهلاك الكلي (نهاية)", value="", placeholder="")
        c3 = st.text_input("استهلاك الشهر السابق (نهاية)", value="", placeholder="")
        d3 = st.text_input("الاستهلاك الحالي (نهاية)", value="", placeholder="")
        e3 = st.text_input("الرصيد الحالي (نهاية)", value="", placeholder="")
        c8 = st.text_input("قيمة الشحنة (الثانية)", value="", placeholder="")
        p2_calc, p3_calc = tiers_from_p1(p1)
        st.caption(f"سعر الشريحة الثانية: {p2_calc:.2f} — سعر الشريحة الثالثة: {p3_calc:.2f}")

    # صف صغير في نص المعطيات: الرسوم/الدمغة/عدد الشهور بدون استهلاك جنب بعض
    st.markdown("")
    cc1, cc2, cc3 = st.columns(3, gap="small")
    with st.container():
        with cc1:
            monthly_fee_option = st.selectbox("الرسوم الشهرية", options=[6.20, 7.10, 12.0, 13.68, 17.5, 19.5, 0.0, "حر"], index=0)
        with cc2:
            stamp = 0.036
            st.number_input("دمغة الاستهلاك (ثابتة)", value=stamp, step=0.001, format="%.3f", disabled=True)
        with cc3:
            zero_tail_text = st.text_input("عدد الشهور بدون استهلاك", value="", placeholder="")

    # تحويل الرسوم الشهرية لو "حر"
    if monthly_fee_option == "حر":
        monthly_fee = st.text_input("رسوم شهرية مخصصة", value="", placeholder="")
    else:
        monthly_fee = str(monthly_fee_option)

    st.write("")
    go = st.button("احسب", use_container_width=True)

with col_outputs:
    st.markdown("### **المخرجات**")
    out_table_placeholder = st.empty()
    download_placeholder = st.empty()
    checks_placeholder = st.empty()

def to_float(x: str) -> float:
    x = (x or "").strip()
    if x == "": return 0.0
    x = x.replace("،", ".").replace(",", ".")
    try: return float(x)
    except: return 0.0

def to_int(x: str) -> int:
    try: return int(float(x))
    except: return 0

if go:
    inp = Inputs(
        start_date=pd.Timestamp(sdate),
        end_date=pd.Timestamp(edate),
        B2_STOT=to_float(b2),
        C2_SPREV=to_float(c2),
        D2_SCUR=to_float(d2),
        E2_START_BAL=to_float(e2),
        F2_SDATE=pd.Timestamp(sdate),

        B3_ETOT=to_float(b3),
        C3_EPREV=to_float(c3),
        D3_ECUR=to_float(d3),
        E3_END_BAL=to_float(e3),
        F3_EDATE=pd.Timestamp(edate),

        topup1_net=to_float(c7),
        topup2_net=to_float(c8),

        p1=p1, p2=0.0, p3=0.0,
        stamp=0.036,
        monthly_fee=to_float(monthly_fee),
        zero_tail=to_int(zero_tail_text)
    )
    res = distribute(inp)

    # بطاقات الهدف جنب بعض
    target_q_placeholder.markdown(
        f"<div class='target-card'><b>الكمية المستهدفة</b> (م³): {res.q_target:.1f}</div>", unsafe_allow_html=True
    )
    target_v_placeholder.markdown(
        f"<div class='target-card blue'><b>القيمة المستهدفة</b> (جنيه): {res.v_target:.3f}</div>", unsafe_allow_html=True
    )

    # تجهيز جدول بإضافة عمود مسلسل يبدأ من 1
    df = res.table.copy()
    df.insert(0, "Serial", range(1, len(df) + 1))

    # إجماليات
    total_row = {
        "Serial": "المجموع",
        "Month": "",
        "Quantity(m3)": round(df["Quantity(m3)"].sum(), 1),
        "Value+Stamp_noFee(EGP)": round(df["Value+Stamp_noFee(EGP)"].sum(), 3),
        "MonthlyFee(EGP)": round(df["MonthlyFee(EGP)"].sum(), 3),
        "Value(EGP)": round(df["Value(EGP)"].sum(), 3),
    }

    # عرض جدول بتنسيق HTML للتحكم في سطر المجموع والألوان
    def render_html_table(df: pd.DataFrame, total_row: dict) -> str:
        # رؤوس
        headers = ["مسلسل", "الشهر", "الكمية", "قيمة+دمغة بدون رسوم", "الرسوم الشهرية", "القيمة"]
        cols = ["Serial", "Month", "Quantity(m3)", "Value+Stamp_noFee(EGP)", "MonthlyFee(EGP)", "Value(EGP)"]

        # صفوف عادية
        rows_html = []
        for _, row in df.iterrows():
            rows_html.append(
                f"<tr>"
                f"<td style='text-align:center;width:80px'>{row['Serial']}</td>"
                f"<td style='text-align:center;width:120px'>{row['Month']}</td>"
                f"<td style='text-align:center;width:120px'>{row['Quantity(m3)']:.1f}</td>"
                f"<td style='text-align:center;width:160px'>{row['Value+Stamp_noFee(EGP)']:.3f}</td>"
                f"<td style='text-align:center;width:140px'>{row['MonthlyFee(EGP)']:.3f}</td>"
                f"<td style='text-align:center;width:160px'>{row['Value(EGP)']:.3f}</td>"
                f"</tr>"
            )
        # سطر المجموع
        total_html = (
            f"<tr style='background:#FFF59D;'>"
            f"<td style='text-align:center;font-weight:800;color:#B00000'>المجموع</td>"
            f"<td></td>"
            f"<td style='text-align:center;font-weight:800;color:#B00000'>{total_row['Quantity(m3)']:.1f}</td>"
            f"<td style='text-align:center;font-weight:800;color:#B00000'>{total_row['Value+Stamp_noFee(EGP)']:.3f}</td>"
            f"<td style='text-align:center;font-weight:800;color:#B00000'>{total_row['MonthlyFee(EGP)']:.3f}</td>"
            f"<td style='text-align:center;font-weight:800;color:#B00000'>{total_row['Value(EGP)']:.3f}</td>"
            f"</tr>"
        )

        html = ("<div style='overflow-x:auto;'>"
                "<table style='border-collapse:collapse;width:100%;'>"
                "<thead>"
                "<tr style='background:#FFE066;'>"
                + "".join([f"<th style='padding:8px;border:1px solid #ddd;text-align:center'>{h}</th>" for h in headers])
                + "</tr></thead><tbody>"
                + "".join(rows_html)
                + total_html +
                "</tbody></table></div>")
        return html

    out_table_placeholder.markdown(render_html_table(df, total_row), unsafe_allow_html=True)

    # تنزيلات
    xbuf_path = "/mnt/data/swaqat_result.xlsx"
    with pd.ExcelWriter(xbuf_path, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name="نتيجة التوزيع")
    csv_path = "/mnt/data/swaqat_result.csv"
    df.to_csv(csv_path, index=False)

    download_placeholder.download_button("تحميل النتيجة (Excel)", data=open(xbuf_path,"rb").read(), file_name="swaqat_result.xlsx")
    download_placeholder.download_button("تحميل النتيجة (CSV)", data=open(csv_path,"rb").read(), file_name="swaqat_result.csv")

    checks_placeholder.write({
        "مجموع الكميات": float(df["Quantity(m3)"].sum()),
        "مجموع قيمة بدون رسوم": float(df["Value+Stamp_noFee(EGP)"].sum()),
        "مجموع الرسوم الشهرية": float(df["MonthlyFee(EGP)"].sum()),
        "مجموع القيم النهائية": float(df["Value(EGP)"].sum()),
    })
else:
    target_q_placeholder.markdown("<div class='target-card'>الكمية المستهدفة (م³): —</div>", unsafe_allow_html=True)
    target_v_placeholder.markdown("<div class='target-card blue'>القيمة المستهدفة (جنيه): —</div>", unsafe_allow_html=True)
