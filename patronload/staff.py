# -*- coding: utf-8 -*-
import cx_Oracle
import ast
# import sys
import re
import xml.etree.ElementTree as ET
from datetime import date
# from datetime import timedelta
from dateutil.relativedelta import relativedelta
import configparser

config = configparser.ConfigParser()
config.read('patron.config')
dw = config['DW']


def xstr(s):
    """Return an empty string if the type is NoneType

    This avoids error when we're looking for a string throughout the script

    :param s: an object to be checked if it is NoneType
    """

    if s is None:
        return ''
    return str(s)


def phone_format(n):
    """Return a pretty phone format

    The data warehouse send back 1234567890
    we want 123-456-7890

    :param n: a ten digit number to parse
    """

    if n is None:
        return ''
    return re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1-\2-\3', n)


# make some dates for later
six_months = date.today() + relativedelta(months=+6)
two_years = six_months + relativedelta(years=+2)

# Start import staff departments #
file = open("staff_departments.txt", "r")

contents = file.read()
departments = ast.literal_eval(contents)

file.close()

# End import staff departments #

staff_rejects = open("STAFF_REJECTS/staff_rejects_full.txt", "w")
staff_no_barcode = open("STAFF_REJECTS/staff_no_barcode.txt", "w")
staff_no_email = open("STAFF_REJECTS/staff_no_email.txt", "w")
staff_no_phone = open("STAFF_REJECTS/staff_no_phone.txt", "w")
staff_no_addr = open("STAFF_REJECTS/staff_no_addr.txt", "w")
staff_no_email_no_krb = open("STAFF_REJECTS/staff_no_email_no_krb.txt", "w")
staff_no_email_yes_krb = open("STAFF_REJECTS/staff_no_email_yes_krb.txt", "w")

# Start Oracle data import #

# Connect as user "LIBUSER" to the "WAREHOUSE.WORLD" as defined in the tns.ora
connection = cx_Oracle.connect(dw['user'], dw['password'], "WAREHOUSE.WORLD")
cursor = connection.cursor()
cursor.execute("""
        SELECT *
        FROM LIBRARY_EMPLOYEE
       """)
#        WHERE rownum <= 10

res = cursor.fetchall()

# get list of column names from oracle
col_name = []
for i in range(0, len(cursor.description)):
    col_name.append(cursor.description[i][0])

staff_rejects.write(xstr(col_name[0]) + '|' +
                    col_name[1] + '|' +
                    col_name[2] + '|' +
                    col_name[3] + '|' +
                    col_name[4] + '|' +
                    col_name[5] + '|' +
                    col_name[6] + '|' +
                    col_name[7] + '|' +
                    col_name[8] + '|' +
                    col_name[9] + '|' +
                    col_name[10] + '|' +
                    col_name[11] + '|' +
                    col_name[12] + '|' +
                    col_name[13] + "\n")


# create a list of dictionaries for staff data
staff = []
for row in res:
    if (row[6]):
        # purge = row[5]
        # purge += timedelta(days=365)
        # purge += timedelta(days=365)
        # note the use of row[5].strftime('%Y-%m-%d') (APPOINTMENT_END_DATE)
        # to get a real date we can use
        user = {col_name[0]: xstr(row[0]).decode("utf-8",
                                                 errors="backslashreplace"),
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
                col_name[13]: xstr(row[13])}
        staff.append(user)
    else:
        end_date = 'Unknown'
        if row[5]:
            end_date = row[5].strftime('%Y-%m-%d')
        # print (end_date + '|' + xstr(row[3]) + "|" + xstr(row[0]))
        if row[3] and (xstr(row[4]) == ''):
            staff_no_email.write(row[3] + "\n")
            if row[6]:
                staff_no_email_yes_krb.write(row[3] + "\t" +
                                             row[6] + "\t" +
                                             end_date + "\n")
            else:
                staff_no_email_no_krb.write(row[3] + "\t" +
                                            end_date + "\n")

        staff_rejects.write(xstr(row[0]) + '|' +
                            xstr(row[1]) + '|' +
                            xstr(row[2]) + '|' +
                            xstr(row[3]) + '|' +
                            xstr(row[4]) + '|' +
                            end_date + '|' +
                            xstr(row[6]) + '|' +
                            xstr(row[7]) + '|' +
                            xstr(row[8]) + '|' +
                            xstr(row[9]) + '|' +
                            xstr(row[10]) + '|' +
                            xstr(row[11]) + '|' +
                            xstr(row[12]) + '|' +
                            xstr(row[13]) + "\n")
cursor.close()
connection.close()

for i in range(0, len(staff)):
    patron = staff[i]
    patron_file = 'STAFF/' + patron["MIT_ID"] + '.xml'

    # print (patron["APPOINTMENT_END_DATE"] +
    #        "|" + patron["MIT_ID"] +
    #        "|" + patron["FULL_NAME"])

    # import staff record template #
    tree = ET.parse('staff_template.xml')
    root = tree.getroot()
    for primary_id in root.iter('primary_id'):
        primary = ''
        if patron["KRB_NAME_UPPERCASE"]:
            primary = patron["KRB_NAME_UPPERCASE"] + '@MIT.EDU'
        else:
            primary = patron["EMAIL_ADDRESS"]
        primary_id.text = primary
    # for full_name in root.iter('full_name'):
    #    full_name.text = patron["FULL_NAME"]
    name_split = re.split(",",  patron["FULL_NAME"], 1)
    for last_name in root.iter('last_name'):
        last_name.text = name_split[0].strip()
    for first_name in root.iter('first_name'):
        first_name.text = name_split[1].strip()
    for expiry_date in root.iter('expiry_date'):
        # print(expiry_date.text)
        # expiry_date.text = patron["APPOINTMENT_END_DATE"] + 'Z'
        expiry_date.text = six_months.strftime('%Y-%m-%d') + 'Z'
    for purge_date in root.iter('purge_date'):
        # print(purge_date.text)
        # purge_date.text = patron["PURGE"] + 'Z'
        purge_date.text = two_years.strftime('%Y-%m-%d') + 'Z'
    for user_group in root.iter('user_group'):
        # print(purge_date.text)
        user_group.text = patron["LIBRARY_PERSON_TYPE_CODE"]
        user_group.set('desc', patron["LIBRARY_PERSON_TYPE"])

    for user_identifiers in root.iter('user_identifiers'):
        # for user_identifier in user_identifiers.find("user_identifier"):
        for user_identifier in user_identifiers:
            id_type = user_identifier.findall("id_type")
            type = id_type[0]
            id_value = user_identifier.findall("value")
            value = id_value[0]

            if type.text == '02':
                value.text = patron["MIT_ID"]
            elif type.text == '01':
                if patron["LIBRARY_ID"] and patron["LIBRARY_ID"] != 'NONE':
                    value.text = patron["LIBRARY_ID"]
                else:
                    staff_no_barcode.write(patron["MIT_ID"] + "\n")
                    user_identifiers.remove(user_identifier)

    for contact_info in root.iter('contact_info'):
        addresses = contact_info.find("addresses")
        if patron["OFFICE_ADDRESS"]:
            addresses[0][0].text = patron["OFFICE_ADDRESS"]
        else:
            addresses[0][0].text = 'NO ADDRESS ON FILE IN DATA WAREHOUSE'
            staff_no_addr.write(patron["MIT_ID"] + "\n")
        if patron["EMAIL_ADDRESS"]:
            emails = contact_info.find("emails")
            emails[0][0].text = patron["EMAIL_ADDRESS"]
        phones = contact_info.find("phones")
        if patron["OFFICE_PHONE"]:
            phones[0][0].text = phone_format(patron["OFFICE_PHONE"])
        else:
            staff_no_phone.write(patron["MIT_ID"] + "\n")
            tels = phones.findall('phone')
            for tel in tels:
                phones.remove(tel)
    for user_statistic in root.iter('user_statistic'):
        if user_statistic[1].text == 'DEPT':
            if patron["ORG_UNIT_ID"] in departments:
                user_statistic[0].text = departments[patron["ORG_UNIT_ID"]]
            else:
                user_statistic[0].text = 'ZQ'
                # sys.stderr.write("Unknown dept: " +
                #                  patron["ORG_UNIT_ID"] + "\n")
            if patron["ORG_UNIT_TITLE"]:
                user_statistic[0].set('desc', patron["ORG_UNIT_TITLE"])
            else:
                user_statistic[0].set('desc', 'Unknown')

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
