from llama import config
from llama.alma import Alma_API_Client


def test_client_init_with_params():
    client = Alma_API_Client(api_key="abc123", base_api_url="http://example.com/")
    assert client.base_url == "http://example.com/"
    assert client.headers == {"Authorization": "apikey abc123"}


def test_client_init_from_config():
    api_key = config.get_alma_api_key()
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


def test_alma_get_brief_po_lines(mocked_alma, mocked_alma_api_client):
    po_line_stubs = mocked_alma_api_client.get_brief_po_lines()
    assert next(po_line_stubs) == {"created_date": "2021-05-13Z", "number": "POL-123"}
    assert next(po_line_stubs) == {"created_date": "2021-05-02Z", "number": "POL-456"}


def test_alma_get_fund_by_code(mocked_alma, mocked_alma_api_client):
    fund = mocked_alma_api_client.get_fund_by_code("ABC")
    assert fund["fund"][0]["code"] == "ABC"
    assert fund["fund"][0]["external_id"] == "1234567-000001"


def test_alma_get_invoice(mocked_alma, mocked_alma_api_client):
    invoice = mocked_alma_api_client.get_invoice("0501130657")
    assert invoice["number"] == "0501130657"


def test_alma_get_vendor_details(mocked_alma, mocked_alma_api_client):
    vendor = mocked_alma_api_client.get_vendor_details("BKHS")
    assert vendor["code"] == "BKHS"
    assert vendor["name"] == "The Bookhouse, Inc."


def test_alma_get_po_line_full_record(mocked_alma, mocked_alma_api_client):
    po_line_record = mocked_alma_api_client.get_full_po_line("POL-123")
    assert po_line_record["resource_metadata"]["title"] == "Book title"
    assert po_line_record["created_date"] == "2021-05-13Z"


def test_alma_mark_invoice_paid(mocked_alma):
    client = Alma_API_Client(config.get_alma_api_key())
    paid = client.mark_invoice_paid(
        invoice_id="0501130657", invoice_xml_path="tests/fixtures/invoice_empty.xml"
    )
    assert "<number>0501130657</number>" in paid


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
