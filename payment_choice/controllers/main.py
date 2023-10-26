# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import werkzeug

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)


class ChoiceController(http.Controller):
    _success_url = '/payment/choice/success'
    _other_url = '/payment/choice/other'
    _cancel_url = '/payment/choice/cancel'

    @http.route([_success_url, _cancel_url ], type='http', auth='public', csrf=False, save_session=False)
    def choice_handle_feedback(self, reference, **data):
        _logger.info("Choice: choice handel feedback data: %s", data)
        if(len(data) == 0): 
            return request.redirect('/payment/status')

        else:
            _logger.info('Choice: entering form_feedback with post response %s', data)
            _logger.info('Choice: entering form_feedback with reference response %s', reference)

            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'choice', data
            )
            _logger.info("*****LOOK HERE****** %s", tx_sudo)
            tx_sudo._handle_notification_data('choice', data)
            return request.redirect('/payment/status')
    @http.route('/payment/choice/redirect', type='http', auth='public', csrf=False, save_session=False)
    def choice_redirect(self, **post):
        redirect_url = post.get('redirect_url')
        return werkzeug.utils.redirect(redirect_url)
   


