import sqlite3
import pandas as pd
import streamlit as st
from datetime import date
import base64
from pathlib import Path

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="نظام رحلة المخطوط", layout="wide")
DB = "manuscripts.db"

# =====================
# LOGO (Base64)
# =====================
def img_to_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

LOGO_B64 = img_to_base64("logo.png")

# =====================
# CSS
# =====================
# CSS – مطابق لواجهة الأنظمة الحكومية
# =====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

html, body, .stApp {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', sans-serif;
    background-color: #F5F6F8;
    color: #111827;
}

/* ===== Header ===== */
.header {
    background-color: #FFFFFF;
    padding: 24px 32px;
    border-radius: 12px;
    border-bottom: 2px solid #E5E7EB;
    margin-bottom: 20px;
}

/* نخلي ترتيب العناصر يسار → يمين */
.header-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    direction: ltr;
}

/* اللوجو يسار ونازل شوي */
.header-logo img {
    width: 120px;
    margin-top: 10px;
}

/* النص يرجع RTL */
.header-text {
    direction: rtl;
    text-align: right;
}

.header-text h1 {
    color: #374151;
    margin: 0;
}
.header-text p {
    color: #6B7280;
    margin-top: 6px;
}

/* باقي الستايل */
h2, h3 { color: #374151; font-weight: 700; margin-top: 10px; }
label { color: #111827 !important; font-weight: 700 !important; }

input, textarea {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
}
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
}

button {
    background-color: #2563EB !important;
    color: white !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
}

.kpi {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.kpi h4 { color: #6B7280; margin-bottom: 6px; }
.kpi h2 { color: #111827; margin: 0; }

.stDataFrame {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

# =====================
# HEADER (Logo inside white header)
# =====================
st.markdown(f"""
<div class="header">
  <div class="header-flex">
    <div class="header-logo">
      <img src="data:image/png;base64,{LOGO_B64}">
    </div>
    <div class="header-text">
      <h1>نظام تتبع رحلة المخطوط</h1>
      <p>مجمع الملك عبدالعزيز للمكتبات الوقفية</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# =====================
# DB HELPERS
# =====================
@st.cache_resource
def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

conn = get_conn()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS manuscripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manuscript_no TEXT NOT NULL UNIQUE,
    title TEXT,
    stage TEXT,
    department TEXT,
    assignee TEXT,
    entered_stage_date TEXT,
    sla_days INTEGER DEFAULT 0
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_stage ON manuscripts(stage)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_department ON manuscripts(department)")
conn.commit()


def fetch_df():
    return pd.read_sql("SELECT * FROM manuscripts ORDER BY id ASC", conn)


def add_row(manuscript_no, title, stage, department, assignee, entered_stage_date, sla_days):
    cur.execute("""
        INSERT INTO manuscripts
        (manuscript_no, title, stage, department, assignee, entered_stage_date, sla_days)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (manuscript_no.strip(), title.strip(), stage, department, assignee.strip(), str(entered_stage_date), int(sla_days)))
    conn.commit()


def update_row(row_id, manuscript_no, title, stage, department, assignee, entered_stage_date, sla_days):
    cur.execute("""
        UPDATE manuscripts
        SET manuscript_no=?, title=?, stage=?, department=?, assignee=?, entered_stage_date=?, sla_days=?
        WHERE id=?
    """, (manuscript_no.strip(), title.strip(), stage, department, assignee.strip(), str(entered_stage_date), int(sla_days), int(row_id)))
    conn.commit()


def delete_row(row_id):
    cur.execute("DELETE FROM manuscripts WHERE id=?", (int(row_id),))
    conn.commit()


STAGES = ["استلام", "فحص", "ترميم أو تعقيم", "رقمنة", "مراجعة جودة", "فهرسة"]
DEPTS  = ["مركز الترميم والتعقيم", "مركز الرقمنة والفهرسة", "الإتاحة"]

# =====================
# ADD FORM
# =====================
st.subheader("إدخال مخطوط جديد")

with st.form("add_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)

    with c1:
        manuscript_no = st.text_input("رقم المخطوط")
        stage = st.selectbox("المرحلة", STAGES, index=0)

    with c2:
        title = st.text_input("عنوان المخطوط")
        department = st.selectbox("الإدارة", DEPTS, index=0)

    with c3:
        assignee = st.text_input("المستلم")
        entered_stage_date = st.date_input("تاريخ دخول المرحلة", date.today())
        sla_days = st.number_input("SLA (أيام)", min_value=0, value=5, step=1)

    submitted = st.form_submit_button("حفظ")

    if submitted:
        if not manuscript_no.strip():
            st.error("رقم المخطوط إلزامي.")
        else:
            try:
                add_row(manuscript_no, title, stage, department, assignee, entered_stage_date, sla_days)
                st.success("تم حفظ المخطوط بنجاح")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("رقم المخطوط موجود مسبقًا. غيّر الرقم أو عدّل السجل من قسم (تعديل/حذف).")

# =====================
# DATA + CALCS
# =====================
df_raw = fetch_df()

if not df_raw.empty:
    df = df_raw.copy()
    df["entered_stage_date"] = pd.to_datetime(df["entered_stage_date"], errors="coerce")
    today_dt = pd.to_datetime(date.today())

    df["أيام في المرحلة"] = (today_dt - df["entered_stage_date"]).dt.days
    df["الأيام المتبقية"] = df["sla_days"].fillna(0).astype(int) - df["أيام في المرحلة"].fillna(0).astype(int)
    df["حالة الالتزام"] = df["الأيام المتبقية"].apply(lambda x: "متأخر" if x < 0 else "ضمن الوقت")

    df = df.rename(columns={
        "id": "المعرف",
        "manuscript_no": "رقم المخطوط",
        "title": "العنوان",
        "stage": "المرحلة",
        "assignee": "المستلم",
        "department": "الإدارة",
        "entered_stage_date": "تاريخ دخول المرحلة",
        "sla_days": "SLA (أيام)"
    })
else:
    df = pd.DataFrame()

# =====================
# FILTERS
# =====================
st.markdown("---")
st.subheader("بحث وتصفية")

f1, f2, f3, f4 = st.columns(4)

with f1:
    q_no = st.text_input("بحث برقم المخطوط", placeholder="مثال: 12345")
with f2:
    f_stage = st.multiselect("المرحلة", STAGES, default=[])
with f3:
    f_dept = st.multiselect("الإدارة", DEPTS, default=[])
with f4:
    f_status = st.multiselect("حالة الالتزام", ["ضمن الوقت", "متأخر"], default=[])

df_view = df.copy()
if not df_view.empty:
    if q_no.strip():
        df_view = df_view[df_view["رقم المخطوط"].astype(str).str.contains(q_no.strip(), na=False)]
    if f_stage:
        df_view = df_view[df_view["المرحلة"].isin(f_stage)]
    if f_dept:
        df_view = df_view[df_view["الإدارة"].isin(f_dept)]
    if f_status:
        df_view = df_view[df_view["حالة الالتزام"].isin(f_status)]

# =====================
# KPI
# =====================
st.markdown("---")
st.subheader("مؤشرات عامة")

total = 0 if df_view.empty else len(df_view)
within = 0 if df_view.empty else len(df_view[df_view["حالة الالتزام"] == "ضمن الوقت"])
late = 0 if df_view.empty else len(df_view[df_view["حالة الالتزام"] == "متأخر"])

k1, k2, k3 = st.columns(3)
k1.markdown(f"<div class='kpi'><h4>إجمالي</h4><h2>{total}</h2></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi'><h4>ضمن SLA</h4><h2>{within}</h2></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi'><h4>متأخر</h4><h2>{late}</h2></div>", unsafe_allow_html=True)

# =====================
# TABLE
# =====================
st.markdown("---")
st.subheader("قائمة المخطوطات")

TABLE_COLS = [
    "رقم المخطوط",
    "العنوان",
    "المرحلة",
    "المستلم",
    "الإدارة",
    "تاريخ دخول المرحلة",
    "SLA (أيام)",
    "أيام في المرحلة",
    "الأيام المتبقية",
    "حالة الالتزام",
    "المعرف"
]

if not df_view.empty:
    st.dataframe(df_view[TABLE_COLS], use_container_width=True, hide_index=True)
else:
    st.info("لا توجد بيانات مطابقة للتصفية الحالية.")

# =====================
# EDIT / DELETE
# =====================
st.markdown("---")
st.subheader("تعديل / حذف")

if df_raw.empty:
    st.info("لا يوجد سجلات للتعديل.")
else:
    # اختيار سجل
    options = df_raw[["id", "manuscript_no", "title"]].copy()
    options["label"] = options.apply(lambda r: f"{r['manuscript_no']} — {r['title'] or ''} (ID={r['id']})", axis=1)
    chosen = st.selectbox("اختر السجل", options["label"].tolist())

    chosen_id = int(options.loc[options["label"] == chosen, "id"].iloc[0])
    row = df_raw[df_raw["id"] == chosen_id].iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        e_no = st.text_input("رقم المخطوط (تعديل)", value=row["manuscript_no"] or "")
        e_stage = st.selectbox("المرحلة (تعديل)", STAGES, index=STAGES.index(row["stage"]) if row["stage"] in STAGES else 0)
    with c2:
        e_title = st.text_input("عنوان المخطوط (تعديل)", value=row["title"] or "")
        e_dept = st.selectbox("الإدارة (تعديل)", DEPTS, index=DEPTS.index(row["department"]) if row["department"] in DEPTS else 0)
    with c3:
        e_assignee = st.text_input("المستلم (تعديل)", value=row["assignee"] or "")
        e_date = st.date_input("تاريخ دخول المرحلة (تعديل)", value=pd.to_datetime(row["entered_stage_date"]).date() if row["entered_stage_date"] else date.today())
        e_sla = st.number_input("SLA (أيام) (تعديل)", min_value=0, value=int(row["sla_days"] or 0), step=1)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("حفظ التعديل"):
            if not e_no.strip():
                st.error("رقم المخطوط إلزامي.")
            else:
                try:
                    update_row(chosen_id, e_no, e_title, e_stage, e_dept, e_assignee, e_date, e_sla)
                    st.success("تم تحديث السجل.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("رقم المخطوط مستخدم بسجل آخر.")
    with b2:
        if st.button("حذف السجل"):
            delete_row(chosen_id)
            st.success("تم حذف السجل.")
            st.rerun()

# =====================
# REPORTS
# =====================
st.markdown("---")
st.subheader("التقارير")

if df_view.empty:
    st.info("لا توجد بيانات للرسم.")
else:
    st.write("حسب المرحلة")
    st.bar_chart(df_view.groupby("المرحلة").size())

    st.write("حسب الإدارة")
    st.bar_chart(df_view.groupby("الإدارة").size())

# =====================
# EXPORT
# =====================
st.markdown("---")
csv = df_view.drop(columns=["المعرف"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
st.download_button("تحميل التقرير", csv, "manuscripts_report.csv", "text/csv")
