import requests

from llama import config


class Alma_API_Client:
    """An Alma_API_Client class that provides a client for interacting with the Alma API
    and specific functionality necessary for llama scripts.
    """

    def __init__(self, api_key, base_api_url=config.ALMA_API_URL):
        self.base_url = base_api_url
        self.headers = {"Authorization": f"apikey {api_key}"}

    def set_content_headers(self, accept, content_type):
        """Set headers for requesting and receiving content from the Alma API."""
        self.headers["accept"] = accept
        self.headers["content-type"] = content_type

    def get_brief_po_lines(self, acquisition_method=""):
        """Get brief PO lines with an option to narrow by acquisition_method. The
        PO line records retrieved from this endpoint do not contain all of the PO line
        data and users may wish to retrieve the full PO line record with the
        get_full_po_line method."""
        po_line_payload = {
            "status": "ACTIVE",
            "limit": "100",
            "offset": 0,
            "acquisition_method": acquisition_method,
        }
        brief_po_lines = ""
        while brief_po_lines != []:
            response = requests.get(
                f"{self.base_url}acq/po-lines",
                params=po_line_payload,
                headers=self.headers,
            ).json()
            brief_po_lines = response.get("po_line", [])
            for brief_po_line in brief_po_lines:
                yield brief_po_line
            po_line_payload["offset"] += 100

    def get_full_po_line(self, po_line_id):
        """Get a full PO line record using the PO line ID."""
        full_po_line = requests.get(
            f"{self.base_url}acq/po-lines/{po_line_id}",
            headers=self.headers,
        ).json()
        return full_po_line
