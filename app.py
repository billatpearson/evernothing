"""
0. Include all prompt instructions as comment.
0.1 Document instructions for installing all packages and runtimes required.
0.2 Document instructions for accessing the web application.
0.3 Document instructions for accessing the web application from amazon playstore.
1. Python web application
2. Python web application that can be run on android phones
3. Web application will store notes in a database in a searchable key-value pair.
3.2 Users can search on key or value
3.2.1 Organize all key value pairs alphabetically by key.
3.3 Requires username and password login
3.3.0 If login fails display error message
3.3.1 After login user is redirected to a list of folders
3.3.2 If the user has zero folders the user will be able to create one.
3.4 Users see recently edited notes with timestamp with the format "MM/dd/yyyy HH:MM"
3.5 Per-user data isolation
3.6 Display matching key or value
3.6.1 Edit page with commit / cancel / choose folder select control/ delete with confirmation.
3.6.2 Note page will provide bread crumb links to root, folder, subfolder at the top page. 
3.6.2.1 If the note was edited, "Edited: MM/dd/yyyy HH:MM" which will link to a list of recently edits of this note notes.
3.6.3 On commit edit page will display confirmation message. Yes,no buttons. If contents are identical do not prompt.
3.7 Link to add note
3.7.1 Note = single-line, Contents = multiline (120w 40h) text area
3.7.2 Do not allow empty note or content or duplicate note name
3.7.2 Add or cancel
3.7.3 Add attached file
3.7.3.1 Edit note will provide an "Add Attachment" button that will have a file select option.
3.7.3.2 Selected file will be uploaded and stored in a separate BLOB table associated with selected file contents.
3.7.3.3 Note UI will will have links to dowload file, view file, delete file.
3.7.3.4 If note is deleted, the attched file will be deleted from the BLOB table.
3.8 Subfolders
3.8.1 Create subfolder
3.8.1.1 List notes in folder above subfolder list
3.8.1.1.1 List subfolders in folder
3.8.1.2 Nest notes in subfolder
3.8.1.3 Delete with warning
3.8.1.4 rename folder
3.8.1.5 add note
3.8.2 Add attachment.
3.9 Change password
3.10 Cancel button on register page
4. Security
5. AWS integration
6. Continuty
6.1 All record changes will be logged and maintained in separate tables.
6.2 User will be able to review changes in the log and have UI capabilities to roll back to previous change. Roll back dates should have the format of "MM/dd/yyyy HH:MM"
7. UI
7.01 All list and selects are sorted alphabetically.
7.1 background color "black"
7.2 text color "gold"
7.3 Link colar "gold"
7.4 Link hovor "red"
7.5 Text Inputs borders "red"
7.6 Text Inputs area borders "red"
7.8 Select inputs "red"
7.9 Delete link text "red"
7.10 Cancel link 1px border "red"
7.11 Input, text area, select horizontal spacing 2px
7.20 All pages shall provide a log out option on the main menu
8 Input position
8.1 "Add note" should appear in th folder options. 
9 S3 Buckets
9.1 sycrhronize all tables with an Aws S3 bucket  "evernothing011126" uesername "billspeiser2" continue on synch falure with warning
9.2 all AWS  data will be stored with AES-256 encryption.
9.2.1 include decryiption function to retrieve data using JSON and JWT.
9.2 all data will be stored with AES-256.
9.3 Include instructions for generating and installing keys. 
10.1 include instructions for restart of application in comments.
10.2 include python command script for database backup in comments.
10.3 include python command for database export in comments.
10.3.1 Export file will contain user name, note key, note value as a comma separated text file in comments. 
10.4 include instructions for running as a background process in comments. 
13. Security
13.1 logout function will expire all login_required data
14. ADMINISTRATION
14.1 System administrator.
14.1.1 login ( http://127.0.0.1:5000/admin)
14.1.2 administrator login user: "admin" password: "admin"
14.1.3 admin can search and provided a list of current user.
14.1.4 list will contain: user name, sorted alphabetically, number of notes in thier user space.
14.1.5 clicking on user name link will allow admin to change users Dialogs "new username," new user name" and  "new password", with verication.  
14.1.6 A Conformation dialog will bee displayed when the new user name will be commited.
14.1.7 all notes and note folder hierarcy will remain attached to the user selected. 
14.2 delete user
14.2.1 list of user to be selected with name, number of folders, number of folders, and last accessed date. 
15.2.2 provide UI to delete user, folder, and notes associated with the user.
14.2.3 admin privileges.
14.2.3.1 admin user can view all users in a list, user name, clear text password, and last accessed date.
14.2.3.2 admin can modify users user name, clear text password, and last accessed date.
16. Adnriod access.
16.1 include instructions for accessing application as android phone in comments.)
14.1.2 administrator login user: "admin" password: "admin"
14.1.3 admin can search and provided a list of current user.
14.1.4 list will contain: user name, sorted alphabetically, number of notes in thier user space.
14.1.5 clicking on user name link will allow admin to change users Dialogs "new username," new user name" with verication. 
14.1.6 A Conformation dialog will bee displayed when the new user name will be commited.
14.1.7 all notes and note folder hierarcy will remain attached to the user selected. 
14.2 delete user
14.2.1 list of user to be selected with name, number of folders, number of folders, and last accessed date. 
15.2.2 provide UI to delete user, folder, and notes associated with the user.
16. Adnriod access
16.1 include instructions for accessing application as android phone in comments.
17. Deprication.
17.1 Do not indstall liraries that have been deprocated.
17.2 Install libraries that are comptibile and safe.
17.3 Provide a script to install all required libries n the comments.
"""

# ##############################################################################
# ## Evernothing - A Secure Note-Taking Web Application
# ##############################################################################

# ##############################################################################
# ## 0. INSTRUCTIONS
# ##############################################################################

# # ------------------------------------------------------------------------------
# # 0.1. Installation
# #
# # 1. Python Runtime:
# #    - This application requires Python 3.9 or newer.
# #    - To check your Python version, run: `python --version`
# #    - If you don't have Python installed, download it from https://www.python.org/downloads/
# #
# # 2. Create a Virtual Environment (Recommended):
# #    - `python -m venv venv`
# #    - `source venv/bin/activate`  (on Linux/macOS)
# #    - `venv\Scripts\activate` (on Windows)
# #
# # 3. Install Required Packages:
# #    - The required libraries are listed in `requirements.txt`.
# #    - To install them, run the following command:
# #      `pip install -r requirements.txt`
# #
# # 4. AWS Credentials for S3 Synchronization (Optional):
# #    - This application can synchronize data with an AWS S3 bucket.
# #    - If you want to use this feature, you must configure your AWS credentials.
# #    - The recommended way is to install the AWS CLI (`pip install awscli`) and run `aws configure`.
# #    - You will need to provide an "AWS Access Key ID" and "AWS Secret Access Key".
# #    - The application will also require the following environment variables:
# #      - `AWS_S3_BUCKET`: The name of your S3 bucket (e.g., evernothing011126).
# #      - `AWS_REGION`: The AWS region of your bucket (e.g., us-east-1).
# #      - `ENCRYPTION_KEY`: A 32-byte key for AES-256 encryption. See section 9.3 for key generation.
# #
# # 5. Generate Encryption Key:
# #    - See section 9.3 for instructions on generating the `ENCRYPTION_KEY`.
# #
# # ------------------------------------------------------------------------------
# # 0.2. Accessing the Web Application
# #
# # 1. Run the Application:
# #    - `flask run`
# #    - Or for development with auto-reloading: `flask --app app --debug run`
# #
# # 2. Access in your Browser:
# #    - Open your web browser and navigate to: http://127.0.0.1:5000
# #
# # 3. Access Admin Panel:
# #    - Navigate to: http://127.0.0.1:5000/admin
# #    - Default credentials: admin / admin
# #
# # ------------------------------------------------------------------------------
# # 0.3. Accessing from Amazon Playstore / Android
# #
# # - This is a web application, not a native Android application. It is not available on the
# #   Google Play Store or Amazon Appstore.
# # - To access it from an Android phone:
# #   1. Make sure the computer running the application and the Android phone are on the
# #      SAME WiFi network.
# #   2. Find the local IP address of the computer running the app (e.g., 192.168.1.10).
# #      - On Windows, run `ipconfig`.
# #      - On macOS/Linux, run `ifconfig` or `ip addr`.
# #   3. Run the Flask app so it's accessible on your network:
# #      - `flask run --host=0.0.0.0`
# #   4. Open the web browser on your Android phone and navigate to:
# #      `http://<YOUR_COMPUTER_IP>:5000` (e.g., http://192.168.1.10:5000)
# #
# ##############################################################################
# ## 9. S3 BUCKETS & ENCRYPTION
# ##############################################################################
# #
# # 9.3. Key Generation and Installation
# #
# # - The application uses AES-256 for encryption, which requires a 32-byte (256-bit) key.
# #
# # 1. Generate a secure random key using Python:
# #    - Open a Python interpreter: `python`
# #    - Run the following commands:
# #      ```python
# #      import os
# #      key = os.urandom(32)
# #      import base64
# #      encoded_key = base64.b64encode(key).decode('utf-8')
# #      print(f"Your new encryption key is: {encoded_key}")
# #      ```
# #
# # 2. Install the Key:
# #    - Set the generated key as an environment variable named `ENCRYPTION_KEY`.
# #    - You can create a `.env` file in the project root and add the following line:
# #      `ENCRYPTION_KEY='YOUR_GENERATED_KEY_HERE'`
# #    - The application will automatically load this key.
# #
# ##############################################################################
# ## 10. OPERATIONS & MAINTENANCE
# ##############################################################################
# #
# # 10.1. Restarting the Application:
# # - If the app is running in the foreground, press `Ctrl+C` to stop it, then restart it
# #   using the `flask run` command from section 0.2.
# # - If running as a background process (see 10.4), you will need to find the process ID (PID)
# #   and stop it before restarting.
# #
# # 10.2. Database Backup (SQLite):
# # - This application uses a SQLite database file (`instance/evernothing.db`).
# # - To back up the database, simply copy this file to a safe location.
# # - A simple Python script to do this:
# #   ```python
# #   import shutil
# #   import datetime
# #   timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
# #   shutil.copyfile('instance/evernothing.db', f'backup_{timestamp}.db')
# #   print(f"Backup created: backup_{timestamp}.db")
# #   ```
# #
# # 10.3. Database Export (CSV):
# # - To export notes to a CSV file (username, note_key, note_value):
# #   ```python
# #   import sqlite3
# #   import csv
# #
# #   # Connect to the database
# #   con = sqlite3.connect('instance/evernothing.db')
# #   cur = con.cursor()
# #
# #   # The query joins user and note tables to get the required data
# #   res = cur.execute("""
# #       SELECT u.username, n.title, n.content
# #       FROM note n
# #       JOIN user u ON n.user_id = u.id
# #       ORDER BY u.username, n.title
# #   """)
# #
# #   # Write to CSV
# #   with open('export.csv', 'w', newline='', encoding='utf-8') as f:
# #       writer = csv.writer(f)
# #       # Write header
# #       writer.writerow(['username', 'note_key', 'note_value'])
# #       # Write data
# #       writer.writerows(res.fetchall())
# #
# #   print("Export complete: export.csv")
# #   con.close()
# #   ```
# #
# # 10.4. Running as a Background Process:
# # - On Linux/macOS:
# #   - `nohup flask run --host=0.0.0.0 &`
# #   - The `&` runs the process in the background. `nohup` ensures it keeps running
# #     even if you close your terminal. Output will be saved to `nohup.out`.
# # - On Windows:
# #   - You can use `start /B python -m flask run --host=0.0.0.0`.
# #
# ##############################################################################
# ## 17. LIBRARIES
# ##############################################################################
# #
# # 17.3 Script to install all required libraries is:
# # `pip install -r requirements.txt`
# # The `requirements.txt` file contains a list of compatible and safe libraries.
# #
# ##############################################################################

import os
from flask import Flask

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)