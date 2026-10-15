import calendar
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from odoo import fields, models
from odoo.exceptions import UserError


class CornerstonePlatformWizard(models.TransientModel):
    _name = "cornerstoneplatform.wizard"
    _description = "Import CornerstonePlatform Donations"

    month = fields.Date(
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )

    def action_create_move(self):
        self.ensure_one()
        company = self.env.company
        month_start = self.month.replace(day=1)
        month_end = self.month.replace(
            day=calendar.monthrange(self.month.year, self.month.month)[1]
        )

        gifts = self._get_month_gifts(month_start, month_end)
        gift_totals = defaultdict(Decimal)
        account_by_id = {}
        for gift in gifts:
            if not self._gift_matches_company(gift, company):
                continue
            cause = gift.get("cause") or {}
            account = self._find_cause_account(cause, company)
            if not account:
                ledger_account = cause.get("ledgerAccount") or {}
                cause_label = (
                    ledger_account.get("number")
                    or cause.get("name")
                    or cause.get("code")
                    or "unknown"
                )
                raise UserError(
                    self.env._(
                        "No account in company %(company)s matches donation cause %(cause)s.",
                        company=company.display_name,
                        cause=cause_label,
                    )
                )
            try:
                amount = Decimal(str(gift.get("amount", "0")))
            except (InvalidOperation, TypeError) as error:
                raise UserError(
                    self.env._("A donation has an invalid amount.")
                ) from error
            if amount < 0:
                raise UserError(self.env._("Donation amounts cannot be negative."))
            gift_totals[account.id] += amount
            account_by_id[account.id] = account

        if not gift_totals:
            raise UserError(
                self.env._("No donations were found for the active company and month.")
            )

        currency = company.currency_id
        account_ids = list(gift_totals)
        existing_lines = self.env["account.move.line"].search(
            [
                ("account_id", "in", account_ids),
                ("company_id", "=", company.id),
                ("date", ">=", month_start),
                ("date", "<=", month_end),
                ("move_id.state", "in", ["draft", "posted"]),
            ]
        )
        booked_totals = defaultdict(Decimal)
        for line in existing_lines:
            booked_totals[line.account_id.id] += Decimal(str(line.credit))
            booked_totals[line.account_id.id] -= Decimal(str(line.debit))

        differences = {}
        for account_id, gift_total in gift_totals.items():
            difference = currency.round(float(gift_total - booked_totals[account_id]))
            if currency.compare_amounts(difference, 0) < 0:
                raise UserError(
                    self.env._(
                        "Account %(account)s is already credited more than the donations total.",
                        account=account_by_id[account_id].display_name,
                    )
                )
            if currency.compare_amounts(difference, 0) > 0:
                differences[account_id] = difference

        if not differences:
            raise UserError(
                self.env._("The donations are already recorded for this month.")
            )

        parameters = self.env["ir.config_parameter"].sudo()
        debit_account_code = parameters.get_str(
            "cornerstoneplatform.debit_account_code"
        )
        if not debit_account_code:
            raise UserError(
                self.env._("Set the CornerstonePlatform debit account code in system parameters.")
            )
        journal_code = parameters.get_str("cornerstoneplatform.journal_code")
        if not journal_code:
            raise UserError(
                self.env._("Set the CornerstonePlatform journal code in system parameters.")
            )
        debit_accounts = self.env["account.account"].search(
            [
                ("code", "=", debit_account_code),
                # ("company_ids", "=", company.id),
            ]
        )
        if not debit_accounts:
            raise UserError(
                self.env._(
                    "No debit account with code %(code)s exists for %(company)s.",
                    code=debit_account_code,
                    company=company.display_name,
                )
            )
        debit_account = debit_accounts.ensure_one()

        journals = self.env["account.journal"].search(
            [
                ("code", "=", journal_code),
                # ("company_id", "=", company.id),
                ("type", "=", "general")
            ]
        )
        if not journals:
            raise UserError(
                self.env._("No general journal with code %(code)s was found.", code=journal_code)
            )
        journal = journals.ensure_one()

        total = currency.round(sum(differences.values()))
        move_label = self.env._(
            "CornerstonePlatform donations %(month)s",
            month=self.month.strftime("%Y-%m"),
        )
        line_values = [
            fields.Command.create(
                {
                    "name": move_label,
                    "account_id": debit_account.id,
                    "debit": total,
                    "credit": 0,
                }
            )
        ]
        for account_id, amount in differences.items():
            line_values.append(
                fields.Command.create(
                    {
                        "name": move_label,
                        "account_id": account_id,
                        "debit": 0,
                        "credit": amount,
                    }
                )
            )

        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "company_id": company.id,
                "journal_id": journal.id,
                "date": month_end,
                "ref": move_label,
                "line_ids": line_values,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Donation Difference Entry"),
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
        }

    def _get_month_gifts(self, start_date, end_date):
        client = self.env["cornerstoneplatform.client"]
        modules = client._get_modules()
        fundraising_module = next(
            (
                module
                for module in modules
                if (module.get("code") or "").casefold() == "fundraising"
            ),
            None,
        )
        if not fundraising_module:
            raise UserError(
                self.env._("The Fundraising module was not found in CornerstonePlatform.")
            )

        query = f"""
query Gifts {{
    room {{
        module {{
            fundraising(id: {int(fundraising_module['id'])}) {{
                gifts(
                    filters: {{
                        date: {{
                            interval: {{
                                from: "{start_date.isoformat()}"
                                to: "{end_date.isoformat()}"
                            }}
                        }}
                    }}
                ) {{
                    items {{
                        amount
                        date
                        cause {{
                            name
                            code
                            ledgerDimensionValues {{
                                dimension {{
                                    name
                                }}
                                value
                            }}
                            ledgerAccount {{
                                number
                                name
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
"""
        data = client._execute_query(query)
        gifts = (
            (data.get("room") or {})
            .get("module", {})
            .get("fundraising", {})
            .get("gifts", {})
            .get("items", [])
        )
        return gifts or []

    def _gift_matches_company(self, gift, company):
        company_names = {
            company.name.casefold(),
            company.display_name.casefold(),
            str(company.id).casefold(),
        }
        cause = gift.get("cause") or {}
        for dimension_value in cause.get("ledgerDimensionValues") or []:
            dimension = dimension_value.get("dimension") or {}
            name = (dimension.get("name") or "").casefold()
            value = str(dimension_value.get("value") or "").casefold()
            if name in company_names or value in company_names:
                return True
        return False

    def _find_cause_account(self, cause, company):
        Account = self.env["account.account"]
        ledger_account = cause.get("ledgerAccount") or {}
        ledger_account_number = ledger_account.get("number")
        if not ledger_account_number:
            return Account.browse()

        company_domain = [("company_ids", "=", company.id)]
        accounts = Account.search(
            company_domain + [("code", "=", str(ledger_account_number))]
        )
        return accounts.ensure_one()