import requests

from odoo import models
from odoo.exceptions import UserError


MODULES_QUERY = """
query Modules {
    room {
        modules {
            id
            code
        }
    }
}
"""


class CornerstonePlatformClient(models.AbstractModel):
    _name = "cornerstoneplatform.client"
    _description = "CornerstonePlatform GraphQL Client"

    def _get_modules(self):
        data = self._execute_query(MODULES_QUERY)
        return (data.get("room") or {}).get("modules") or []

    def _execute_query(self, query):
        parameters = self.env["ir.config_parameter"].sudo()
        url = parameters.get_str("cornerstoneplatform.graphql_url")
        cookie_value = parameters.get_str("cornerstoneplatform.cookie")
        if not url or not cookie_value:
            raise UserError(
                self.env._(
                    "Set the CornerstonePlatform GraphQL URL and cookie in system parameters."
                )
            )

        try:
            response = requests.post(
                url,
                json={"query": query},
                cookies={"CSNSESSID": cookie_value},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as error:
            raise UserError(
                self.env._("Could not fetch data from CornerstonePlatform: %s", error)
            ) from error

        if result.get("errors"):
            messages = "; ".join(
                error.get("message", str(error)) for error in result["errors"]
            )
            raise UserError(
                self.env._("CornerstonePlatform returned an error: %s", messages)
            )
        return result.get("data") or {}