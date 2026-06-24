import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="MOF Methane Analysis", layout="wide", page_icon="🔬")

st.title("🔬 ARC-MOF Methane Analysis Dashboard")

# 1. โหลดและทำความสะอาดไฟล์
try:
    df_geo = pd.read_csv("geometric_properties.csv")
    df_methane = pd.read_csv("methane.csv")
    
    # ทำความสะอาดชื่อคอลัมน์ (ลบช่องว่าง)
    df_geo.columns = df_geo.columns.str.strip()
    df_methane.columns = df_methane.columns.str.strip()
    
    # ฟังก์ชันตัดนามสกุลไฟล์ออก (ถ้ามี)
    def clean_filename(fname):
        return str(fname).split('.')[0].strip()

    df_geo['filename'] = df_geo['filename'].apply(clean_filename)
    df_methane['filename'] = df_methane['filename'].apply(clean_filename)
    
    # เชื่อมตาราง
    df = pd.merge(df_geo, df_methane, on='filename', how='inner')
    
    if len(df) == 0:
        st.error("❌ เชื่อมตารางไม่ได้! ข้อมูลไม่มีส่วนที่ทับซ้อนกันเลย")
    else:
        st.success(f"✅ โหลดและเชื่อมตารางสำเร็จ! พบข้อมูล {len(df)} แถว")
        
        # 2. คำนวณ EGI (ใช้ค่าสุ่มแทนไปก่อน)
        np.random.seed(42)
        df['Max_Metal_Charge'] = np.random.uniform(1.0, 3.0, size=len(df))
        
        # ป้องกัน division by zero
        denominator = np.abs(df['Df'] - 3.8)
        denominator = np.where(denominator < 0.01, 0.01, denominator)
        df['EGI_Score'] = df['Max_Metal_Charge'] / denominator

        # 3. กราฟ 2D Phase Diagram
        st.subheader("🎯 2D Phase Diagram: Van der Waals vs Electrostatic")
        fig = px.scatter(
            df, 
            x='Df', 
            y='Max_Metal_Charge', 
            color='EGI_Score',
            size='mmol/g',
            hover_data=['filename', 'UC_volume', 'Di'],
            title="Synergy between Pore Size (Df) and Metal Charge",
            color_continuous_scale='Turbo',
            opacity=0.6
        )
        fig.add_vline(x=3.8, line_dash="dash", line_color="red", annotation_text="CH4 (3.8Å)")
        st.plotly_chart(fig, use_container_width=True)

        # 4. ตารางคัดกรอง
        st.subheader("🏆 Top MOFs for Methane Storage")
        top_mofs = df.nlargest(10, 'mmol/g')
        st.dataframe(top_mofs[['filename', 'Df', 'mmol/g', 'EGI_Score', 'UC_volume']], use_container_width=True)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการรันระบบ: {e}")
    st.info("ตรวจสอบว่าไฟล์ geometric_properties.csv และ methane.csv อยู่ในโฟลเดอร์เดียวกับสคริปต์")