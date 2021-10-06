# Functions for Alma Invoice/SAP scripts
import json
from urllib.request import urlopen


def xstr(this_string):
    """Return an empty string if the type is NoneType

    This avoids error when we're looking for a string throughout the script

    :param s: an object to be checked if it is NoneType
    """

    if this_string is None:
        return ''
    return str(this_string)


def get_values_as_dict(line, slices):
    """Utility function to handle fixed length format file used by SAP"""
    values = {}
    key_list = {key.split("_")[0] for key in slices.keys()}
    for key in key_list:
        values[key] = line[slices[key+"_start"]:slices[key+"_end"]].strip()
    return values


def extract_vendor(json):
    try:
        return (json['vendor']['value'])
    except KeyError:
        return 0


CFILE = {
            'bytes_start': 0,
            'bytes_end': 16,
            'records_start': 16,
            'records_end': 32,
            'credit_start': 32,
            'credit_end': 52,
            'debit_start': 52,
            'debit_end': 72,
            'ctl3_start': 72,
            'ctl3_end': 92,
            'ctl4_start': 92,
            'ctl4_end': 112
         }


DFILE = {
            'type_start': 0,
            'type_end': 1,
            'docdate_start': 1,
            'docdate_end': 9,
            'basedate_start': 9,
            'basedate_end': 17,
            'extref_start': 17,
            'extref_end': 33,
            'vtype_start': 33,
            'vtype_end': 37,
            'vacct_start': 37,
            'vacct_end': 43,
            'amount_start': 43,
            'amount_end': 59,
            'sign_start': 59,
            'sign_end': 60,
            'method_start': 60,
            'method_end': 61,
            'supplement_start': 61,
            'supplement_end': 63,
            'terms_start': 63,
            'terms_end': 67,
            'block_start': 67,
            'block_end': 68,
            'payee_start': 68,
            'payee_end': 69,
            'vname_start': 69,
            'vname_end': 104,
            'vcity_start': 104,
            'vcity_end': 139,
            'vline2_start': 139,
            'vline2_end': 174,
            'pobox_start': 174,
            'pobox_end': 175,
            'street_start': 175,
            'street_end': 210,
            'zip_start': 210,
            'zip_end': 220,
            'region_start': 220,
            'region_end': 223,
            'country_start': 223,
            'country_end': 226,
            'text_start': 226,
            'text_end': 276,
            'vline3_start': 276,
            'vline3_end': 311
         }
