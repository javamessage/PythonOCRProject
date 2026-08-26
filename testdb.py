import sqlite3

def insert_data(name, surname, stu_id,color,address,have_car):

    conn = sqlite3.connect('ocr_db.db')
    cursor = conn.cursor()

    sql = 'INSERT INTO student_data (Name,Surname,Student_ID,Color,Address,have_car ) VALUES (?,?,?,?,?,?)'

    # Execute the insertion
    cursor.execute(sql, (name, surname, stu_id, color, address, have_car))
    conn.commit()
    conn.close()

def update_data(no,name, surname, color,address,have_car):
    conn = sqlite3.connect('ocr_db.db')
    cursor = conn.cursor()

    sql = 'UPDATE student_data SET Name=?, Surname=?, Color=?, Address=?, have_car=? WHERE no=?'

    # Execute the update
    cursor.execute(sql, (name, surname, color, address, have_car, no))
    conn.commit()
    conn.close()


def delete_data(no):
    conn = sqlite3.connect('ocr_db.db')
    cursor = conn.cursor()

    sql = 'DELETE FROM student_data WHERE no=?'

    # Execute the deletion
    cursor.execute(sql, (no,))
    conn.commit()
    conn.close()

#insert_data('John', 'Doe', 12345, 'Blue', '123 Main St', 'Yes')
#insert_data('Jane', 'Smith', 67890, 'Red', '456 Elm St', 'No')
#insert_data('Alice', 'Johnson', 54321, 'Green', '789 Oak St', 'Yes')
#update_data(9, 'John', 'Doe',  1, '123 Main St', 'Yes')
delete_data(11)


print("end")