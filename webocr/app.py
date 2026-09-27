import os
import hashlib
import pymysql
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, Response,session

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # เปลี่ยนเป็น secret key ของคุณ


DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME', 'ocrdb')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,   
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('กรุณาเข้าสู่ระบบก่อนเข้าถึงหน้านี้', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        # ตรวจสอบข้อมูลผู้ใช้จากฐานข้อมูล (ตัวอย่างนี้เป็นการตรวจสอบแบบง่าย)
        if not username or not password:
            flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'warning')
            return render_template('login.html')
        # ตรวจสอบข้อมูลผู้ใช้จากฐานข้อมูล (ตัวอย่างนี้เป็นการตรวจสอบแบบง่าย)
        password_md5 = hashlib.md5(password.encode()).hexdigest()

        try:
            conn = get_db_connection()
            user = None
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE username=%s"
                cursor.execute(sql, (username,))
                user = cursor.fetchone()
            conn.close()

            if user:
                db_password = str(user.get('password',''))
                if (db_password.lower() == password_md5.lower()):
                    session['user'] = user.get('username')
                    flash(f'ยินดีต้อนรับ {session["user"]} เข้าสู่ระบบสำเร็จ', 'success')
                    return redirect(url_for('index'))

            flash('Error', 'danger')
        except Exception as e:
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """ออกจากระบบและลบ Session"""
    username = session.pop('user', None)
    if username:
        flash(f'คุณ {username} ออกจากระบบเรียบร้อยแล้ว', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """แสดงหน้าเว็บอัปโหลดและรายการไฟล์ PDF ที่ถูกบันทึกไว้ใน Database"""
    pdf_list = []
    db_connected = True
    error_message = None

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # ดึงเฉพาะ id, filename, filesize, uploaded_at
            cursor.execute("SELECT id, filename, filesize, uploaded_at FROM pdfstore ORDER BY id DESC")
            pdf_list = cursor.fetchall()
        conn.close()
    except Exception as e:
        db_connected = False
        error_message = f"ไม่สามารถเชื่อมต่อฐานข้อมูล MySQL ได้: {str(e)}"

    return render_template('index.html', pdf_list=pdf_list, db_connected=db_connected, db_error=error_message, current_user=session.get('user'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """รับไฟล์ PDF แล้วบันทึกลงใน MySQL Table pdfstore (Field pdfblob)"""
    if 'pdf_file' not in request.files:
        flash('ไม่พบข้อมูลไฟล์ที่อัปโหลด', 'danger')
        return redirect(url_for('index'))

    file = request.files['pdf_file']

    if file.filename == '':
        flash('กรุณาเลือกไฟล์ PDF ก่อนกดอัปโหลด', 'warning')
        return redirect(url_for('index'))

    if file and file.filename.lower().endswith('.pdf'):
        try:
            # อ่านข้อมูลไบนารี (Binary data) ของไฟล์ PDF
            pdf_data = file.read()
            filename = file.filename
            filesize = len(pdf_data)

            if filesize == 0:
                flash('ไฟล์ PDF ที่เลือกไม่มีข้อมูล (ขนาด 0 bytes)', 'warning')
                return redirect(url_for('index'))

            # บันทึกลงในตาราง pdfstore ใน field pdfblob
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "INSERT INTO pdfstore (filename, pdfblob, filesize) VALUES (%s, %s, %s)"
                cursor.execute(sql, (filename, pdf_data, filesize))
            conn.close()

            flash(f'บันทึกไฟล์ "{filename}" ลงในฐานข้อมูล MySQL (ตาราง pdfstore) สำเร็จ!', 'success')
        except Exception as e:
            flash(f'เกิดข้อผิดพลาดในการบันทึกลง MySQL: {str(e)}', 'danger')
    else:
        flash('ระบบรองรับเฉพาะไฟล์ประเภท PDF (.pdf) เท่านั้น', 'danger')

    return redirect(url_for('index'))

@app.route('/view/<int:pdf_id>')
@login_required
def view_pdf(pdf_id):
    """ดึงข้อมูล pdfblob จาก MySQL แล้วแสดงผล PDF ในเบราว์เซอร์"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT filename, pdfblob FROM pdfstore WHERE id = %s", (pdf_id,))
            record = cursor.fetchone()
        conn.close()

        if record and record['pdfblob']:
            return Response(
                record['pdfblob'],
                mimetype='application/pdf',
                headers={"Content-Disposition": f"inline; filename=\"{record['filename']}\""}
            )
        else:
            flash('ไม่พบไฟล์ PDF ที่ต้องการ', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการดึงข้อมูลไฟล์: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/download/<int:pdf_id>')
@login_required
def download_pdf(pdf_id):
    """ดึงข้อมูล pdfblob จาก MySQL แล้วดาวน์โหลดไฟล์"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT filename, pdfblob FROM pdfstore WHERE id = %s", (pdf_id,))
            record = cursor.fetchone()
        conn.close()

        if record and record['pdfblob']:
            return Response(
                record['pdfblob'],
                mimetype='application/pdf',
                headers={"Content-Disposition": f"attachment; filename=\"{record['filename']}\""}
            )
        else:
            flash('ไม่พบไฟล์ PDF ที่ต้องการดาวน์โหลด', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการดาวน์โหลด: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/delete/<int:pdf_id>', methods=['POST'])
@login_required
def delete_pdf(pdf_id):
    """ลบรายการ PDF ออกจากตาราง pdfstore"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM pdfstore WHERE id = %s", (pdf_id,))
        conn.close()
        flash('ลบข้อมูลไฟล์ PDF ออกจากฐานข้อมูลสำเร็จ', 'info')
    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
