import time

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
        self.headers["Accept"] = accept
        self.headers["Content-Type"] = content_type

    def get_paged(
        self,
        endpoint,
        record_type,
        params=None,
        limit=100,
        _offset=0,
        _records_retrieved=0,
    ):
        """Retrieve paginated results from the Alma API for a given endpoint.
        Args:
            endpoint: The paged Alma API endpoint to call, e.g. "acq/invoices".
            record_type: The type of record returned by the Alma API for the specified
                endpoint, e.g. "invoice" record_type returned by the "acq/invoices"
                endpoint. See <https://developers.exlibrisgroup.com/alma/apis/docs/xsd/
                rest_invoice.xsd/?tags=POST#invoice> for example.
            params: Any endpoint-specific params to supply to the GET request.
            limit: The maximum number of records to retrieve per page. Valid values are
                0-100.
            _offset: The offset value to supply to paged request. Should only be used
                internally by this method's recursion.
            _records_retrieved: The number of records retrieved so far for a given
                paged endpoint. Should only be used internally by this method's
                recursion.
        """
        params = params or {}
        params["limit"] = limit
        params["offset"] = _offset
        response = requests.get(
            url=f"{self.base_url}{endpoint}",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        time.sleep(0.1)
        total_record_count = response.json()["total_record_count"]
        records = response.json().get(record_type, [])
        records_retrieved = _records_retrieved + len(records)
        for record in records:
            yield record
        if records_retrieved < total_record_count:
            yield from self.get_paged(
                endpoint,
                record_type,
                params=params,
                limit=limit,
                _offset=_offset + limit,
                _records_retrieved=records_retrieved,
            )

    def get_brief_po_lines(self, acquisition_method=""):
        """Get brief PO lines with an option to narrow by acquisition_method. The
        PO line records retrieved from this endpoint do not contain all of the PO line
        data and users may wish to retrieve the full PO line record with the
        get_full_po_line method."""
        po_line_params = {
            "status": "ACTIVE",
            "acquisition_method": acquisition_method,
        }
        return self.get_paged("acq/po-lines", "po_line", params=po_line_params)

    def get_full_po_line(self, po_line_id):
        """Get a full PO line record using the PO line ID."""
        full_po_line = requests.get(
            f"{self.base_url}acq/po-lines/{po_line_id}",
            headers=self.headers,
        ).json()
        time.sleep(0.1)
        return full_po_line

    def get_fund_by_code(self, fund_code):
        """Get fund details using the fund code."""
        endpoint = f"{self.base_url}acq/funds"
        params = {"q": f"fund_code~{fund_code}", "view": "full"}
        r = requests.get(endpoint, headers=self.headers, params=params)
        r.raise_for_status()
        time.sleep(0.1)
        return r.json()

    def get_invoice(self, invoice_id):
        """Get an invoice by ID."""
        endpoint = f"{self.base_url}acq/invoices/{invoice_id}"
        r = requests.get(endpoint, headers=self.headers)
        r.raise_for_status()
        time.sleep(0.1)
        return r.json()

    def get_invoices_by_status(self, status):
        """Get all invoices with a provided status."""
        invoice_params = {
            "invoice_workflow_status": status,
        }
        return self.get_paged("acq/invoices", "invoice", params=invoice_params)

    def get_vendor_details(self, vendor_code):
        """Get vendor info from Alma."""
        endpoint = f"{self.base_url}acq/vendors/{vendor_code}"
        r = requests.get(endpoint, headers=self.headers)
        r.raise_for_status()
        time.sleep(0.1)
        return r.json()

    def mark_invoice_paid(self, invoice_id: str, invoice_xml_path: str) -> str:
        """Mark an invoice as paid using the invoice process endpoint."""
        endpoint = f"{self.base_url}acq/invoices/{invoice_id}"
        params = {"op": "paid"}
        with open(invoice_xml_path, "rb") as file:
            r = requests.post(endpoint, headers=self.headers, params=params, data=file)
            r.raise_for_status()
        time.sleep(0.1)
        # TODO: check for Alma-specific error codes. Do we also need to check for
        # alerts? See https://developers.exlibrisgroup.com/alma/apis/docs/acq/
        # UE9TVCAvYWxtYXdzL3YxL2FjcS9pbnZvaWNlcy97aW52b2ljZV9pZH0=/ and https://
        # developers.exlibrisgroup.com/blog/Creating-an-invoice-using-APIs/ for more
        # info.
        return r.text
