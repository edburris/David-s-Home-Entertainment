
import logging

from odoo import _, api, fields, models
from odoo.addons.payment_choice import utils as payment_utils
from werkzeug import urls



_logger = logging.getLogger(__name__)

class AccountMove(models.Model): 
    _inherit = 'account.move'

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
        'payment_reference', 'amount_total', 'currency_id', 'partner_id',
    )
    def _compute_link(self):
       
        base_url = self.env.company.get_base_url()  # Don't generate links for the wrong website
        url_params = {
            'reference': urls.url_quote(self.payment_reference),
            'amount': self.amount_total,
            'access_token': self._get_access_token(),
            **self._get_additional_link_values(),

        }
        return f'{base_url}/payment/pay?{urls.url_encode(url_params)}&invoice_id={self.id}'

    def action_register_payment_choice(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        link = self._compute_link();
        _logger.info("PAYMENT LINK: " + link)
        _logger.info("SHOULD REDIRECT NOW")
        return {
            "url": link,
            "type": "ir.actions.act_url"
        }
