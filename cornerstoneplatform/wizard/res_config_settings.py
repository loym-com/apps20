from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cornerstoneplatform_graphql_url = fields.Char(
        string="GraphQL URL",
        config_parameter="cornerstoneplatform.graphql_url",
    )
    cornerstoneplatform_cookie = fields.Char(
        string="Session Cookie",
        config_parameter="cornerstoneplatform.cookie",
    )
    cornerstoneplatform_debit_account_code = fields.Char(
        string="Debit Account Code",
        config_parameter="cornerstoneplatform.debit_account_code",
    )
    cornerstoneplatform_journal_code = fields.Char(
        string="Journal Code",
        config_parameter="cornerstoneplatform.journal_code",
    )