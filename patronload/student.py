#!/usr/bin/python3
# -*- coding: utf-8 -*-

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import ast
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from dateutil.relativedelta import relativedelta

import cx_Oracle

sys.path.append("..")
from llama import CONFIG


def xstr(s):
    """Return an empty string if the type is NoneType

    This avoids error when we're looking for a string throughout the script

    :param s: an object to be checked if it is NoneType
    """

    if s is None:
        return ""
    return str(s)


def phone_format(n):
    if n is None:
        return ""
    return re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", n)


# make some dates for later
six_months = date.today() + relativedelta(months=+6)
two_years = six_months + relativedelta(years=+2)

# Start import student departments #
file = open("student_departments.txt", "r")

contents = file.read()
departments = ast.literal_eval(contents)

file.close()

# End import student departments #
student_reject = open("rejects_students_script.txt", "w")

dsn = cx_Oracle.makedsn(
    CONFIG.DATA_WAREHOUSE_HOST, CONFIG.DATA_WAREHOUSE_PORT, CONFIG.DATA_WAREHOUSE_SID
)

connection = cx_Oracle.connect(
    CONFIG.DATA_WAREHOUSE_USER,
    CONFIG.DATA_WAREHOUSE_PASSWORD,
    dsn,
)
cursor = connection.cursor()
cursor.execute(
    """
        SELECT
            MIT_ID,
            LAST_NAME,
            FIRST_NAME,
            MIDDLE_NAME,
            TERM_STREET1,
            TERM_STREET2,
            TERM_STREET3,
            TERM_CITY,
            TERM_STATE,
            TERM_ZIP,
            TERM_PHONE1,
            TERM_PHONE2,
            OFFICE_LOCATION,
            OFFICE_PHONE,
            STUDENT_YEAR,
            EMAIL_ADDRESS,
            KRB_NAME_UPPERCASE,
            HOME_DEPARTMENT,
            LIBRARY_ID
        FROM
            LIBRARY_STUDENT
        """
)
# WHERE rownum <= 5
# WHERE MIT_ID='929058407'

res = cursor.fetchall()

# BEGIN get list of column names from oracle
col_name = []
for i in range(0, len(cursor.description)):
    col_name.append(cursor.description[i][0])
    # print (str(i) + ": " + cursor.description[i][0])

# END get list of column names from oracle

student_reject.write(
    col_name[0]
    + "|"
    + col_name[1]
    + "|"
    + col_name[2]
    + "|"
    + col_name[3]
    + "|"
    + col_name[4]
    + "|"
    + col_name[5]
    + "|"
    + col_name[6]
    + "|"
    + col_name[7]
    + "|"
    + col_name[8]
    + "|"
    + col_name[9]
    + "|"
    + col_name[10]
    + "|"
    + col_name[11]
    + "|"
    + col_name[12]
    + "|"
    + col_name[13]
    + "|"
    + col_name[14]
    + "|"
    + col_name[15]
    + "|"
    + col_name[16]
    + "|"
    + col_name[17]
    + "|"
    + col_name[18]
    + "\n"
)

student = []

# skip if there is no MIT ID or EMAIL
for row in res:
    if row[16]:
        user = {
            col_name[0]: row[0],
            col_name[1]: xstr(row[1]),
            col_name[2]: xstr(row[2]),
            col_name[3]: xstr(row[3]),
            col_name[4]: xstr(row[4]),
            col_name[5]: xstr(row[5]),
            col_name[6]: xstr(row[6]),
            col_name[7]: xstr(row[7]),
            col_name[8]: xstr(row[8]),
            col_name[9]: xstr(row[9]),
            col_name[10]: xstr(row[10]),
            col_name[11]: xstr(row[11]),
            col_name[12]: xstr(row[12]),
            col_name[13]: xstr(row[13]),
            col_name[14]: xstr(row[14]),
            col_name[15]: xstr(row[15]),
            col_name[16]: xstr(row[16]),
            col_name[17]: xstr(row[17]),
            col_name[18]: xstr(row[18]),
        }
        student.append(user)
    else:
        student_reject.write(
            xstr(row[0])
            + "|"
            + xstr(row[1])
            + "|"
            + xstr(row[2])
            + "|"
            + xstr(row[3])
            + "|"
            + xstr(row[4])
            + "|"
            + xstr(row[5])
            + "|"
            + xstr(row[6])
            + "|"
            + xstr(row[7])
            + "|"
            + xstr(row[8])
            + "|"
            + xstr(row[9])
            + "|"
            + xstr(row[10])
            + "|"
            + xstr(row[11])
            + "|"
            + xstr(row[12])
            + "|"
            + xstr(row[13])
            + "|"
            + xstr(row[14])
            + "|"
            + xstr(row[15])
            + "|"
            + xstr(row[16])
            + "|"
            + xstr(row[17])
            + "|"
            + xstr(row[18])
            + "\n"
        )

cursor.close()
connection.close()

for i in range(0, len(student)):
    patron = student[i]
    patron_file = "STUDENT/" + patron["MIT_ID"] + ".xml"

    # import student record template #
    tree = ET.parse("student_template.xml")

    fname = patron["FIRST_NAME"]

    if patron["MIDDLE_NAME"]:
        fname += " " + patron["MIDDLE_NAME"]

    fname += " " + patron["LAST_NAME"]

    root = tree.getroot()
    for primary_id in root.iter("primary_id"):
        primary = ""
        if patron["KRB_NAME_UPPERCASE"]:
            primary = patron["KRB_NAME_UPPERCASE"] + "@MIT.EDU"
        else:
            primary = patron["EMAIL_ADDRESS"]
        primary_id.text = primary
    # for full_name in root.iter('full_name'):
    #    full_name.text = fname.strip()

    for first_name in root.iter("first_name"):
        first_name.text = patron["FIRST_NAME"]

    for middle_name in root.iter("middle_name"):
        middle_name.text = patron["MIDDLE_NAME"]

    for last_name in root.iter("last_name"):
        last_name.text = patron["LAST_NAME"]

    for expiry_date in root.iter("expiry_date"):
        # print(expiry_date.text)
        expiry_date.text = six_months.strftime("%Y-%m-%d") + "Z"

    for purge_date in root.iter("purge_date"):
        # print(purge_date.text)
        purge_date.text = two_years.strftime("%Y-%m-%d") + "Z"

    for contact_info in root.iter("contact_info"):
        addresses = contact_info.find("addresses")
        if patron["TERM_STREET1"]:
            addresses[0][0].text = patron["TERM_STREET1"]
        else:
            addresses[0][0].text = "NO ADDRESS ON FILE IN DATA WAREHOUSE"
        addresses[0][1].text = patron["TERM_STREET2"]
        addresses[0][2].text = patron["TERM_CITY"]
        addresses[0][3].text = patron["TERM_STATE"]
        addresses[0][4].text = patron["TERM_ZIP"]

        emails = contact_info.find("emails")
        if patron["EMAIL_ADDRESS"]:
            emails[0][0].text = patron["EMAIL_ADDRESS"]
        else:
            ems = emails.findall("email")
            for em in ems:
                emails.remove(em)

        phones = contact_info.find("phones")
        if patron["OFFICE_PHONE"] and patron["TERM_PHONE1"]:
            phones[0][0].text = phone_format(patron["OFFICE_PHONE"])
            phones[1][0].text = phone_format(patron["TERM_PHONE1"])
        elif patron["OFFICE_PHONE"]:
            phones[0][0].text = phone_format(patron["OFFICE_PHONE"])
        elif patron["TERM_PHONE1"]:
            phones[0][0].text = phone_format(patron["TERM_PHONE1"])
        elif patron["TERM_PHONE2"]:
            phones[0][0].text = phone_format(patron["TERM_PHONE2"])
        tels = phones.findall("phone")
        for tel in tels:
            pn = tel.findall("phone_number")
            if not pn[0].text:
                phones.remove(tel)

    for user_identifiers in root.iter("user_identifiers"):
        # for user_identifier in user_identifiers.find("user_identifier"):
        for user_identifier in user_identifiers:
            id_type = user_identifier.findall("id_type")
            type = id_type[0]
            id_value = user_identifier.findall("value")
            value = id_value[0]

            if type.text == "02":
                value.text = patron["MIT_ID"]
            elif type.text == "01":
                if patron["LIBRARY_ID"] and patron["LIBRARY_ID"] != "NONE":
                    value.text = patron["LIBRARY_ID"]
                else:
                    user_identifiers.remove(user_identifier)

    for user_statistic in root.iter("user_statistic"):
        if user_statistic[1].text == "DEPT":
            if patron["HOME_DEPARTMENT"] in departments:
                user_statistic[0].text = departments[patron["HOME_DEPARTMENT"]]
            else:
                user_statistic[0].text = "ZZ"
                # sys.stderr.write("Unknown dept: " +
                #                 patron["HOME_DEPARTMENT"] + "\n")

    for user_group in root.iter("user_group"):
        status = ""
        if re.search("^[1234Uu]$", patron["STUDENT_YEAR"]):
            status = "31"
        elif re.search("^[Gg]$", patron["STUDENT_YEAR"]):
            status = "32"

        if re.search("^NI[UVWTRH]$", patron["HOME_DEPARTMENT"]):
            status = "54"

        user_group.text = status

    tree.write(patron_file, encoding="UTF-8", xml_declaration=False)


# __END__

# Here are the Oracle columns for reference #
#
# MIT_ID    0
# LAST_NAME    1
# FIRST_NAME    2
# MIDDLE_NAME    3
# TERM_STREET1    4
# TERM_STREET2    5
# TERM_STREET3    6
# TERM_CITY    7
# TERM_STATE    8
# TERM_ZIP    9
# TERM_PHONE1    10
# TERM_PHONE2    11
# OFFICE_LOCATION    12
# OFFICE_PHONE    13
# STUDENT_YEAR    14
# EMAIL_ADDRESS    15
# KRB_NAME_UPPERCASE    16
# HOME_DEPARTMENT    17
# LIBRARY_ID    18
