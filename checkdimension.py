import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="MOF Methane Analysis", layout="wide", page_icon="🔬")
st.title("🔬 ARC-MOF Methane Analysis Dashboard")

@st.cache_data # เพิ่ม Cache ให้โหลดข้อมูลครั้งเดียวไม่ต้องโหลดซ้ำ
def load_and_merge_data():
    # 1. โหลดข้อมูล
    df_geo = pd.read_csv("geometric_properties.csv")
    df_methane = pd.read_csv("methane.csv")
    
    # 2. ทำความสะอาดชื่อคอลัมน์
    df_geo.columns = df_geo.columns.str.strip()
    df_methane.columns = df_methane.columns.str.strip()
    
    # 3. ฟังก์ชันลบตัวเลขหรือนามสกุลไฟล์ทิ้ง (ใช้แค่ชื่อ MOF หลัก)
    def clean_filename(fname):
        return str(fname).split('.')[0].strip()

    df_geo['filename'] = df_geo['filename'].apply(clean_filename)
    df_methane['filename'] = df_methane['filename'].apply(clean_filename)
    
    # 4. สำคัญมาก: ลบแถวที่ filename ซ้ำออกก่อน Merge (เลือกเก็บตัวแรกไว้)
    df_geo = df_geo.drop_duplicates(subset=['filename'], keep='first')
    df_methane = df_methane.drop_duplicates(subset=['filename'], keep='first')
    
    # 5. เชื่อมตาราง
    df = pd.merge(df_geo, df_methane, on='filename', how='inner')
    return df

try:
    with st.spinner("กำลังประมวลผลข้อมูลมหาศาล..."):
        df = load_and_merge_data()
    
    st.success(f"✅ เชื่อมตารางสำเร็จ! ตอนนี้เหลือข้อมูลสะอาด {len(df)} แถว")
    
    # คำนวณ EGI (Placeholder ประจุ)
    np.random.seed(42)
    df['Max_Metal_Charge'] = np.random.uniform(1.0, 3.0, size=len(df))
    denominator = np.abs(df['Df'] - 3.8)
    denominator = np.where(denominator < 0.01, 0.01, denominator)
    df['EGI_Score'] = df['Max_Metal_Charge'] / denominator

    # กราฟ
    st.subheader("🎯 2D Phase Diagram")
    fig = px.scatter(
        df, x='Df', y='Max_Metal_Charge', color='EGI_Score',
        size='mmol/g', hover_data=['filename', 'UC_volume', 'Di'],
        title="Synergy between Pore Size (Df) and Metal Charge",
        color_continuous_scale='Turbo', opacity=0.6
    )
    fig.add_vline(x=3.8, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

    # ตาราง
    st.subheader("🏆 Top MOFs for Methane Storage")
    st.dataframe(df.nlargest(10, 'mmol/g')[['filename', 'Df', 'mmol/g', 'EGI_Score']], use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")