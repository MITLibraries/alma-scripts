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
    assert client.headers["accept"] == "application/json"
    assert client.headers["content-type"] == "application/json"


def test_alma_get_brief_po_lines(mocked_alma, mocked_alma_api_client):
    po_line_stubs = mocked_alma_api_client.get_brief_po_lines()
    assert next(po_line_stubs) == {"created_date": "2021-05-13Z", "number": "POL-123"}
    assert next(po_line_stubs) == {"created_date": "2021-05-02Z", "number": "POL-456"}


def test_alma_get_po_line_full_record(mocked_alma, mocked_alma_api_client):
    po_line_record = mocked_alma_api_client.get_full_po_line("POL-123")
    assert po_line_record["resource_metadata"]["title"] == "Book title"
    assert po_line_record["created_date"] == "2021-05-13Z"
