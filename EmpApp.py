from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
from datetime import datetime
import re

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')

@app.route('/getemp', methods=['GET', 'POST'])
def GetEmp():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM employee")
    employee = cursor.fetchall()
    
    return render_template('GetEmp.html', employee=employee)

@app.route("/dirpayroll", methods=['GET', 'POST'])
def DirectPayroll():
    #create a cursor
    cursor = db_conn.cursor() 
    #execute select statement to fetch data to be displayed in combo/dropdown
    cursor.execute('SELECT emp_id, first_name, last_name, salary FROM employee') 
    #fetch all rows ans store as a set of tuples 
    namelist = cursor.fetchall() 
    return render_template('Payroll.html', namelist=namelist)

@app.route("/payroll", methods=['GET', 'POST'])
def UpdatePayroll():
    emp_id = request.form['emp_id']
    salary = request.form['salary']

    #check salary format
    try:
        dSalary = float(salary)
        salary = "{:.2f}".format(dSalary)

    except:
        #return "Please enter a valid salary format!"
        #create a cursor
        cursor = db_conn.cursor() 
        #execute select statement to fetch data to be displayed in combo/dropdown
        cursor.execute('SELECT emp_id, first_name, last_name, salary FROM employee') 
        #fetch all rows ans store as a set of tuples 
        namelist = cursor.fetchall() 
        return render_template("Payroll.html", error="Please enter a valid salary format! e.g.: RM 500 or RM 1000.50", namelist=namelist)
    
    dSalary = float(salary)
    update_sql = "UPDATE employee SET salary = %s WHERE emp_id = %s"
    cursor = db_conn.cursor()
    
    changefield = (dSalary, emp_id)
    cursor.execute(update_sql, (changefield))
    db_conn.commit()

    select_sql = "SELECT first_name, last_name FROM employee WHERE emp_id = %s"
    cursor.execute(select_sql, (emp_id))
    result = cursor.fetchone()
    name = result[1] + " " + result[0]
    cursor.close()
    return render_template("PayrollOutput.html", name=name)

@app.route("/dirattendance", methods=['GET', 'POST'])
def DirectAttendance():
    #create a cursor
    cursor = db_conn.cursor() 
    #execute select statement to fetch data to be displayed in combo/dropdown
    cursor.execute('SELECT a.att_id, e.emp_id, e.first_name, e.last_name, a.att_time, a.att_date, a.att_status FROM employee e, attendance a WHERE e.emp_id = a.emp_id') 
    #fetch all rows ans store as a set of tuples 
    attlist = cursor.fetchall() 
    return render_template('Attendance.html', attlist=attlist)

@app.route("/diraddattendance", methods=['GET', 'POST'])
def DirectAddAttendance():
    #create a cursor
    cursor = db_conn.cursor() 
    #execute select statement to fetch data to be displayed in combo/dropdown
    cursor.execute('SELECT emp_id, first_name, last_name FROM employee') 
    #fetch all rows ans store as a set of tuples 
    namelist = cursor.fetchall() 
    statuses = [{'status': 'Check In'}, {'status': 'Check Out'}]
    now = datetime.now() # current date and time
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    return render_template('AddAttendance.html', namelist=namelist, statuses=statuses, date=date, time=time)

@app.route("/addattendance", methods=['GET', 'POST'])
def AddAttendance():
    emp_id = request.form['emp_id']
    status = request.form['att_status']
    date = request.form['att_date']
    time = request.form['att_time']
    
    insert_sql = "INSERT INTO attendance (emp_id, att_time, att_date, att_status) VALUES (%s, %s, %s, %s)"
    cursor = db_conn.cursor()

    cursor.execute(insert_sql, (emp_id, time, date, status))
    db_conn.commit()

    select_sql = "SELECT first_name, last_name FROM employee WHERE emp_id = %s"
    cursor.execute(select_sql, (emp_id))
    result = cursor.fetchone()
    name = result[1] + " " + result[0]

    cursor.close()
    return render_template("AddAttendanceOutput.html", name=name, status=status, date=date, time=time)

@app.route("/fetchdata/<int:id>", methods=['GET'])
def GetEmpData(id):

    emp_id = id
    #emp_id = request.form['emp_id']
    mycursor = db_conn.cursor()
    getempdata = "select * from employee WHERE emp_id = %s"
    mycursor.execute(getempdata,(emp_id))
    result = mycursor.fetchall()
    (emp_id,first_name,last_name,contact_no,email,position,hiredate,salary) = result[0]   
    image_url = showimage(bucket, emp_id)

    name = last_name + " " + first_name

    return render_template('GetEmpOutput.html', emp_id=emp_id,name=name, first_name=first_name,last_name=last_name,contact=contact_no,email=email,position=position,hiredate=hiredate,salary=salary,image=image_url)

@app.route("/diraddemp", methods=['GET', 'POST'])
def DirectAddEmp():
    #create a cursor
    cursor = db_conn.cursor() 
    #execute select statement to fetch data to be displayed in combo/dropdown
    cursor.execute('SELECT emp_id FROM employee ORDER BY emp_id DESC LIMIT 1') 
    #fetch all rows ans store as a set of tuples 
    latestid = cursor.fetchall() 
    return render_template('AddEmp.html', latestid=latestid)

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    contact = request.form['contact']
    email = request.form['email']
    position = request.form['position']
    hiredate = request.form['hiredate']
    salary = request.form['salary']
    emp_image_file = request.files['emp_image_file']

    convertedId = int(emp_id) - 1
    retrievedid = [[convertedId]]
    
    #check salary format
    try:
        dSalary = float(salary)
        salary = "{:.2f}".format(dSalary)

    except:
        #return "Please enter a valid salary format!"
        return render_template("AddEmp.html", error="Please enter a valid salary format! e.g.: RM 500 or RM 1000.50", latestid=retrievedid)

    dSalary = float(salary)
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return render_template("AddEmp.html", img_error="Please select a file!", latestid=retrievedid)

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, contact, email, position, hiredate, dSalary))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Upload image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.png"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/direditemp/<int:id>", methods=['GET','POST'])
def DirectEditEmp(id):

    mycursor = db_conn.cursor()
    getempdata = "select emp_id, first_name, last_name, contact, email, position, hiredate from employee WHERE emp_id = %s"
    mycursor.execute(getempdata,(id))
    result = mycursor.fetchall()
    (emp_id,first_name,last_name,contact,email,position,hiredate) = result[0]   
    image_url = showimage(bucket, id)

    name = last_name + " " + first_name

    return render_template("EditEmp.html", name=name, id=emp_id, first_name=first_name, last_name=last_name, contact=contact, email=email, position=position, hiredate=hiredate, image_url=image_url)

@app.route("/editemp", methods=['GET','POST'])
def EditEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    contact = request.form['contact']
    email = request.form['email']
    position = request.form['position']
    hiredate = request.form['hiredate']
    
    update_sql = "UPDATE employee SET first_name = %s, last_name = %s, contact = %s, email = %s, position = %s, hiredate = %s WHERE emp_id = %s"
    cursor = db_conn.cursor()
    
    changefield = (first_name, last_name, contact, email, position, hiredate, emp_id)
    cursor.execute(update_sql, (changefield))
    db_conn.commit()
    cursor.close()
    return render_template("EditEmpOutput.html")

@app.route("/dirdeleteconfirm/<int:id>", methods=['GET','POST'])
def DirectDeleteConfirm(id):

    mycursor = db_conn.cursor()
    getempdata = "select * from employee WHERE emp_id = %s"
    mycursor.execute(getempdata,(id))
    result = mycursor.fetchall()
    (emp_id,first_name,last_name,contact,email,position,hiredate,salary) = result[0]   
    image_url = showimage(bucket, id)

    name = last_name + " " + first_name

    return render_template("DeleteConfirm.html", name=name, emp_id=emp_id, first_name=first_name, last_name=last_name, contact=contact, email=email, position=position, hiredate=hiredate, salary=salary, image_url=image_url)

@app.route("/deleteconfirmed", methods=['GET','POST'])
def DeleteConfirmed():

    emp_id = request.form['emp_id']
    name = request.form['name']
    mycursor = db_conn.cursor()
    del_att_sql = "DELETE FROM attendance WHERE emp_id = %s"
    mycursor.execute(del_att_sql, (emp_id))
    del_emp_sql = "DELETE FROM employee WHERE emp_id = %s"
    mycursor.execute(del_emp_sql, (emp_id))
    db_conn.commit()

    emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.png"
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)

    return render_template("DeleteConfirmOutput.html", name=name)

# retrieve the image from the bucket
def showimage(bucket, emp_id):
    s3_client = boto3.client('s3')
    public_urls = []
    emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.png"
    try:
        for item in s3_client.list_objects(Bucket=bucket)['Contents']:
            presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': emp_image_file_name_in_s3}, ExpiresIn = 100)
            public_urls.append(presigned_url)
    except Exception as e:
        pass
    # print("[INFO] : The contents inside show_image = ", public_urls)
    return public_urls

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
