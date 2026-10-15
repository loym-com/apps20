# CornerstonePlatform Donations

## Open the Wizard

Open **Accounting > Journal Entries**, then choose **Import from Cornerstone** from the list view's three-dot menu next to Import and Export. The option is available to users in the **Accounting Manager** group.

## System Parameters

Register the following parameters in Odoo under **Settings > Technical > Parameters > System Parameters**. Developer mode may be required to access the Technical menu.

| Key | Value |
| --- | --- |
| `cornerstoneplatform.graphql_url` | Full URL of the CornerstonePlatform GraphQL endpoint, for example `https://example.com/_graphql`. |
| `cornerstoneplatform.cookie` | Value of the authenticated `CSNSESSID` session cookie. Enter the cookie value only, without `CSNSESSID=`. |
| `cornerstoneplatform.debit_account_code` | Code of the Odoo account to debit for the donation total. This account must be available to the active company. |
| `cornerstoneplatform.journal_code` | Code of the general journal (`account.journal.code`) to use for the generated entry. |

The cookie is an authentication credential. Store it securely and update it when the CornerstonePlatform session expires. The wizard cannot fetch donations until the GraphQL URL and cookie are configured. It cannot create the journal entry until the debit account code and journal code are configured.
