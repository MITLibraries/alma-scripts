from defusedxml import ElementTree as ET

from llama import credit_card_slips


def test_create_po_line_dict_all_fields(
    mocked_alma,
    mocked_alma_api_client,
    po_line_record_all_fields,
):
    po_line_dict = credit_card_slips.create_po_line_dict(
        mocked_alma_api_client,
        po_line_record_all_fields,
    )
    assert po_line_dict["account_1"] == "1234567-000001"
    assert "account_2" not in po_line_dict
    assert po_line_dict["cardholder"] == "abc"
    assert po_line_dict["invoice_num"] == "Invoice #: 210513BOO"
    assert po_line_dict["item_title"] == "Book title"
    assert po_line_dict["poline"] == "POL-123"
    assert po_line_dict["price"] == "$12.00"
    assert po_line_dict["quantity"] == "2"
    assert po_line_dict["vendor"] == "Corporation"


def test_create_po_line_dict_missing_fields(
    mocked_alma,
    mocked_alma_api_client,
):
    po_line_dict_missing_fields = credit_card_slips.create_po_line_dict(
        mocked_alma_api_client,
        {},
    )
    assert po_line_dict_missing_fields["vendor"] == "No vendor found"
    assert po_line_dict_missing_fields["poline"] == "No PO Line number found"
    assert po_line_dict_missing_fields["account_1"] == "No fund code found"
    assert po_line_dict_missing_fields["po_date"] == "No PO Line created date found"
    assert po_line_dict_missing_fields["item_title"] == "Unknown title"
    assert po_line_dict_missing_fields["price"] == "$0.00"
    assert po_line_dict_missing_fields["invoice_num"] == (
        "Invoice #: No PO Line created date foundUNK"
    )
    assert po_line_dict_missing_fields["quantity"] == "0"
    assert po_line_dict_missing_fields["cardholder"] == "No cardholder note found"


def test_create_po_line_dict_multiple_funds(
    mocked_alma,
    mocked_alma_api_client,
    po_line_record_multiple_funds,
):
    po_line_dict_multiple_funds = credit_card_slips.create_po_line_dict(
        mocked_alma_api_client,
        po_line_record_multiple_funds,
    )
    assert po_line_dict_multiple_funds["account_2"] == "1234567-000002"


def test_create_po_line_dict_spaces_in_title(
    mocked_alma,
    mocked_alma_api_client,
    po_line_record_spaces_in_title,
):
    po_line_dict_spaces_in_title = credit_card_slips.create_po_line_dict(
        mocked_alma_api_client,
        po_line_record_spaces_in_title,
    )
    assert po_line_dict_spaces_in_title["invoice_num"] == "Invoice #: 210513ATI"


def test_create_po_line_dicts(
    mocked_alma, mocked_alma_api_client, po_line_record_all_fields
):
    po_line_records = [po_line_record_all_fields]
    po_line_dicts = credit_card_slips.create_po_line_dicts(
        mocked_alma_api_client, po_line_records
    )
    for po_line_dict in po_line_dicts:
        assert po_line_dict["account_1"] == "1234567-000001"
        assert "account_2" not in po_line_dict
        assert po_line_dict["cardholder"] == "abc"
        assert po_line_dict["invoice_num"] == "Invoice #: 210513BOO"
        assert po_line_dict["item_title"] == "Book title"
        assert po_line_dict["poline"] == "POL-123"
        assert po_line_dict["price"] == "$12.00"
        assert po_line_dict["quantity"] == "2"
        assert po_line_dict["vendor"] == "Corporation"


def test_get_account_from_fund_code_with_fund_code(
    mocked_alma,
    mocked_alma_api_client,
):
    account = credit_card_slips.get_account_from_fund_code(
        mocked_alma_api_client, "ABC"
    )
    assert account == "1234567-000001"


def test_get_account_from_fund_code_without_fund_code(mocked_alma_api_client):
    account = credit_card_slips.get_account_from_fund_code(mocked_alma_api_client, None)
    assert account == "No fund code found"


def test_get_cardholder_from_notes_with_cardholder_note(
    po_line_record_all_fields,
):
    cardholder = credit_card_slips.get_cardholder_from_notes(po_line_record_all_fields)
    assert cardholder == "abc"


def test_get_cardholder_from_notes_without_cardholder_note():
    cardholder = credit_card_slips.get_cardholder_from_notes({})
    assert cardholder == "No cardholder note found"


def test_get_credit_card_full_po_lines_from_date(mocked_alma, mocked_alma_api_client):
    po_line_records = credit_card_slips.get_credit_card_full_po_lines_from_date(
        mocked_alma_api_client, "2021-05-13"
    )
    for po_line_record in po_line_records:
        assert po_line_record["resource_metadata"]["title"] == "Book title"
        assert po_line_record["created_date"] == "2021-05-13Z"


def test_get_po_line_created_date_with_date(po_line_record_all_fields):
    po_line_created_date = credit_card_slips.get_po_line_created_date(
        po_line_record_all_fields
    )
    assert po_line_created_date == "210513"


def test_get_po_line_created_date_without_date():
    po_line_created_date = credit_card_slips.get_po_line_created_date({})
    assert po_line_created_date == "No PO Line created date found"


def test_get_po_title_with_title():
    po_line_record = {"resource_metadata": {"title": "Book title"}}
    assert credit_card_slips.get_po_title(po_line_record) == "Book title"


def test_get_po_title_without_title():
    po_line_record = {"resource_metadata": {"title": None}}
    assert credit_card_slips.get_po_title(po_line_record) == "Unknown title"


def test_get_quantity_from_locations_with_locations():
    po_line_record = {"location": [{"quantity": 1}, {"quantity": 1}]}
    assert credit_card_slips.get_quantity_from_locations(po_line_record) == "2"


def test_get_quantity_from_locations_without_locations():
    po_line_record = {}
    assert credit_card_slips.get_quantity_from_locations(po_line_record) == "0"


def test_get_total_price_with_total_price():
    po_line_record = {"fund_distribution": [{"amount": {"sum": "30.0"}}]}
    assert credit_card_slips.get_total_price(po_line_record, "15.00") == "30.00"


def test_get_total_price_without_total_price():
    po_line_record = {"fund_distribution": [{"amount": {"sum": ""}}]}
    assert credit_card_slips.get_total_price(po_line_record, "15.00") == "15.00"


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


def test_populate_credit_card_slip():
    xml_template = credit_card_slips.load_xml_template(
        "config/credit_card_slip_template.xml"
    )
    po_line_dict = {"poline": "POL-123", "item_title": "Book title"}
    credit_card_slip = credit_card_slips.populate_credit_card_slip(
        xml_template, po_line_dict
    )
    assert credit_card_slip.find('.//td[@class="poline"]').text == "POL-123"
    assert credit_card_slip.find('.//td[@class="item_title"]').text == "Book title"


def test_xml_data_from_dicts(mocked_alma):
    po_line_dicts = [{"title": "Book title", "poline": "POL-123"}]
    credit_card_slips_xml_string = credit_card_slips.xml_data_from_dicts(po_line_dicts)
    credit_card_slips_xml = ET.fromstring(credit_card_slips_xml_string)
    assert credit_card_slips_xml.find('.//td[@class="poline"]').text == "POL-123"
