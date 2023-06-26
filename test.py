from flask import Flask, request, render_template,session,flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import os, re, hashlib, pandas, tabula
import shutil
import numpy as np
import base64


app = Flask(__name__)
app.secret_key = 'shhhhh'
#Folder initialization!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


app.jinja_env.globals['pd'] = pandas
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt', 'docx'}  # Add allowed file extensions

#Global variables initialization!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

tab_file_path=''
transcript_type=''
concatenated_df=[]
country=''
us_cgpa=''
aus_cgpa=''
canada_cgpa=''

#Database Connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'credentio'
mysql = MySQL(app)


def allowed_file(filename):
    # Check if the file extension is allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def delete_folder_contents(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            delete_folder_contents(file_path)
            os.rmdir(file_path)

@app.route('/')
def hello():  
    app.logger.info(os.environ['Path']) 
    return render_template('home.html')


@app.route('/login')
def openlogin():  
    app.logger.info(os.environ['Path']) 
    return render_template('login.html')

@app.route('/loginsuccess', methods=["POST","GET"] )
def loginsuccess():
    # Output a message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        app.logger.info(password)
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE email = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['firstname']=account[1]
            session['email']=account[3]
            # Redirect to home page
            if account[3] == 'Admin@gmail.com':
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM school")
                data = cursor.fetchall()
                app.logger.info(data)
                cursor.close()
                return render_template('admin.html', universities=data)
            else:
                return render_template('userview.html', name=session['firstname'])
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
            return render_template('login.html', msg=msg)
    # Show the login form with message (if any)
    

@app.route('/register')
def openregister():
        return render_template('register.html')

@app.route('/registrationsuccess', methods=['GET', 'POST'])
def register_success():
    # Output message if something goes wrong...
    msg=''
    logmsg=''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST':
        # Create variables for easy access
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        app.logger.info(username)
        password = request.form['password']
        confirmpassword = request.form['confirmpword']
    if password == confirmpassword:
        cursor = mysql.connection.cursor()
        sql="SELECT * FROM accounts WHERE email = %s"
        cursor.execute(sql, (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
            logmsg='Sign in here'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', username):
           msg = 'Invalid email address!'
           logmsg=''
        elif not username or not password :
            msg = 'Please fill out the form!'
            logmsg=''
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO accounts(firstname, lastname, email, password) VALUES (%s, %s, %s, %s)', (firstname, lastname, username, password))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            logmsg='Sign in here'
    else:
        msg = 'Passwords don\'t match'

    # Check if account exists using MySQL
    
    return render_template('register2.html', msg=msg, logmsg=logmsg)
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('openlogin'))

@app.route('/unis')
def Admin():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM school")
    data = cursor.fetchall()
    app.logger.info(data)
    cursor.close()
    return render_template('admin.html', universities=data)

@app.route('/insert', methods=['GET', 'POST'])
def insert():
    if request.method == 'POST':
        name=request.form['name']
        image=request.form['image']
        location=request.form['location']
        link=request.form['link']
        description=request.form['description']
        defaultcgpa=request.form['usa_cgpa']
        countrycgpa=request.form['country_cgpa']

        #check if data already exists
        cursor = mysql.connection.cursor()
        sql="SELECT * FROM school WHERE name = %s AND location LIKE %s"
        args=location+ '%'
        cursor.execute(sql, (name, args))
        uni = cursor.fetchone()
        if uni:
            flash("Data Already exists")  
        else:
            flash("Data Inserted successsfuly")  
            cursor.execute("INSERT INTO school (name, image, location, link, description, default_cgpa, country_cgpa) VALUES (%s, %s, %s,%s, %s, %s, %s)", (name, image, location, link, description, defaultcgpa, countrycgpa))
            cursor.execute("UPDATE school SET country_cgpa = NULL WHERE country_cgpa = 0.00;")
            mysql.connection.commit()
        return redirect(url_for('Admin'))
    
@app.route('/delete/<string:id_data>', methods=['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully")
    cursor=mysql.connection.cursor()
    cursor.execute('DELETE FROM school WHERE id=%s', (id_data,))
    mysql.connection.commit()
    return redirect(url_for('Admin'))

@app.route('/update', methods=["POST", "GET"])
def  update():
    if request.method == 'POST':
        id_data = request.form['id']
        name=request.form['name']
        image=request.form['image']
        location=request.form['location']         
        link=request.form['link']
        description=request.form['description']
        defaultcgpa=request.form['defaultcgpa']
        countrycgpa=request.form['countrycgpa']

        cursor=mysql.connection.cursor()
        cursor.execute("UPDATE school SET name=%s, image=%s, location=%s, link=%s, description=%s, default_cgpa=%s, country_cgpa=%s", (name, image, location, link, description, defaultcgpa, countrycgpa))
        flash('Data Updated Successfully')
        return redirect(url_for('Admin'))

@app.route('/users')
def user():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM accounts")
    data = cursor.fetchall()
    app.logger.info(data)
    cursor.close()

    return render_template('users.html', users=data)

@app.route('/userview')
def hellouser():  
    app.logger.info(os.environ['Path']) 
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('userview.html', name=session['firstname'])
    # User is not loggedin redirect to login page
    return redirect(url_for('openlogin'))

@app.route('/userview', methods=['POST'])
def upload_file():
    global tab_file_path
    global country
    global transcript_type
    global concatenated_df
    concatenated_df=[]
    app.logger.info(os.environ['Path']) 

   

    # Check if a file was uploaded
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    # Check if the file has a valid filename and extension
    if file.filename == '' or not allowed_file(file.filename):
        return 'Invalid file'
    
    delete_folder_contents(app.config['UPLOAD_FOLDER'])
    # Save the uploaded file to the specified folder
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    tab_file_path=file_path.replace("\\","/")

    app.logger.info(tab_file_path)
    transcript_type = request.form.get('transcript-type')
    app.logger.info(transcript_type)
    if transcript_type == 'official':
        app.logger.info(transcript_type)
        tables = tabula.read_pdf(tab_file_path,multiple_tables=True,pages='all',encoding='cp1252', stream=True, guess=False, lattice=True)
        modified_tables = []
        common_column_headers = ['COURSE', 'COURSE TITLE', 'CREDIT UNIT', 'MARK', 'GRADE SCORE', 'WEIGHTED SCORE', 'GPA', 'CGPA']
        # Replace with your desired column names
        # Concatenate the tables into a single DataFrame
        for i, table in enumerate(tables):
            if i == 0 or i == len(tables) - 1:
                print("okay")  # Exclude first and last table
            else:
                table = table.dropna(axis=1, how='all')
                num_columns = table.shape[1]
                new_column_headers = common_column_headers[:num_columns]
                table.columns = new_column_headers
                modified_tables.append(table)
        # Concatenate modified tables into a single dataframe
        concatenated_df = pandas.concat(modified_tables, ignore_index=True)
        #concatenated_df.to_csv('finnaoutput_table.csv', index=False)

        #Create Semester i rows below Total
        rows_to_insert = []
        # Iterate over the rows of the DataFrame
        count=2
        for index, row in concatenated_df.iterrows():
            if row['COURSE'] == 'TOTAL' or row['COURSE TITLE'] == 'TOTAL':
                # Create a new row with the desired values
                new_row = pandas.Series(['Semester ' + str(count), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], index=concatenated_df.columns)
                # Append the new row to the list of rows to insert
                rows_to_insert.append(new_row)
                count=count+1
            # Append the current row to the list of rows to insert
            rows_to_insert.append(row)
        concatenated_df = pandas.DataFrame(rows_to_insert, columns=concatenated_df.columns)

        # Reset the index of the updated DataFrame
        concatenated_df.reset_index(drop=True, inplace=True)
        #print(updated_df)
        #updated_df.to_csv('finnaoutput3_table.csv', index=False, mode ='a') 

        #Remove rows with Total
        column_name1 = 'COURSE'
        column_name2 ='COURSE TITLE'
        value_total = 'TOTAL'
        concatenated_df= concatenated_df[concatenated_df[column_name1] != value_total]
        concatenated_df= concatenated_df[concatenated_df[column_name2] != value_total]
        #print(concatenated_df)
        concatenated_df = concatenated_df.drop(concatenated_df.index[-1])
        #concatenated_df.to_csv('finnaoutput4_table.csv', index=False) 

        #Deleting GPA,CGPA AND WEIGHTED SCORE COLUMNS
        del concatenated_df["WEIGHTED SCORE"]
        del concatenated_df["GPA"]
        del concatenated_df["CGPA"]

        print(concatenated_df)

        def check_numeric_columns(df, column_name):
            for index, value in df[column_name].items():
                if isinstance(value, str):
                # Select only the numeric characters from the string
                    numeric_chars = ''.join(char for char in value if char.isdigit())
        
                    # Convert the numeric string to an integer value
                    numeric_value = int(numeric_chars)
        
                    # Update the value in the DataFrame
                    df.at[index, column_name] = numeric_value
            #df.to_csv('finnaoutput5_table.csv', index=False) 
            return df

        column_mark="MARK"
        column_unit="CREDIT UNIT"
        concatenated_df=check_numeric_columns(concatenated_df, column_mark)
        concatenated_df=check_numeric_columns(concatenated_df, column_unit)
        #concatenated_df.to_csv('finnaoutput5_table.csv', index=False) 


    #Unofficial Transcript!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
    # Unofficial Transcrip!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
    else:
        modified_tables = []
        tables = tabula.read_pdf(tab_file_path,pages='all',encoding='cp1252', lattice=True, stream=True)
        table_count = len(tables)
        app.logger.info(tables)
        selected_tables =tables[0:table_count]
        common_column_headers = ['COURSE', 'COURSE TITLE', 'CREDIT UNIT', 'GRADE SCORE', 'WEIGHTED SCORE', 'GPA', 'CGPA']

        # Concatenate the tables into a single DataFrame
        for i, table in enumerate(selected_tables):
            table.columns.name = None
            table = table.dropna(axis=1, how='all')
            num_columns = table.shape[1]
            new_column_headers = common_column_headers[:num_columns]
            table.columns = new_column_headers
            modified_tables.append(table) 
            #concatenated_df = pandas.concat([concatenated_df, table])
        concatenated_df = pandas.concat(modified_tables)
        app.logger.info(concatenated_df)

        # Save the combined DataFrame to a CSV file, appending to any existing data
        #
        del concatenated_df["WEIGHTED SCORE"]
        del concatenated_df["GPA"]
        del concatenated_df["CGPA"]

        #REMOVE ROW
        column_name = 'CREDIT UNIT'  # Index of the column to check
        value_to_drop = 'CREDIT\rUNIT'  # Value of the cell to match
        concatenated_df= concatenated_df[concatenated_df[column_name] != value_to_drop]

        #REMOVE ROW
        column_name2 = 'COURSE TITLE'  
        value_total = 'TOTAL'
        concatenated_df= concatenated_df[concatenated_df[column_name2] != value_total]
        concatenated_df.to_csv('output_table1.csv', index=False)

        country = request.form.get('country')
        app.logger.info(country)
    return render_template('userview2.html', name=session['firstname'])
    
#show data!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
@app.route('/show_data', methods=['POST'])
def show_file():
    global country
    global transcript_type
    global concatenated_df
    global us_cgpa
    global aus_cgpa
    global canada_cgpa

    if transcript_type == "official":
        mapping_dict_us = {
            range(70, 101): 'A',
            range(60, 70): 'B+',
            range(50,60): 'B',
            range(45,50):'C+',
            range(0,45):'F'
        }
    else:
        mapping_dict_us = {'A': 'A', 'B': 'B+', 'C': 'B', 'D': 'C+', 'F': 'F'}
    
    
    mapping_us = {'A':4.0, 'B+':3.3, 'B':3.0, 'C+':2.3, 'F':0}

    if country =="canada":
        grade_equivalency = 'Canadian Grades Equivalency'
        weighted_scores = 'Canadian Weighted Score Equivalency'
           
    else:
        grade_equivalency = 'USA Grades Equivalency'
        weighted_scores = 'USA Weighted Score Equivalency'

    if transcript_type == "official":
        concatenated_df[grade_equivalency] = concatenated_df['MARK'].apply(lambda x: next((v for k, v in mapping_dict_us.items() if x in k), np.nan))
    else:
        concatenated_df[grade_equivalency] = concatenated_df['GRADE SCORE'].map(mapping_dict_us)


    #Mapping the total new weighted scores
    concatenated_df[weighted_scores] = concatenated_df[grade_equivalency].map(mapping_us)
    concatenated_df[weighted_scores] *= concatenated_df['CREDIT UNIT'].astype(float)
    concatenated_df[weighted_scores] = concatenated_df[weighted_scores] .round(2)
    #Clacing CGPA
    concatenated_df['CREDIT UNIT'] = concatenated_df['CREDIT UNIT'].astype(float)
    unit_sum = concatenated_df['CREDIT UNIT'].sum()
    print(unit_sum)

    weighted_point_sum = concatenated_df[weighted_scores].sum()
    print(weighted_point_sum)

    cgpa= weighted_point_sum/ unit_sum

    print(cgpa)
    
    result = "{:.2f}".format(cgpa)
    canada_cgpa=result
    us_cgpa=result
    result = str(result) + "/4.00"
    app.logger.info(result)

    concatenated_df.to_csv('finnaoutput_table.csv', index=False) 
    if country== "uk":
        if transcript_type == "official":
            mapping_dict_uk = {
            range(70, 101): 'First Class Honours',
            range(60, 70): 'Upper Second Class Honours',
            range(50, 60): 'Lower Second Class Honours',
            range(45,50): 'Third Class',
            range(40,45):'Pass',
            range(0,40):'Fail'
        }
        else:
            mapping_dict_uk = {'A': 'First Class Honours', 'B': 'Upper Second Class Honours', 'C': 'Lower Second Class Honours', 'D': 'Third Class', 'F': 'Fail'}
        
        del concatenated_df["USA Grades Equivalency"]
        del concatenated_df["USA Weighted Score Equivalency"]
        uk_grade_equivalency = 'UK Grades Equivalency'
        if transcript_type == "official":
            concatenated_df[uk_grade_equivalency] = concatenated_df['MARK'].apply(lambda x: next((v for k, v in mapping_dict_uk.items() if x in k), np.nan))
        else:
            concatenated_df[uk_grade_equivalency] = concatenated_df['GRADE SCORE'].map(mapping_dict_uk)

        result = str(result)
        result = result + "(Note UK does not use the GPA system, this is the US equivalent CGPA)"
    if country == "australia":
        if transcript_type == 'official':
            mapping_dict_aus = {
            range(83, 101): 'HD',
            range(73, 83): 'D',
            range(63,73): 'C',
            range(50,63):'P',
            range(0,50):'F'
        }
        else:
            mapping_dict_aus = {'A': 'D', 'B': 'C', 'C': 'P', 'D': 'F', 'F': 'F'}
        
        mapping_aus = {'HD':7.0, 'D':6.0, 'C':5.0, 'P':4.0, 'F':0}

        del concatenated_df["USA Grades Equivalency"]
        del concatenated_df["USA Weighted Score Equivalency"]

        grade_equivalency = 'Australian Grades Equivalency'
        weighted_scores = 'Australian Weighted Score Equivalency'
        
        if transcript_type == 'official':
            concatenated_df[grade_equivalency] = concatenated_df['MARK'].apply(lambda x: next((v for k, v in mapping_dict_aus.items() if x in k), np.nan))
        else:
            concatenated_df[grade_equivalency] = concatenated_df['GRADE SCORE'].map(mapping_dict_aus)


        #Mapping the total new weighted scores
        concatenated_df[weighted_scores] = concatenated_df[grade_equivalency].map(mapping_aus)
        concatenated_df[weighted_scores] *= concatenated_df['CREDIT UNIT'].astype(float)
        concatenated_df[weighted_scores] = concatenated_df[weighted_scores] .round(2)
        #Clacing CGPA
        concatenated_df['CREDIT UNIT'] = concatenated_df['CREDIT UNIT'].astype(float)
        unit_sum = concatenated_df['CREDIT UNIT'].sum()
        print(unit_sum)

        weighted_point_sum = concatenated_df[weighted_scores].sum()
        print(weighted_point_sum)

        cgpa= weighted_point_sum/ unit_sum

        print(cgpa)
    
        result = "{:.2f}".format(cgpa)
        aus_cgpa=result
        result= str(result) + "/7.00"
        

    concatenated_df = concatenated_df.replace({np.nan: " "})

    
    return render_template('tables.html', name=session['firstname'], dataframe=concatenated_df, variable=result)

@app.route('/userunis')
def view_us():
    location = 'USA'
    cursor = mysql.connection.cursor()
    sql=("SELECT * FROM school WHERE location LIKE %s")
    args=location+ '%'
    cursor.execute(sql,(args,))
    data = cursor.fetchall()
    app.logger.info(data)
    cursor.close()
    return render_template('universities.html', name=session['firstname'], rows=data)

@app.route('/ukunis')
def view_uk():
    location = 'United Kingdom'
    cursor = mysql.connection.cursor()
    sql=("SELECT * FROM school WHERE location LIKE %s")
    args=location+ '%'
    cursor.execute(sql,(args,))
    data = cursor.fetchall()
    app.logger.info(data)
    cursor.close()
    return render_template('universities.html', name=session['firstname'], rows=data)

@app.route('/canadaunis')
def view_canada():
    location = 'Canada'
    cursor = mysql.connection.cursor()
    sql=("SELECT * FROM school WHERE location LIKE %s")
    args=location+ '%'
    cursor.execute(sql,(args,))
    data = cursor.fetchall()
    app.logger.info(data)
    cursor.close()
    return render_template('universities.html', name=session['firstname'], rows=data)

@app.route('/australiaunis')
def view_australia():
    location = 'Australia'
    cursor = mysql.connection.cursor()
    sql=("SELECT * FROM school WHERE location LIKE %s")
    args=location+ '%'
    cursor.execute(sql,(args,))
    data = cursor.fetchall()
    app.logger.info(data)
    cursor.close()
    return render_template('universities.html', name=session['firstname'], rows=data)

@app.route('/view_schools')
def views_schools():
    location =''
    cursor = mysql.connection.cursor()

    if country == 'uk':
        location = "United Kingdom"
    elif country == 'usa':
        location = 'USA'
    elif country == 'australia':
        location= 'Australia'
    else:
        location='Canada'
    
    if country== 'uk' or country =='usa' or country == 'canada':
        sql="SELECT * FROM school WHERE location LIKE %s AND default_cgpa <= %s ORDER BY default_cgpa DESC"
        args=location+ '%'
        cursor.execute(sql, (args,us_cgpa))
        
    else:
        sql="SELECT * FROM school WHERE location LIKE %s AND (default_cgpa <= %s OR country_cgpa <= %s) ORDER BY country_cgpa DESC"
        args=location+ '%'
        cursor.execute(sql, (args,us_cgpa,aus_cgpa))

    rows = cursor.fetchall()
    app.logger.info(rows)
    mysql.connection.commit()
    cursor.close()
    app.logger.info(rows)
    return render_template('filterschool.html',location=location, name=session['firstname'], rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
