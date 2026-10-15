import { Component } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { STATIC_ACTIONS_GROUP_NUMBER } from "@web/search/action_menus/action_menus";

const cogMenuRegistry = registry.category("cogMenu");

export class ImportFromCornerstone extends Component {
    static template = "cornerstoneplatform.ImportFromCornerstone";
    static components = { DropdownItem };

    setup() {
        this.action = useService("action");
    }

    openWizard() {
        this.action.doAction("cornerstoneplatform.action_cornerstoneplatform_wizard");
    }
}

cogMenuRegistry.add(
    "cornerstoneplatform_import",
    {
        Component: ImportFromCornerstone,
        groupNumber: STATIC_ACTIONS_GROUP_NUMBER,
        isDisplayed: async ({ searchModel }) =>
            searchModel?.resModel === "account.move" &&
            (await user.hasGroup("account.group_account_manager")),
    },
    { sequence: 2 }
);