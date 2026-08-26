import warnings
#warnings.filterwarnings("ignore", category=UserWarning, module="easyocr")
warnings.filterwarnings("ignore", category=UserWarning)
import fitz  # PyMuPDF
import easyocr

# 1. โหลดโมเดลภาษา (th = ภาษาไทย, en = ภาษาอังกฤษ)
reader = easyocr.Reader(['th', 'en'])

pdf_path = 'Doc111.pdf'
doc = fitz.open(pdf_path)

# 2. วนลูปอ่าน PDF ทีละหน้า
for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    
    # แปลงหน้า PDF เป็นรูปภาพในรูปแบบ bytes (PNG)
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")  # ตัวแปรนี้เป็น bytes อยู่แล้ว
    
    # 3. สแกนข้อความ (ส่งค่า img_data ที่เป็น bytes เข้าไปตรงๆ)
    result = reader.readtext(img_data, detail=0)
    
    print(f"=== หน้าที่ {page_num + 1} ===")
    print(" ".join(result))
    print('\n')
