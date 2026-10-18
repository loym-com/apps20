{
    "name": "Cornerstone Platform",
    "version": "20.0.1.0.0",
    "author": "Henrik Norlin",
    "category": "Accounting",
    "summary": "GraphQL Integration",
    "depends": ["account", "base_import"],
    "data": [
        "security/ir.access.csv",
        "wizard/cornerstoneplatform_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cornerstoneplatform/static/src/cornerstoneplatform_cog_menu.js",
            "cornerstoneplatform/static/src/cornerstoneplatform_cog_menu.xml",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
