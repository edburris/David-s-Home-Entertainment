# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import uuid

import requests
from werkzeug.urls import url_encode, url_join, url_parse

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment_choice import utils as choice_utils

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('choice', "Choice")], ondelete={'choice': 'set default'})
    choice_user_name = fields.Char(
        string="Choice Username", help="This should be the username of the odoo account you have setup with choice",
        required_if_provider='choice')
    choice_password = fields.Char(
        string="Choice Secret Password", help="This should be the password of the odoo account you have setup with choice",
        required_if_provider='choice')
    choice_merch_guid = fields.Char(
        string="Merchant GUID", help="This should be your merchant GUID as given to you by Choice",
        required_if_provider='choice')
    choice_device_cc_guid = fields.Char(
        string="Credit Card GUID", help="This should be your Credit Card GUID as given to you by Choice",
        required_if_provider='choice')
    #== THE CHOICE_ACH_GUID IS NOT REQUIRED IF CUSTOMER HAS CHOSEN NOT TO USE ACH WITH CHOICE ==#
    choice_device_ach_guid = fields.Char(
        string="ACH GUID", help="This should be your ACH GUID as given to you by Choice")

    #=== COMPUTE METHODS ===#

    @api.depends('code')

    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page. """
        super()._compute_view_configuration_fields()
        self.filtered(lambda p: p.code == 'custom').update({
            'show_allow_express_checkout': False,
        })

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'choice').update({
            'support_express_checkout': False,
            'support_manual_capture': False,
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    #=== CONSTRAINT METHODS ===#

    # === BUSINESS METHODS - PAYMENT FLOW === #

    def _choice_make_bearer_token():
        self.ensure_one()
        url = url_join('https://sandboxv2.choice.dev/api/v1/token')
        payload = {"grant_type": "password", 
                   "username": choice_utils.get_choice_user_name,
                   "password": choice_utils.get_choice_password  
                   }
        _logger.info("CHOICE MAKE BEARER TOEKN REQUEST PAYLOAD: " + payload)
        try:
            response = requests.request(method='POST', url=url, data=payload, headers=None, timeout=60)
            # Choice can send 4XX errors for payment failures (not only for badly-formed requests).
            # Check if an error code is present in the response content and raise only if not.
            # See https://developers.choice.dev/#other-errors.
            # If the request originates from an offline operation, don't raise to avoid a cursor
            # rollback and return the response as-is for flow-specific handling.
            if not response.ok \
                    and 400 <= response.status_code < 500 \
                    and response.json().get('error'):  # The 'code' entry is sometimes missing
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    _logger.exception("invalid API request at %s with data %s", url, payload)
                    error_msg = response.json().get('error', {}).get('message', '')
                    raise ValidationError(
                        "Choice: " + _(
                            "The communication with the API failed.\n"
                            "Choice gave us the following info about the problem:\n'%s'", error_msg
                        )
                    )
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError("Choice: " + _("Could not establish the connection to the API."))
        return response.json()["access_token"]

    def _choice_make_request_bearer(
        self, endpoint, payload=None, method='POST'
    ):
        """ Make a request to Choice API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict payload: The payload of the request
        :param str method: The HTTP method of the request
        # :param bool offline: Whether the operation of the transaction being processed is 'offline'
        # :param str idempotency_key: The idempotency key to pass in the request.
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()

        url = url_join('https://sandboxv2.choice.dev/api/v1/', endpoint)
        headers = {
            'AUTHORIZATION': f'Bearer {self._choice_make_bearer_token()}',
            'content_type': 'application/json'
        }
        try:
            response = requests.request(method, url, data=payload, headers=headers, timeout=60)
            # Choice can send 4XX errors for payment failures (not only for badly-formed requests).
            # Check if an error code is present in the response content and raise only if not.
            # See https://developers.choice.dev/#other-errors.
            # If the request originates from an offline operation, don't raise to avoid a cursor
            # rollback and return the response as-is for flow-specific handling.
            if not response.ok \
                    and 400 <= response.status_code < 500 \
                    and response.json().get('error'):  # The 'code' entry is sometimes missing
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    _logger.exception("invalid API request at %s with data %s", url, payload)
                    error_msg = response.json().get('error', {}).get('message', '')
                    raise ValidationError(
                        "Choice: " + _(
                            "The communication with the API failed.\n"
                            "Choice gave us the following info about the problem:\n'%s'", error_msg
                        )
                    )
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError("Choice: " + _("Could not establish the connection to the API."))
        return response.json()

    