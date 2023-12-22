# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Meadowlark Technology Solutions LLC
#
# Author: Meadowlark Technology Solutions LLC
#
# Released under the GNU General Public License
#
import logging
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    choice_payment_method = fields.Char(string="Choice Payment Method ID", readonly=True)
