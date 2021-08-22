#Scripts for loading patrons into Alma from the MIT Data Warehouse. 

*More documentation coming soon!*

##What's here?
1. Directories:
    - **STAFF** Directory where generated staff XML files are stored for processing
    - **STUDENT** Directory where generated student XML files are stored for processing
    - **scripts** Currently some Perl scripts for packing up the XML files in a format suitable for Alma. *the scripts will be rewritten in Python*
2. Main Scripts
    These two do almost all of the heavy lifting. They pull data from the DW and create Alma patron XML files.
    - **staff.py**
    - **student.py**
3. Utility files
    - `patron.config.dist`  stripped config file where secret stuff would go
    - `staff_template.xml`  [mostly] blank template file for patron type staff
    - `student_template.xml` [mostly] blank template file for patron type student
    - `staff_departments.txt` list of departments for staff
    - `student_departments.txt` list of departments from students

