import streamlit as st
import pandas as pd
from openai import OpenAI
from pyscf import gto, scf
from mp_api.client import MPRester
import py3Dmol
from stmol import showmol
import json

# ─── 1. ตั้งค่าหน้าเว็บ ───
st.set_page_config(page_title="Hybrid MOF Quantum", page_icon="✨", layout="wide")

# ─── 2. ระบบ Session State (ล็อกอิน) ───
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ─── 3. แถบควบคุมด้านข้าง (Sidebar: Theme & DB & Login) ───
st.sidebar.header("🎨 Appearance & Database")

# Theme Switcher
theme_choice = st.sidebar.selectbox("เลือกธีมหน้าเว็บ:", ["Dark (Premium)", "Light (Clean)", "Default (Streamlit)"])

# ปรับ CSS และสีพื้นหลัง 3D ตามธีมที่เลือก
bg_3d = "white"
if theme_choice == "Dark (Premium)":
    bg_3d = "#0b0f19"
    st.markdown("""
    <style>
        .stApp { background-color: #0b0f19; color: #e0e6ed; }
        .sparkle-title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #00f2fe, #4facfe, #00f2fe); background-size: 200% auto; color: #fff; background-clip: text; text-fill-color: transparent; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shine 3s linear infinite; }
        @keyframes shine { to { background-position: 200% center; } }
    </style>
    """, unsafe_allow_html=True)
elif theme_choice == "Light (Clean)":
    bg_3d = "#ffffff"
    st.markdown("""
    <style>
        .stApp { background-color: #ffffff; color: #1e1e1e; }
        .sparkle-title { font-size: 2.8rem; font-weight: 800; background: linear-gradient(90deg, #ff7e5f, #feb47b, #ff7e5f); background-size: 200% auto; color: #fff; background-clip: text; text-fill-color: transparent; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shine 3s linear infinite; }
        @keyframes shine { to { background-position: 200% center; } }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown('<style>.sparkle-title { font-size: 2.8rem; font-weight: 800; color: #1f77b4; }</style>', unsafe_allow_html=True)

selected_db = st.sidebar.selectbox(
    "🗄️ เลือกฐานข้อมูล:",
    ["Materials Project (Live API)", "CoRe MOF (Local DB)", "ARC-MOF (Local DB)"]
)
st.sidebar.divider()

# Login System
if not st.session_state.logged_in:
    st.sidebar.subheader("🔐 System Login")
    username_input = st.sidebar.text_input("👤 Username:", value="Tanat")
    api_key_input = st.sidebar.text_input("🔑 OpenAI API Key:", type="password")
    mp_key_input = st.sidebar.text_input("🔑 MP API Key:", type="password")
    
    if st.sidebar.button("🚀 Login & Connect"):
        st.session_state.username = username_input
        st.session_state.api_key = api_key_input
        st.session_state.mp_api_key = mp_key_input
        st.session_state.logged_in = True
        st.rerun()
else:
    st.sidebar.success(f"👋 Welcome, **{st.session_state.username}**!")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.api_key = ""
        st.session_state.mp_api_key = ""
        st.rerun()

st.sidebar.divider()

# ─── 4. ส่วนหัวของเว็บ (Header) ───
st.markdown('<div class="sparkle-title">✨ Ultimate Hybrid MOF Quantum Platform</div>', unsafe_allow_html=True)
st.caption("ระบบค้นหาอัจฉริยะ, เปรียบเทียบวัสดุ, เรนเดอร์ 3 มิติ และวิเคราะห์ด้วย AI")
st.divider()

# ─── ฟังก์ชันเสริม: แสดงโมเดล 3 มิติ ───
def render_3d_molecule(cif_string, bg_color):
    view = py3Dmol.view(width=350, height=300)
    view.addModel(cif_string, 'cif')
    view.setStyle({'stick': {'radius': 0.15}, 'sphere': {'scale': 0.25}})
    view.addUnitCell()
    view.zoomTo()
    view.setBackgroundColor(bg_color)
    showmol(view, height=300, width=350)

# ─── 5. โหมดการทำงาน (Modes) ───
source_mode = st.radio(
    "เลือกโหมดการทำงาน:",
    ["🤖 Gen AI Search (ค้นหาด้วยภาษาธรรมชาติ)", "🌐 Exact Match (เปรียบเทียบวัสดุ 3D)", "⚛️ Live Quantum (คำนวณสดในเครื่อง)"],
    horizontal=True
)

comparison_data = [] 
ai_summary_input = ""

# ==========================================
# 🌟 MODE 1: Gen AI Search (Text-to-Query) 🌟
# ==========================================
if "Gen AI Search" in source_mode:
    st.info("💡 บรรยายคุณสมบัติของวัสดุที่คุณต้องการ แล้ว AI จะแปลงเป็นเงื่อนไขค้นหาในฐานข้อมูลให้เอง")
    user_prompt = st.text_area("🔎 อธิบาย MOF ที่อยากได้:", "อยากได้ MOF ที่มีสังกะสี (Zn) เป็นองค์ประกอบ มีรูพรุนเยอะๆ พลังงานต่ำๆ เหมาะกับมีเทน")
    
    if st.button("✨ ให้ AI ค้นหาวัสดุ", type="primary"):
        if not st.session_state.get('api_key'):
            st.error("❌ กรุณา Login และใส่ OpenAI API Key เพื่อใช้งานสมองกลค้นหา")
        else:
            with st.spinner("🤖 AI กำลังตีความข้อความของคุณ..."):
                try:
                    client = OpenAI(api_key=st.session_state.api_key)
                    nlp_prompt = f"""
                    แปลงข้อความนี้: "{user_prompt}" 
                    ให้เป็น JSON conditions สำหรับค้นหาฐานข้อมูล (ห้ามตอบอย่างอื่นนอกจาก JSON) เช่น:
                    {{"elements": ["Zn"], "porosity_preference": "high", "energy": "low"}}
                    """
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": nlp_prompt}],
                        temperature=0.0
                    )
                    
                    search_params = response.choices[0].message.content
                    st.success("🎯 AI ตีความเงื่อนไขสำเร็จ!")
                    st.code(search_params, language="json")
                    
                    st.divider()
                    st.write(f"🗄️ **กำลังค้นหาในฐานข้อมูล: {selected_db} ...**")
                    
                    # จำลองการดึงฐานข้อมูลแบบ Local
                    if "Local DB" in selected_db:
                        st.warning(f"📥 (ระบบจำลอง) กำลังจำลองการดึงข้อมูลจากไฟล์ {selected_db}.csv ในเครื่องของคุณ...")
                        # สร้างตารางข้อมูลจำลองให้ดูเป็นตัวอย่าง
                        mock_df = pd.DataFrame({
                            "MOF_Name": ["Zn-MOF-74", "ZIF-8 (Zn)", "Zn-BTC"],
                            "Void_Fraction": [0.65, 0.49, 0.55],
                            "Surface_Area_m2g": [3200, 1500, 2100],
                            "Suitability_CH4": ["High", "Medium", "High"]
                        })
                        st.dataframe(mock_df, use_container_width=True)
                        st.success(f"✅ สมมติว่าพบข้อมูลที่ตรงเงื่อนไข 3 ตัวจาก {selected_db}!")
                    else:
                        st.info("🌐 สำหรับโหมด Materials Project API กรุณาใช้โหมด Exact Match ด้านบนเพื่อดึงข้อมูลจริงครับ")
                        
                except Exception as e:
                    st.error(f"ระบบ AI ขัดข้อง: {e}")

# ==========================================
# 🌟 MODE 2: Exact Match (API + 3D Viewer) 🌟
# ==========================================
elif "Exact Match" in source_mode:
    user_input = st.text_input("🔎 พิมพ์ชื่อวัสดุ (ค้นหาหลายตัวให้คั่นด้วยลูกน้ำ) เช่น: MOF-5, UiO-66, HKUST-1", "MOF-5, HKUST-1")
    
    if st.button("⚡ ดึงข้อมูลเปรียบเทียบ", type="primary"):
        if not st.session_state.get('mp_api_key') or not st.session_state.get('api_key'):
            st.error("❌ กรุณา Login และใส่ API Key ให้ครบทั้ง 2 ช่องครับ")
        else:
            with st.spinner("🤖 AI Agent กำลังวิเคราะห์รหัสวัสดุ..."):
                try:
                    client = OpenAI(api_key=st.session_state.api_key)
                    agent_prompt = f'แปลงชื่อ "{user_input}" เป็นรหัส mp-id คั่นด้วยลูกน้ำเท่านั้น (เช่น mp-1188730, mp-1207164)'
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": agent_prompt}],
                        temperature=0.0
                    )
                    target_ids = [x.strip() for x in response.choices[0].message.content.split(',')]
                    st.info(f"🎯 AI แปลงรหัสสำเร็จ: {target_ids}")
                    
                    with MPRester(st.session_state.mp_api_key) as mpr:
                        cols = st.columns(len(target_ids)) 
                        for idx, mp_id in enumerate(target_ids):
                            doc = mpr.materials.summary.search(material_ids=[mp_id])
                            if doc:
                                data = doc[0]
                                comparison_data.append({
                                    "ID": mp_id, "Formula": data.formula_pretty, "Crystal": str(data.symmetry.crystal_system),
                                    "Energy (eV/atom)": round(data.formation_energy_per_atom, 4), "Volume (Å³)": round(data.volume, 2)
                                })
                                with cols[idx]:
                                    st.subheader(f"💎 {data.formula_pretty}")
                                    try:
                                        render_3d_molecule(data.structure.to(fmt="cif"), bg_3d)
                                    except:
                                        st.warning("โหลด 3D ไม่ได้")
                            else:
                                st.warning(f"ไม่พบข้อมูล {mp_id}")
                        
                        if comparison_data:
                            st.divider()
                            st.subheader("📊 Comparison Table")
                            df = pd.DataFrame(comparison_data)
                            st.dataframe(df, use_container_width=True)
                            ai_summary_input = df.to_string() 
                except Exception as e:
                    st.error(f"ระบบขัดข้อง: {e}")

# ==========================================
# 🌟 MODE 3: Live Quantum (PySCF) 🌟
# ==========================================
else:
    user_input = st.text_input("ทดสอบระบบ:", "Methane (CH4) Probe Simulation")
    if st.button("⚛️ รันคำนวณสด", type="primary"):
        with st.spinner("กำลังแก้สมการ Hartree-Fock..."):
            try:
                mol = gto.M(atom='''C 0 0 0; H 0 0 1.089; H 1.026 0 -0.363; H -0.513 -0.889 -0.363; H -0.513 0.889 -0.363''', basis='sto-3g')
                mf = scf.HF(mol)
                energy = mf.kernel()
                st.success("✅ คำนวณสำเร็จ!")
                st.metric("Total Energy (Methane)", f"{energy:.6f} Hartree")
                ai_summary_input = f"System: Methane, Energy: {energy:.6f} Hartree"
            except Exception as e:
                st.error(f"PySCF ขัดข้อง: {e}")

# ─── 6. OpenAI สรุปผล (AI Report) ───
if ai_summary_input and st.session_state.get('api_key'):
    st.divider()
    st.write("🧠 **[AI Report]**")
    with st.spinner("AI กำลังวิเคราะห์ศักยภาพ..."):
        try:
            client = OpenAI(api_key=st.session_state.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"วิเคราะห์ข้อมูลนี้: {ai_summary_input}\nสรุปสั้นๆ (ภาษาไทย) วัสดุใดเสถียร/ปริมาตรดีต่อการบรรจุ CH4"}],
                temperature=0.3
            )
            st.info(response.choices[0].message.content)
        except Exception as e:
            st.error(f"AI ขัดข้อง: {e}")

# ─── 7. Distributors & Support (Sidebar Bottom) ───
st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.subheader("🌟 Official Distributors")
st.sidebar.markdown("""<div style='font-weight:600; line-height:1.2;'>distributor🌿<br>POTEY_007👑<br>MOSS_KAI_POP🐔<br>TN_LEVI🐐<br>ARM-DOI🤣<br>PAI☕</div>""", unsafe_allow_html=True)
st.sidebar.divider()
st.sidebar.subheader("☕ Support the Developers")
fake_qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Thanks%20for%20supporting!&color=ffffff&bgcolor=0b0f19"
if theme_choice == "Light (Clean)":
    fake_qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Thanks%20for%20supporting!"
st.sidebar.image(fake_qr_url, caption="Scan to Donate (Mock QR)")