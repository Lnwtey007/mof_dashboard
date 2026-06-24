import tarfile
from pymatgen.io.cif import CifParser
import pandas as pd
import warnings

# ปิดแจ้งเตือนจุกจิก
warnings.filterwarnings("ignore")

TAR_FILE = 'ARCMOF_20220610.tar.gz'

def extract_max_charge_from_raw(cif_content):
    try:
        parser = CifParser.from_str(cif_content)
        cif_dict = parser.as_dict()
        
        # เข้าถึงบล็อกข้อมูลแรกของ CIF
        block_key = list(cif_dict.keys())[0]
        block_data = cif_dict[block_key]
        
        # ดึงประจุจากคอลัมน์ที่เราค้นพบ!
        if '_atom_type_partial_charge' in block_data:
            charges_raw = block_data['_atom_type_partial_charge']
            
            # แปลงข้อมูลที่เป็นข้อความให้เป็นตัวเลขทศนิยม
            if isinstance(charges_raw, list):
                charges = [float(c) for c in charges_raw]
            else:
                charges = [float(charges_raw)]
                
            return max(charges) # คืนค่าประจุบวกที่สูงที่สุด (ซึ่งมักจะเป็น Metal Node)
            
    except Exception:
        pass
    return None

print("🚀 กำลังเดินเครื่องสกัดประจุแบบ Raw Extraction...")

data = []
success_count = 0

with tarfile.open(TAR_FILE, "r:gz") as tar:
    for member in tar:
        if member.name.endswith('.cif'):
            f = tar.extractfile(member)
            if f:
                content = f.read().decode('utf-8')
                max_charge = extract_max_charge_from_raw(content)
                
                if max_charge is not None:
                    # ตัดเอาแค่ชื่อไฟล์ ไม่เอานามสกุล
                    filename = member.name.split('/')[-1].split('.')[0].strip()
                    data.append({'filename': filename, 'Max_Metal_Charge': max_charge})
                    success_count += 1
                    
                    # ปริ้นท์อัปเดตทุกๆ 100 ไฟล์ จะได้รู้ว่าเครื่องไม่ค้าง
                    if success_count % 100 == 0:
                        print(f"⚡ ดึงประจุสำเร็จแล้ว {success_count} โครงสร้าง...")
                        
            # ลองเทสที่ 1,000 ไฟล์แรกก่อน ถ้าผ่านค่อยเอาคอมเมนต์ออกเพื่อรันทั้งหมด
            if success_count >= 1000:
                break

if data:
    df_charges = pd.DataFrame(data)
    df_charges.to_csv("extracted_charges.csv", index=False)
    print(f"\n✅ สำเร็จ! สกัดค่าประจุได้ทั้งหมด {len(data)} โครงสร้าง บันทึกลง extracted_charges.csv แล้ว")
else:
    print("\n❌ ไม่พบข้อมูลประจุเลย รบกวนตรวจสอบไฟล์อีกครั้ง")