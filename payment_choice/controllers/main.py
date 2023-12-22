# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Meadowlark Technology Solutions LLC
#
# Author: Meadowlark Technology Solutions LLC
#
# Released under the GNU General Public License
#

import hashlib
import hmac
import json
import logging
import pprint
from datetime import datetime
import base64
import werkzeug

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.misc import file_open

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_choice import utils as choice_utils


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
    

    @http.route("/choice/invoice/payment/redirect", type="http", auth="public", csrf=False, save_session=False)
    def redirect_invoice_to_payments_page(self, **data):
        _logger.info("GOT TO REDIRECT INVOICE TO PAYMENT PAGE FUNCTION WITH REDIRECT URL: %s ", data);
   


