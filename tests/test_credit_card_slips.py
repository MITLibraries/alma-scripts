import boto3
from defusedxml import ElementTree as ET
from moto import mock_ses

from llama import credit_card_slips


def test_create_credit_card_slips(mocked_alma, mocked_alma_env_vars, alma_json_headers):
    credit_card_slips_xml_string = credit_card_slips.create_credit_card_slips(
        "2021-05-13"
    )
    credit_card_slips_xml = ET.fromstring(credit_card_slips_xml_string)
    assert credit_card_slips_xml.find('.//td[@class="poline"]').text == "POL-123"


def test_create_dict_from_po_line_record_all_fields(
    mocked_alma,
    mocked_alma_env_vars,
    alma_json_headers,
    po_line_record_all_fields,
):
    value_dict = credit_card_slips.create_dict_from_po_line_record(
        po_line_record_all_fields, alma_json_headers
    )
    assert value_dict["account_1"] == "456"
    assert "account_2" not in value_dict
    assert value_dict["cardholder"] == "abc"
    assert value_dict["invoice_num"] == "Invoice #: 210513BOO"
    assert value_dict["item_title"] == "Book title"
    assert value_dict["poline"] == "POL-123"
    assert value_dict["price"] == "$12.00"
    assert value_dict["vendor"] == "Corporation"


def test_create_dict_from_po_line_record_missing_fields(
    mocked_alma,
    mocked_alma_env_vars,
    alma_json_headers,
    po_line_record_missing_fields,
):
    value_dict_missing_fields = credit_card_slips.create_dict_from_po_line_record(
        po_line_record_missing_fields, alma_json_headers
    )
    assert value_dict_missing_fields["item_title"] == "Unknown title"
    assert value_dict_missing_fields["price"] == "$0.00"
    assert value_dict_missing_fields["invoice_num"] == "Invoice #: 210513UNK"
    assert value_dict_missing_fields["cardholder"] == "No cardholder note"


def test_create_dict_from_po_line_record_multiple_funds(
    mocked_alma,
    mocked_alma_env_vars,
    alma_json_headers,
    po_line_record_multiple_funds,
):
    value_dict_multiple_funds = credit_card_slips.create_dict_from_po_line_record(
        po_line_record_multiple_funds, alma_json_headers
    )
    assert value_dict_multiple_funds["account_2"] == "789"


def test_get_account_from_fund_code_with_fund_code(
    mocked_alma,
    mocked_alma_env_vars,
    alma_json_headers,
):
    account = credit_card_slips.get_account_from_fund_code("ABC", alma_json_headers)
    assert account == "456"


def test_get_account_from_fund_code_without_fund_code(
    alma_json_headers,
):
    account = credit_card_slips.get_account_from_fund_code("", alma_json_headers)
    assert account == "No fund code"


def test_get_cardholder_from_notes_with_cardholder_note(po_line_record_all_fields):
    cardholder = credit_card_slips.get_cardholder_from_notes(po_line_record_all_fields)
    assert cardholder == "abc"


def test_get_cardholder_from_notes_without_cardholder_note(
    po_line_record_missing_fields,
):
    cardholder = credit_card_slips.get_cardholder_from_notes(
        po_line_record_missing_fields
    )
    assert cardholder == "No cardholder note"


def test_get_po_title_with_title():
    po_rec_1 = {"resource_metadata": {"title": "Book title"}}
    assert credit_card_slips.get_po_title(po_rec_1) == "Book title"


def test_get_po_title_without_title():
    po_rec_2 = {"resource_metadata": {"title": None}}
    assert credit_card_slips.get_po_title(po_rec_2) == "Unknown title"


def test_load_xml_template():
    root = credit_card_slips.load_xml_template("config/credit_card_slip_template.xml")
    element_classes = [
        "vendor",
        "poline",
        "item_title",
        "price",
        "po_date",
        "invoice_num",
        "credit_memo_num",
        "account_1",
        "account_2",
        "cardholder",
    ]
    assert root.tag == "ccslip"
    for element_class in element_classes:
        assert root.find(f'.//td[@class="{element_class}"]') is not None


@mock_ses
def test_send_credit_card_slips_email():
    ses_client = boto3.client("ses", region_name="us-east-1")
    ses_client.verify_email_identity(EmailAddress="noreply@example.com")
    response = credit_card_slips.send_credit_card_slips_email(
        ses_client,
        "2021-08-09",
        "<html/>",
        "noreply@example.com",
        ["test@example.com"],
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
