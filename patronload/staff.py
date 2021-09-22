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
from llama.ssm import SSM


ssm = SSM()
data_warehouse_user = ssm.get_parameter_value(
    "/apps/alma-sftp/ALMA_PROD_DATA_WAREHOUSE_USER"
)
data_warehouse_password = ssm.get_parameter_value(
    "/apps/alma-sftp/ALMA_PROD_DATA_WAREHOUSE_PASSWORD"
)
data_warehouse_host = ssm.get_parameter_value(
    "/apps/alma-sftp/ALMA_PROD_DATA_WAREHOUSE_HOST"
)
data_warehouse_port = ssm.get_parameter_value(
    "/apps/alma-sftp/ALMA_PROD_DATA_WAREHOUSE_PORT"
)
data_warehouse_sid = ssm.get_parameter_value(
    "/apps/alma-sftp/ALMA_PROD_DATA_WAREHOUSE_SID"
)


def xstr(s):
    """Return an empty string if the type is NoneType

    This avoids error when we're looking for a string throughout the script

    :param s: an object to be checked if it is NoneType
    """

    if s is None:
        return ""
    return str(s)


def phone_format(n):
    """Return a pretty phone format

    The data warehouse send back 1234567890
    we want 123-456-7890

    :param n: a ten digit number to parse
    """

    if n is None:
        return ""
    return re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", n)


# make some dates for later
six_months = date.today() + relativedelta(months=+6)
two_years = six_months + relativedelta(years=+2)

# Start import staff departments #
file = open("staff_departments.txt", "r")

contents = file.read()
departments = ast.literal_eval(contents)

file.close()

# End import staff departments #

staff_rejects = open("rejects_staff_script.txt", "w")

# Start Oracle data import #

# Connect to "WAREHOUSE.WORLD" as defined in the tns.ora
dsn = cx_Oracle.makedsn(data_warehouse_host, data_warehouse_port, data_warehouse_sid)

connection = cx_Oracle.connect(
    data_warehouse_user,
    data_warehouse_password,
    dsn,
)
cursor = connection.cursor()
cursor.execute(
    """
        SELECT *
        FROM LIBRARY_EMPLOYEE
       """
)
#        WHERE rownum <= 10

res = cursor.fetchall()

# get list of column names from oracle
col_name = []
for i in range(0, len(cursor.description)):
    col_name.append(cursor.description[i][0])

# print column headers for rejects file
staff_rejects.write(
    xstr(col_name[0])
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
    + "\n"
)


# create a list of dictionaries for staff data
staff = []
for row in res:
    if row[6]:
        # purge = row[5]
        # purge += timedelta(days=365)
        # purge += timedelta(days=365)
        # note the use of row[5].strftime('%Y-%m-%d') (APPOINTMENT_END_DATE)
        # to get a real date we can use
        user = {
            col_name[0]: xstr(row[0]),
            col_name[1]: xstr(row[1]),
            col_name[2]: xstr(row[2]),
            col_name[3]: xstr(row[3]),
            col_name[4]: xstr(row[4]),
            col_name[5]: row[5],
            col_name[6]: xstr(row[6]),
            col_name[7]: xstr(row[7]),
            col_name[8]: xstr(row[8]),
            col_name[9]: xstr(row[9]),
            col_name[10]: xstr(row[10]),
            col_name[11]: xstr(row[11]),
            col_name[12]: xstr(row[12]),
            col_name[13]: xstr(row[13]),
        }
        staff.append(user)
    else:
        end_date = "Unknown"
        if row[5]:
            end_date = row[5].strftime("%Y-%m-%d")

        staff_rejects.write(
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
            + end_date
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
            + "\n"
        )
cursor.close()
connection.close()

for i in range(0, len(staff)):
    patron = staff[i]
    patron_file = "STAFF/" + patron["MIT_ID"] + ".xml"

    # print (patron["APPOINTMENT_END_DATE"] +
    #        "|" + patron["MIT_ID"] +
    #        "|" + patron["FULL_NAME"])

    # import staff record template #
    tree = ET.parse("staff_template.xml")
    root = tree.getroot()
    for primary_id in root.iter("primary_id"):
        primary = ""
        if patron["KRB_NAME_UPPERCASE"]:
            primary = patron["KRB_NAME_UPPERCASE"] + "@MIT.EDU"
        else:
            primary = patron["EMAIL_ADDRESS"]
        primary_id.text = primary
    # for full_name in root.iter('full_name'):
    #    full_name.text = patron["FULL_NAME"]
    name_split = re.split(",", patron["FULL_NAME"], 1)
    for last_name in root.iter("last_name"):
        last_name.text = name_split[0].strip()
    for first_name in root.iter("first_name"):
        first_name.text = name_split[1].strip()
    for expiry_date in root.iter("expiry_date"):
        # print(expiry_date.text)
        # expiry_date.text = patron["APPOINTMENT_END_DATE"] + 'Z'
        expiry_date.text = six_months.strftime("%Y-%m-%d") + "Z"
    for purge_date in root.iter("purge_date"):
        # print(purge_date.text)
        # purge_date.text = patron["PURGE"] + 'Z'
        purge_date.text = two_years.strftime("%Y-%m-%d") + "Z"
    for user_group in root.iter("user_group"):
        # print(purge_date.text)
        user_group.text = patron["LIBRARY_PERSON_TYPE_CODE"]
        user_group.set("desc", patron["LIBRARY_PERSON_TYPE"])

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

    for contact_info in root.iter("contact_info"):
        addresses = contact_info.find("addresses")
        if patron["OFFICE_ADDRESS"]:
            addresses[0][0].text = patron["OFFICE_ADDRESS"]
        else:
            addresses[0][0].text = "NO ADDRESS ON FILE IN DATA WAREHOUSE"

        emails = contact_info.find("emails")
        if patron["EMAIL_ADDRESS"]:
            emails[0][0].text = patron["EMAIL_ADDRESS"]
        else:
            ems = emails.findall("email")
            for em in ems:
                emails.remove(em)

        phones = contact_info.find("phones")
        if patron["OFFICE_PHONE"]:
            phones[0][0].text = phone_format(patron["OFFICE_PHONE"])
        else:
            tels = phones.findall("phone")
            for tel in tels:
                phones.remove(tel)
    for user_statistic in root.iter("user_statistic"):
        if user_statistic[1].text == "DEPT":
            if patron["ORG_UNIT_ID"] in departments:
                user_statistic[0].text = departments[patron["ORG_UNIT_ID"]]
            else:
                user_statistic[0].text = "ZQ"
                # sys.stderr.write("Unknown dept: " +
                #                  patron["ORG_UNIT_ID"] + "\n")
            if patron["ORG_UNIT_TITLE"]:
                user_statistic[0].set("desc", patron["ORG_UNIT_TITLE"])
            else:
                user_statistic[0].set("desc", "Unknown")

    tree.write(patron_file, encoding="UTF-8", xml_declaration=False)

# End Oracle data import #
#
# Here are the Oracle columns for reference
#
# FULL_NAME    0
# OFFICE_ADDRESS    1
# OFFICE_PHONE    2
# MIT_ID    3
# EMAIL_ADDRESS    4
# APPOINTMENT_END_DATE    5
# KRB_NAME_UPPERCASE    6
# LIBRARY_PERSON_TYPE_CODE    7
# LIBRARY_PERSON_TYPE    8
# ORG_UNIT_ID    9
# ORG_UNIT_TITLE    10
# POSITION_TITLE    11
# DIRECTORY_TITLE    12
# LIBRARY_ID    13
