# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import pandas as pd
import math
import numpy as np

# ثوابت مشابهة للكود
STEP_UNITS = 10  # تمثيل 0.1 كمضاعفات صحيحة
BOUNDS_MIN_FACTOR = 0.5
BOUNDS_MAX_FACTOR = 1.7

@dataclass
class Inputs:
    # تواريخ
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    # قراءات وبوالص
    B2_STOT: float
    C2_SPREV: float
    D2_SCUR: float
    E2_START_BAL: float
    F2_SDATE: pd.Timestamp  # للمطابقة فقط، قد لا نستخدمه مباشرة

    B3_ETOT: float
    C3_EPREV: float
    D3_ECUR: float
    E3_END_BAL: float
    F3_EDATE: pd.Timestamp

    topup1_net: float
    topup2_net: float

    p1: float
    p2: float
    p3: float
    stamp: float  # ثابت 0.036
    monthly_fee: float
    zero_tail: int  # F12

def tiers_from_p1(p1: float) -> Tuple[float, float]:
    p1r = round(p1, 2)
    mapping = {
        2.35: (3.1, 3.6),
        2.50: (3.25, 3.75),
        2.60: (3.35, 4.00),
        3.00: (4.00, 5.00),
        4.00: (5.00, 7.00),
    }
    if p1r in mapping:
        return mapping[p1r]
    p2 = p1 + 0.75
    p3 = p2 + 0.5
    return (p2, p3)

def price_no_fee(q: float, p1: float, p2: float, p3: float, stamp: float) -> float:
    """حساب قيمة الاستهلاك بدون الرسوم الشهرية (يشمل الدمغة لكل م3)."""
    t1 = p1 + stamp
    t2 = p2 + stamp
    t3 = p3 + stamp
    if q <= 30.0:
        v = q * t1
    elif q <= 60.0:
        v = 30.0 * t1 + (q - 30.0) * t2
    else:
        v = 30.0 * t1 + 30.0 * t2 + (q - 60.0) * t3
    return v

def months_between(start_date: pd.Timestamp, end_date: pd.Timestamp) -> List[pd.Timestamp]:
    # نفس BuildMonths (من الشهر الأول لقبل شهر نهاية الفترة)
    sMon = pd.Timestamp(year=start_date.year, month=start_date.month, day=1)
    eMon = pd.Timestamp(year=end_date.year, month=end_date.month, day=1)
    ePrev = (eMon - pd.offsets.MonthBegin(1))
    # في VBA: DateDiff("m", sMon, ePrev) + 1
    months = []
    cur = sMon
    # احسب عدد الشهور
    count = (ePrev.year - sMon.year) * 12 + (ePrev.month - sMon.month) + 1
    count = max(1, min(count, 12))
    for i in range(count):
        months.append(cur)
        cur = cur + pd.offsets.MonthBegin(1)
    return months

def to_units(q: float) -> int:
    return int(round(q * STEP_UNITS))

def from_units(u: int) -> float:
    return u / STEP_UNITS

@dataclass
class DistributionResult:
    table: pd.DataFrame  # Month, Quantity(m3), Value(EGP)
    q_target: float
    v_target: float
    checks: Dict[str, float]

def distribute(inputs: Inputs) -> DistributionResult:
    # ضبط شرائح الأسعار
    p2_calc, p3_calc = tiers_from_p1(inputs.p1)
    p2 = inputs.p2 if inputs.p2 > 0 else p2_calc
    p3 = inputs.p3 if inputs.p3 > 0 else p3_calc

    # حساب رؤوس القيم (مطابقة VBA)
    F6 = round(inputs.E2_START_BAL + inputs.topup1_net + inputs.topup2_net, 3)  # H_BAL_START
    F10 = price_no_fee(inputs.D2_SCUR, inputs.p1, p2, p3, inputs.stamp)         # H_D2_VAL
    F11 = price_no_fee(inputs.D3_ECUR, inputs.p1, p2, p3, inputs.stamp)         # H_D3_VAL

    # الكمية المستهدفة (F8)
    q_target = inputs.B3_ETOT - inputs.D3_ECUR - inputs.B2_STOT + inputs.D2_SCUR
    q_target = max(0.0, round(q_target, 1))

    # القيمة المستهدفة (F9): (F6 + F10) - (E3 + F11)
    v_target = (F6 + F10) - (inputs.E3_END_BAL + F11)
    v_target = max(0.0, round(v_target, 3))

    months = months_between(inputs.start_date, inputs.end_date)
    m = len(months)
    if m == 0:
        return DistributionResult(pd.DataFrame(columns=["Month","Quantity(m3)","Value(EGP)"]), q_target, v_target, {})

    # قيود الحدود الدنيا/العليا
    d2 = inputs.D2_SCUR
    c3 = inputs.C3_EPREV

    minU = [0]*m
    maxU = [0]*m
    fixed = [False]*m
    qU = [0]*m

    for idx in range(m):
        if idx == 0:
            mn = max(d2, c3 * BOUNDS_MIN_FACTOR)
            mx = max(mn, c3 * BOUNDS_MAX_FACTOR)
        elif idx == m - 1:
            mn = c3
            mx = c3
            fixed[idx] = True
            qU[idx] = to_units(c3)
        else:
            mn = c3 * BOUNDS_MIN_FACTOR
            mx = max(mn, c3 * BOUNDS_MAX_FACTOR)
        mn = max(0.0, mn)
        minU[idx] = to_units(mn)
        maxU[idx] = to_units(mx)

    # Zero tail قبل آخر شهر
    zero_tail = int(max(0, min(inputs.zero_tail, m-1)))
    if zero_tail > 0:
        for idx in range(m - zero_tail - 1, m - 1):
            minU[idx] = 0
            maxU[idx] = 0
            qU[idx] = 0
            fixed[idx] = True

    totalU = to_units(q_target)
    sumMin = sum(minU)
    if sumMin > totalU and sumMin > 0:
        scale = totalU / sumMin if sumMin else 1
        for i in range(m):
            if not fixed[i]:
                minU[i] = int(math.floor(minU[i] * scale))
                if minU[i] > maxU[i]:
                    minU[i] = maxU[i]

    # بداية: خذ الحد الأدنى ثم وزّع الباقي وفقًا للسعات
    qU = minU[:]
    capacity = [max(0, maxU[i] - qU[i]) for i in range(m)]
    left = totalU - sum(qU)
    if left > 0:
        weights = []
        for i in range(m):
            cap = capacity[i]
            # وزن بسيط مع بعض التفاوت
            wt = cap * (1.0 + 0.12 * math.cos((i) * math.pi / 3.0))
            wt = max(0.0, wt)
            weights.append(wt)
        s = sum(weights)
        if s > 0:
            assigned = [0]*m
            for i in range(m):
                assigned[i] = int(math.floor(left * (weights[i]/s)))
                qU[i] = min(maxU[i], qU[i] + assigned[i])
            # وزّع المتبقي واحدًا واحدًا
            remain = totalU - sum(qU)
            j = 0
            while remain > 0 and j < 100000:
                idx = j % m
                if qU[idx] < maxU[idx] and not fixed[idx]:
                    qU[idx] += 1
                    remain -= 1
                j += 1

    # بناء جدول الأسعار بدون رسوم شهرية
    def price_tbl_value(u: int) -> int:
        val = price_no_fee(from_units(u), inputs.p1, p2, p3, inputs.stamp)
        return int(round(val * 1000))

    vM_noFee = [price_tbl_value(u) for u in qU]

    # الهدف بدون الرسوم الشهرية
    feeM = int(round(inputs.monthly_fee * 1000))
    targetTotalM = int(round(v_target * 1000))
    targetNoFeeM = max(0, targetTotalM - feeM * m)

    # تحسين بسيط عشوائي + محاولة اقتراب بالدوال التفاضلية
    import random
    def try_move(i: int, j: int):
        nonlocal qU, vM_noFee
        if i == j: return False
        if qU[i] + 1 > maxU[i]: return False
        if qU[j] - 1 < minU[j]: return False
        before = vM_noFee[i] + vM_noFee[j]
        after = price_tbl_value(qU[i]+1) + price_tbl_value(qU[j]-1)
        cur = sum(vM_noFee)
        need = targetNoFeeM - cur
        delta = after - before
        if abs(need - delta) < abs(need):
            qU[i] += 1
            qU[j] -= 1
            vM_noFee[i] = price_tbl_value(qU[i])
            vM_noFee[j] = price_tbl_value(qU[j])
            return True
        return False

    for _ in range(4000):
        cur = sum(vM_noFee)
        need = targetNoFeeM - cur
        if need == 0:
            break
        i = random.randrange(m)
        j = random.randrange(m)
        try_move(i, j)

    # إجبار التطابق بالعَدد (تصحيح عتبي)
    # أضف/اطرح 1 وحدة (0.1 م3) من/إلى أشهر ممكنة حتى الوصول لأقرب مجموع
    def greedy_adjust(max_steps=5000):
        nonlocal qU, vM_noFee
        steps = 0
        while steps < max_steps:
            cur = sum(vM_noFee)
            need = targetNoFeeM - cur
            if need == 0:
                break
            improve = False
            # جرب كل الأزواج الصغيرة
            for i in range(m):
                if improve: break
                for j in range(m):
                    if i == j: continue
                    if qU[i] + 1 <= maxU[i] and qU[j] - 1 >= minU[j]:
                        before = vM_noFee[i] + vM_noFee[j]
                        after = price_tbl_value(qU[i]+1) + price_tbl_value(qU[j]-1)
                        delta = after - before
                        if abs(need - delta) < abs(need):
                            qU[i] += 1; qU[j] -= 1
                            vM_noFee[i] = price_tbl_value(qU[i])
                            vM_noFee[j] = price_tbl_value(qU[j])
                            improve = True
                            break
            if not improve:
                break
            steps += 1

    greedy_adjust()

    # حساب القيمة المعروضة بإضافة الرسوم الشهرية لكل شهر
    vDispM = [vM_noFee[i] + feeM for i in range(m)]
    sM = sum(vDispM)
    diffM = targetTotalM - sM
    # وزّع فرق المللي بالتساوي من اليمين لليسار كما في VBA
    i = m - 1
    while diffM != 0 and m > 0:
        vDispM[i] += 1 if diffM > 0 else -1
        diffM += -1 if diffM > 0 else 1
        i = (i - 1) % m

    quantities = [from_units(u) for u in qU]
    values = [v/1000.0 for v in vDispM]
    df = pd.DataFrame({
        "Month": [pd.Timestamp(x).strftime("%m/%Y") for x in months],
        "Quantity(m3)": [round(q, 1) for q in quantities],
        "ValueNoFee(EGP)": [round(v/1000.0, 3) for v in vM_noFee],
        "MonthlyFee(EGP)": [round(inputs.monthly_fee, 3)]*m,
        "Value(EGP)": [round(v, 3) for v in values],
    })

    checks = {
        "q_target": q_target,
        "q_sum": round(sum(quantities), 1),
        "v_target": v_target,
        "v_sum": round(sum(values), 3),
    }
    return DistributionResult(df, q_target, v_target, checks)
