import logging
import json
import os
from powerPayCheckout.constants import SHAREPOINT_URLS
from powerPayCheckout.helpers import generate_invoice_number
from powerPayCheckout.microsoft_graph_api import GraphClient
from powerPayCheckout.rapyd_client import generate_checkout_id


class SharePointClient:
    """Use to interact with the SharePoint APIs"""

    def __init__(self, msft_graph_client: GraphClient) -> None:
        """Initialize the Microsoft Graph client

        Args:
            msft_graph_client (GraphClient): Microsoft Graph Client
        """

        # ID of the SharePoint page
        self.site_id = os.getenv("SITE_ID")
        self.msft_graph_client = msft_graph_client

    def get_all_lists(self) -> None:
        """Get all the SharePoint Invoice List"""

        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/c2402b9b-a65b-490a-9bca-b0a4ce953c7d/items"

        graph_result = self.msft_graph_client.send_msft_graph_request(url)

        logging.info(graph_result)

    def create_list_item(self, invoice_details) -> str:
        """Create a new SharePoint Invoice List

        Args:
            invoice_details (dict): request body

        Returns:
            str: request response
        """

        created_success = "Successfully created a new item with id - "
        url = SHAREPOINT_URLS.get("create_url").format(**{"site_id": self.site_id})

        invoice_cost = invoice_details.get("Cost").strip()

        invoice_number = generate_invoice_number().strip()

        # call the Rapyd API to generate the checkout ID
        checkout_id = generate_checkout_id(invoice_cost, invoice_number)

        # raise if we don't have an ID here, it's not necessary to proceed further without a ID
        assert checkout_id

        payload = {
            "fields": {
                "Title": invoice_details.get("Title"),
                "Customer": invoice_details.get("Customer"),
                "Cost": invoice_cost,
                "DueBy": invoice_details.get("DueBy"),
                "InvoiceNumber": invoice_number,
                "CheckoutID": checkout_id,
            }
        }

        graph_result = self.msft_graph_client.send_msft_graph_request(
            url, "POST", json.dumps(payload)
        )

        new_item_id = graph_result.get("id")

        if new_item_id:
            logging.info("Successfully created the item")
            created_success += new_item_id
        else:
            logging.info(f"Error while creating the list item {graph_result}")
            logging.info("Successfully processed the callback from Rapyd")
            created_success = "Failed to create a new item"

        return created_success

    def update_list_item(self, body):
        """Update the SharePoint Invoice list with the payment status

        Args:
            body (dict): request body

        Returns:
            str: request response
        """

        # checkout_id = body.get("checkout_id")
        status: str = body.get("status").strip()
        item_id = body.get("item_id").strip()
        # processed_by = body.get("processed_by").strip()

        assert item_id and status

        if status.lower() == "success":
            item_status = "Payment Successful"
        else:
            item_status = "Payment Failed"

        created_success = f"Successfully updated the item with id - {item_id}"

        url = SHAREPOINT_URLS.get("update_url").format(
            **{"site_id": self.site_id, "item_id": item_id}
        )

        payload = {"Status": item_status}
        # payload = {"Status": item_status, "ProcessedByLookupId": "6"}

        logging.info(f"Payload to update - {payload}")

        graph_result = self.msft_graph_client.send_msft_graph_request(
            url, "PATCH", json.dumps(payload)
        )

        logging.info(graph_result)

        if graph_result.get("id"):
            logging.info(f"Successfully updated the item with id {item_id}")

        else:
            logging.info(f"Error while creating the list item {graph_result}")
            logging.info("Successfully processed the callback from Rapyd")
            created_success = f"Failed to update the item with id {item_id}"

        return created_success
