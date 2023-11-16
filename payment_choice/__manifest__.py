# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: Choice',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'summary': "An American payment provider covering the US and many others.",
    'description': "An American Payment Provider covering the US and many others.",
    'depends': ['payment', 'account', 'sale'],
    'author':"Meadowlark Technology Solutions LLC",
    'website': "https://meadowlarkts.com",

    'data': [
        'views/payment_provider_views.xml',
        'views/payment_choice_templates.xml',
        'views/invoice_choice_register_payment.xml',
        'views/sales_order_choice_register_payment.xml',

        'data/payment_provider_data.xml',  # Depends on views/payment_choice_templates.xml
    ],
    'application': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    # },
    'license': 'LGPL-3',
}
