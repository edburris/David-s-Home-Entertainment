# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Meadowlark Technology Solutions LLC
#
# Author: Meadowlark Technology Solutions LLC
#
# Released under the GNU General Public License
#

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment import utils as payment_utils
from werkzeug import urls
from odoo.http import request



_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    choice_payment_made = fields.Boolean(string="Choice Payment Made", default=False);

    def _get_access_token(self):
        self.ensure_one()
        return payment_utils.generate_access_token(
            self.partner_id.id, self.amount_total, self.currency_id.id
        )
    def _get_additional_link_values(self):
        """ Return the additional values to append to the payment link.

        Note: self.ensure_one()

        :return: The additional payment link values.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
        }
    @api.depends(
        'name', 'amount_total', 'currency_id', 'partner_id',
    )
    def _compute_link(self):
       
        base_url = self.env.company.get_base_url()  # Don't generate links for the wrong website
        url_params = {
            'reference': urls.url_quote(self.name),
            'amount': self.amount_total,
            'access_token': self._get_access_token(),
            **self._get_additional_link_values(),

        }
            # if payment_link.payment_provider_selection != 'all':
            #     url_params['provider_id'] = str(payment_link.payment_provider_selection)
        return f'{base_url}/payment/pay?{urls.url_encode(url_params)}&sale_order_id={self.id}'


    def sale_action_register_payment_choice(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        self.ensure_one()

        _logger.info("SELF REF: %s ", self.name)
        _logger.info("SELF AMNT: %s", self.amount_total)
        _logger.info("SELF PRTNR INV ID %s", self.partner_invoice_id)

        link = self._compute_link();
        _logger.info("PAYMENT LINK: " + link)
        _logger.info("SHOULD REDIRECT NOW")
        return {
            "url": link,
            "type": "ir.actions.act_url"
        }
    
    def change_choice_payment_made(self):
        self.ensure_one()
        _logger.info("Choice Payment Made: %s ", self.choice_payment_made)
        self.write({
            'choice_payment_made': not self.choice_payment_made
        })