import datetime
import json

from llama import CONFIG
from llama.alma import Alma_API_Client


def test_client_init_with_params():
    client = Alma_API_Client(api_key="abc123", base_api_url="http://example.com/")
    assert client.base_url == "http://example.com/"
    assert client.headers == {"Authorization": "apikey abc123"}


def test_client_init_from_config():
    api_key = CONFIG.get_alma_api_key("ALMA_API_ACQ_READ_KEY")
    client = Alma_API_Client(api_key)
    assert client.base_url == "http://example.com/"
    assert client.headers == {"Authorization": "apikey abc123"}


def test_alma_set_content_headers():
    client = Alma_API_Client(api_key="abc123", base_api_url="http://example.com/")
    assert len(client.headers) == 1
    client.set_content_headers("application/json", "application/json")
    assert len(client.headers) == 3
    assert client.headers["Accept"] == "application/json"
    assert client.headers["Content-Type"] == "application/json"


def test_alma_create_invoice(mocked_alma, mocked_alma_api_client):
    with open("tests/fixtures/invoices.json") as f:
        invoice_data = json.load(f)["invoice"][0]
    invoice = mocked_alma_api_client.create_invoice(invoice_data)
    assert invoice["id"] == "01"


def test_alma_create_invoice_line(mocked_alma, mocked_alma_api_client):
    with open("tests/fixtures/invoice_line.json") as f:
        invoice_line_data = json.load(f)
    invoice_line = mocked_alma_api_client.create_invoice_line(
        "123456789", invoice_line_data
    )
    assert invoice_line["number"] == "1"


def test_alma_create_vendor(mocked_alma, mocked_alma_api_client):
    with open("tests/fixtures/vendor.json") as f:
        vendor_data = json.load(f)
    vendor = mocked_alma_api_client.create_vendor(vendor_data)
    assert vendor["code"] == "BKHS"


def test_alma_get_brief_po_lines_no_acq_method(mocked_alma, mocked_alma_api_client):
    po_line_stubs = mocked_alma_api_client.get_brief_po_lines()
    assert next(po_line_stubs) == {"created_date": "2021-05-13Z", "number": "POL-123"}
    assert next(po_line_stubs) == {"created_date": "2021-05-02Z", "number": "POL-456"}


def test_alma_get_brief_po_lines_with_acq_method(mocked_alma, mocked_alma_api_client):
    po_line_stubs = mocked_alma_api_client.get_brief_po_lines("PURCHASE_NOLETTER")
    assert next(po_line_stubs) == {"created_date": "2021-05-15Z", "number": "POL-789"}


def test_alma_get_fund_by_code(mocked_alma, mocked_alma_api_client):
    fund = mocked_alma_api_client.get_fund_by_code("ABC")
    assert fund["fund"][0]["code"] == "ABC"
    assert fund["fund"][0]["external_id"] == "1234567-000001"


def test_alma_get_invoice(mocked_alma, mocked_alma_api_client):
    invoice = mocked_alma_api_client.get_invoice("558809630001021")
    assert invoice["number"] == "0501130657"


def test_alma_get_vendor_details(mocked_alma, mocked_alma_api_client):
    vendor = mocked_alma_api_client.get_vendor_details("BKHS")
    assert vendor["code"] == "BKHS"
    assert vendor["name"] == "The Bookhouse, Inc."


def test_alma_get_vendor_invoices(mocked_alma, mocked_alma_api_client):
    invoices = mocked_alma_api_client.get_vendor_invoices("BKHS")
    assert len(list(invoices)) == 5


def test_alma_get_po_line_full_record(mocked_alma, mocked_alma_api_client):
    po_line_record = mocked_alma_api_client.get_full_po_line("POL-123")
    assert po_line_record["resource_metadata"]["title"] == "Book title"
    assert po_line_record["created_date"] == "2021-05-13Z"


def test_alma_mark_invoice_paid(mocked_alma):
    client = Alma_API_Client("abc123")
    paid = client.mark_invoice_paid(
        invoice_id="558809630001021",
        payment_date=datetime.datetime(2021, 7, 22),
        payment_amount="120",
        payment_currency="USD",
    )
    assert paid["payment"]["payment_status"]["value"] == "PAID"
    assert paid["payment"]["voucher_date"] == "2021-07-22Z"
    assert paid["payment"]["voucher_amount"] == "120"
    assert paid["payment"]["voucher_currency"]["value"] == "USD"


def test_alma_get_invoices_by_status(mocked_alma, mocked_alma_api_client):
    invoices = mocked_alma_api_client.get_invoices_by_status("paid")
    i = next(invoices)
    assert i["number"] == "0501130657"
    assert i["payment"]["payment_status"]["value"] == "PAID"
    assert next(invoices)["number"] == "0501130658"


def test_alma_get_paged(mocked_alma, mocked_alma_api_client):
    records = mocked_alma_api_client.get_paged(
        endpoint="paged",
        record_type="fake_records",
        limit=10,
    )
    assert len(list(records)) == 15


def test_alma_process_invoice(mocked_alma, mocked_alma_api_client):
    processed_invoice = mocked_alma_api_client.process_invoice("00000055555000000")
    assert processed_invoice["invoice_workflow_status"]["value"] == "Waiting to be Sent"
