from llama.alma import Alma_API_Client


def test_alma_create_api_headers():
    alma_api_client = Alma_API_Client("abc123", "http://example.com/")
    assert hasattr(alma_api_client, "api_headers") is False
    alma_api_client.create_api_headers("application/json", "application/json")
    assert alma_api_client.api_headers == {
        "Authorization": "apikey abc123",
        "accept": "application/json",
        "content-type": "application/json",
    }


def test_alma_get_brief_po_lines(mocked_alma, mocked_alma_api_client):
    po_line_stubs = mocked_alma_api_client.get_brief_po_lines()
    assert next(po_line_stubs) == {"created_date": "2021-05-13Z", "number": "POL-123"}
    assert next(po_line_stubs) == {"created_date": "2021-05-02Z", "number": "POL-456"}


def test_alma_get_po_line_full_record(mocked_alma, mocked_alma_api_client):
    po_line_record = mocked_alma_api_client.get_full_po_line("POL-123")
    assert po_line_record["resource_metadata"]["title"] == "Book title"
    assert po_line_record["created_date"] == "2021-05-13Z"
