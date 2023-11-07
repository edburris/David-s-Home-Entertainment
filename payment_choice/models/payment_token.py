# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, fields, models

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    choice_payment_method = fields.Char(string="Choice Payment Method ID", readonly=True)
