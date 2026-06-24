import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="MOF Methane Analysis", layout="wide", page_icon="🔬")
st.title("🔬 ARC-MOF Methane Analysis Dashboard (Real Data)")

@st.cache_data
def load_and_merge_data():
    # 1. โหลดข้อมูลทั้ง 3 ไฟล์
    df_geo = pd.read_csv("geometric_properties.csv")
    df_methane = pd.read_csv("methane.csv")
    df_charges = pd.read_csv("extracted_charges.csv") # 🌟 ไฟล์ประจุของจริง!
    
    # 2. ทำความสะอาดชื่อคอลัมน์
    df_geo.columns = df_geo.columns.str.strip()
    df_methane.columns = df_methane.columns.str.strip()
    df_charges.columns = df_charges.columns.str.strip()
    
    # 3. ตัดนามสกุลไฟล์ทิ้งเพื่อให้เชื่อมกันได้เป๊ะๆ
    def clean_filename(fname):
        return str(fname).split('.')[0].strip()

    df_geo['filename'] = df_geo['filename'].apply(clean_filename)
    df_methane['filename'] = df_methane['filename'].apply(clean_filename)
    df_charges['filename'] = df_charges['filename'].apply(clean_filename)
    
    # 4. ลบข้อมูลซ้ำซ้อนทิ้ง
    df_geo = df_geo.drop_duplicates(subset=['filename'], keep='first')
    df_methane = df_methane.drop_duplicates(subset=['filename'], keep='first')
    df_charges = df_charges.drop_duplicates(subset=['filename'], keep='first')
    
    # 5. ประกอบร่าง (Merge) 3 ตารางเข้าด้วยกัน
    df = pd.merge(df_geo, df_methane, on='filename', how='inner')
    df = pd.merge(df, df_charges, on='filename', how='inner') # นำประจุมาเชื่อม
    
    return df

try:
    with st.spinner("กำลังประกอบร่างข้อมูลวิทยาศาสตร์ของจริง..."):
        df = load_and_merge_data()
    
    st.success(f"✅ เชื่อมตารางสำเร็จ! พบข้อมูลพร้อมวิเคราะห์ {len(df)} โครงสร้าง")
    
    # 🧠 คำนวณ EGI ด้วยข้อมูลจริง (เลิกใช้ Random แล้ว!)
    denominator = np.abs(df['Df'] - 3.8)
    denominator = np.where(denominator < 0.01, 0.01, denominator)
    df['EGI_Score'] = df['Max_Metal_Charge'] / denominator

    # 📊 พล็อตกราฟ 2D Phase Diagram
    st.subheader("🎯 2D Phase Diagram: Real Van der Waals vs Electrostatic")
    fig = px.scatter(
        df, 
        x='Df', 
        y='Max_Metal_Charge', 
        color='EGI_Score',
        size='mmol/g', 
        hover_data=['filename', 'UC_volume', 'Di'],
        title="Synergy between Pore Size (Df) and Metal Charge",
        color_continuous_scale='Turbo', 
        opacity=0.7,
        height=600
    )
    # ตีเส้นสีแดงที่ Methane Kinetic Diameter
    fig.add_vline(x=3.8, line_dash="dash", line_color="red", annotation_text="CH4 (3.8Å)")
    st.plotly_chart(fig, use_container_width=True)

    # 🏆 แสดงตาราง Top MOFs
    st.subheader("🏆 Top MOFs for Methane Storage")
    # โชว์คอลัมน์ประจุจริงให้เห็นชัดๆ
    cols_to_show = ['filename', 'Df', 'Max_Metal_Charge', 'mmol/g', 'EGI_Score']
    st.dataframe(df.nlargest(10, 'mmol/g')[cols_to_show], use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")
    st.info("ตรวจสอบว่าไฟล์ extracted_charges.csv อยู่ในโฟลเดอร์เดียวกันแล้วนะครับ")