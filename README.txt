==================================================
  NCAT Registration System - Setup Instructions
==================================================

This project is a Python + MySQL-based student registration system
built with object-oriented programming (OOP) principles.
This project is 100% complete based on the requirements in the instructions. 


 Works for both macOS and Windows
 Uses MySQL as the database backend
 Uses Python 3 with mysql-connector

--------------------------------------------------
1. INSTALL REQUIREMENTS
--------------------------------------------------

1.1 ➜ Make sure you have Python 3 installed:

   macOS:
      Open Terminal and run:
         python3 --version

   Windows:
      Open Command Prompt and run:
         python --version

   If not installed, download from:
      https://www.python.org/downloads/


1.2 ➜ Install a Code Editor (IDE)

   - We recommend using Visual Studio Code (VS Code) to run and edit the Python application.

     ➤ Download VS Code:
        https://code.visualstudio.com/

   - Once installed, open the project folder in VS Code.

   - (Optional) Install the "Python" extension in VS Code for syntax highlighting and code support.

   - You may also use other IDEs such as PyCharm, Thonny, or IDLE if preferred.


1.3 ➜ Install the MySQL Connector:

   macOS:
      Open Terminal and run:
         python3 -m ensurepip --upgrade
         python3 -m pip install mysql-connector-python

   Windows:
      Open Command Prompt and run:
         python -m ensurepip --upgrade
         python -m pip install mysql-connector-python


1.4 ➜ Make sure MySQL Server is installed and running:

   - Download MySQL Community Server from:
     https://dev.mysql.com/downloads/mysql/

   - Make sure the MySQL Workbench app is also installed.

   - Start your MySQL server to store the database (on macOS, use Homebrew or System Prefs)


--------------------------------------------------
2. SET UP THE DATABASE
--------------------------------------------------

2.1 ➜ Open MySQL Workbench

2.2 ➜ Add and run the .sql codes given in the zip file to complete the following:

   1. Create the NCAT database
   2. Create all necessary tables
   3. Create the AggieAdmin user
   4. Grant access privileges

NCATschema.sql will: 
   ➤ Create the NCAT database schema if it does not already exist.
   ➤ Set the NCAT schema as the active database for all future operations.
   ➤ This is the foundational setup required before running any other SQL files that create tables, insert data, or define users.


AggieAdminUser.sql will create the following login:
   ➤ Username: AggieAdmin
   ➤ Password: AggiePride
   ➤ Allows the AggieAdmin user to manage tables, users, and perform all operations required by the Python application.

Major.sql will:
   ➤ Create the `Major` table to store academic majors (e.g., Computer Science, Biology).
   ➤ Insert sample majors that students can be linked to when created.

Roles.sql will:
   ➤ Create the `Roles` table with role identifiers (e.g., 'mgr' for Manager, 'stu' for Student).
   ➤ Used to distinguish between user types in the application.

Roster.sql will:
   ➤ Create the `Roster` table which stores classes offered (e.g., Python Programming).
   ➤ Each class has an ID, class name, and course code.

Rosterclass.sql will:
   ➤ Create the `Rosterclass` junction table that connects students to classes.
   ➤ Enables many-to-many relationships between users (students) and courses (roster).
   ➤ Tracks enrollments.

Users.sql will:
   ➤ Create the `Users` table to store login and profile info for both students and managers.
   ➤ Columns include username, password, roleID, first/last name, and major.
   ➤ This is the central user database accessed during login.

Classes.sql will:
   ➤ Insert sample data into the `Roster` table (e.g., Database Systems, Software Engineering).
   ➤ Provides initial course options so students can be assigned immediately after creation.

--------------------------------------------------
3. RUN THE PROGRAM
--------------------------------------------------

3.1 ➜ Startup your preferred IDE and open the folder made from decompressing the zip:

3.2 ➜ Select the "Final Project" python file and run the program to start:
         ➤ FinalProject.py

3.3 ➜ The application will automatically connect you to the database as an AggieAdmin through the mysql-connector

3.4 ➜ Login info:

1. Manager: Application Login
   ➤ Manager:
      Username: Manager1
      Password: AggiePride1

   ➤ Manager Menu: Option 1
      View a student's schedule.
      - Enter a student's username to see the list of classes they are currently enrolled in.

   ➤ Manager Menu: Option 2
      View the full class roster.
      - Displays all students assigned to each class in the system.

   ➤ Manager Menu: Option 3
      Add student to class.
      - Choose a student and assign them to an available class from the list.

   ➤ Manager Menu: Option 4
      Drop student from class.
      - Remove a student from a selected class they are currently enrolled in.

   ➤ Manager Menu: Option 5
      Add new student.
      - Create a new student profile, including unique login credentials and personal info.
      - After creation, you will be given the option to immediately assign them to one or more classes.

   ➤ Manager Menu: Option 6 (Extra Option)
      Ban student from school.
      - Select a student to permanently remove from the system.
      - Choose a reason for banning (cheating, attendance, GPA), then confirm.
      - Student is fully deleted from both the roster and user tables.

   ➤ Manager Menu: Option 7
      Exit.
      - Return to the login screen or close the application.


2. Student: Application Login    
   ➤ Student:
      Username: Student1
      Password: AggiePride2

   ➤ Student Menu: Option 1
      View your classes.
      - Displays a list of all classes the logged-in student is currently enrolled in.

   ➤ Student Menu: Option 2
      Drop a class.
      - Allows the student to remove themselves from a selected class.

   ➤ Student Menu: Option 3
      Quit School.
      - Displays a confirmation message.
      - If confirmed, the student's profile and enrollment records are permanently removed from the system.

   ➤ Student Menu: Option 4
      Exit.
      - Returns to the login screen or closes the application.

--------------------------------------------------
4. VIDEO DEMONSTRATION
--------------------------------------------------

This is a text description of the steps used in the video demonstration will walk through every major feature of the NCAT Registration System to verify its functionality.

Each step below will be shown in order:

1.  ➤ Start the program by running the Python script.

2.  ➤ Attempt invalid login:
      - Run the program and enter incorrect login information (e.g., wrong username or password).
      - Do this 3 times in a row.
      - Confirm the system automatically exits and displays the message:
           ❌ Too many failed login attempts. Terminating application.

3.  ➤ Login using the Manager account:
      - Username: Manager1
      - Password: AggiePride1
      - Confirm that the entire Manager menu is visible.
      - Exit the Manager menu.

4.  ➤ Run the program again and login as a Student:
      - Username: Student1
      - Password: AggiePride2
      - Confirm that the entire Student menu is visible.
      - Exit the Student menu.

5.  ➤ Login again as Manager:
      - Use the "Add student to class" option to assign Student1 to a class.
      - Then go through the following Manager menu options:
         - View a student’s schedule
         - View full class roster
      - Do not use options to add new student, drop student, or ban student in this step.
      - Exit the Manager menu.

6.  ➤ Login again as Student1:
      - Use the option to view class schedule.
      - Confirm that class enrollment appears correctly.
      - Exit the Student menu.

7.  ➤ Login again as Manager:
      - Use the "Drop student from class" option to remove Student1 from a class.
      - Make sure the output shows the student was removed.
      - Immediately reassign that same student to a different class.
      - Exit the Manager menu.

8.  ➤ Login again as Student1:
      - Use the "Drop a class" option.
      - Confirm the class is successfully dropped with visible output.
      - Exit the Student menu.

9.  ➤ Login again as Manager:
      - Use the "Add new student" option to create a new student.
      - Assign them to a class after the creation step.
      - Repeat this twice to add both of the new students to a class.
      - Use the "View full class roster" option to confirm both students were added.
      - Use the "Ban a student" option to permanently remove one of the newly added students.
      - Choose a reason for banning and confirm the action.
      - Use "View full class roster" again to confirm the student is no longer listed.
      - Exit the Manager menu.

10. ➤ Login using the other valid student’s credentials:
      - Show that the student menu is available using unique credentials
      - Show that the student is actually in the class roster in the student menu.
      - Exit the Student menu

11. ➤ Login as the Manager:
      - Use the "Ban Student" option to permanetely remove the other created student.
      - Show that the student has been removed.
   
12. ➤ Attempt to login using the banned student’s credentials:
      - Attempt the login twice (should fail both times).
      - Login as Student1.

13. ➤ While logged in as Student1, choose the "Quit School" option:
      - Attempt to login twice to show the student has been removed from the system.
      - Login as the Manager

14. ➤ While logged in as the Manager, choose the "View full class roster" option:
      - Confirm the final roster reflects the previous removals.
      - Exit the Manager menu — END of demonstration.

