# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import requests
from werkzeug import urls
import re

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

from odoo.addons.payment_choice.const import SALES_URL, TOKEN_URL, HOSTED_PAYMENT_PAGE_REQUEST_URL, HOSTED_PAYMENT_PAGE_URL, RETURNS_URL, AUTHS_ONLY_URL, CAPTURES_URL, BANK_CLEARING_GET_URL

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_choice_bearer_token(self):
        url = TOKEN_URL #'https://sandbox.choice.dev/api/v1/token'
        payload = {"grant_type": "password", 
                   "username": self.provider_id.choice_user_name,
                   "password": self.provider_id.choice_password  
                   }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        _logger.info("CHOICE MAKE BEARER TOEKN REQUEST PAYLOAD: %s", payload)
        response = requests.post(url, data=payload, headers=headers, timeout=60)
        
        _logger.info("CHOICE MAKE BEARER TOEKN REQUEST RESPONSE: %s", response.json()['access_token'] )
        return response.json()['access_token']
    
    def _retrieve_choice_checkout_session_credit_card(self):
        url = SALES_URL #"https://sandbox.choice.dev/api/v1/sales/"
        bearer_token = self._get_choice_bearer_token()
        headers = {
            'AUTHORIZATION': f'Bearer {bearer_token}',
            'content_type': 'application/json'
        }
        _logger.info("********* REFERENCE *********** : %s", self.provider_reference)
        res = requests.request("GET", url + self.provider_reference , headers=headers)
        response = res.json()
        _logger.info(_("Choice API OUTGOING URL: %s") % response)
        if len(response) == 0:
            _logger.info(_("Choice Error response session_state: %s") % response)
            raise ValidationError(_("Choice is having some issues to confirm the payment, contact us for support!"))
        return response  # Return the complete response

    def _retrieve_choice_checkout_session_bank_clearing(self):
        url = BANK_CLEARING_GET_URL
        bearer_token = self._get_choice_bearer_token()
        headers = {
            'AUTHORIZATION': f'Bearer {bearer_token}',
            'content_type': 'application/json'
        }
        res = requests.request("GET", url + self.provider_reference , headers=headers)
        response = res.json()
        _logger.info(_("Choice API OUTGOING URL: %s") % response)
        if len(response) == 0:
            _logger.info(_("Choice Error response session_state: %s") % response)
            raise ValidationError(_("Choice is having some issues to confirm the payment, contact us for support!"))
        return response  # Return the complete response


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return OMPay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'choice':
            return res
        _logger.info("Choice _get_specific_rendering_values")
        base_url = self.provider_id.get_base_url()
        
        payload = {
                "DeviceCreditCardGuid" : self.provider_id.choice_device_cc_guid,
                "DeviceAchGuid": self.provider_id.choice_device_ach_guid,
                "Merchantname": self.company_id.name,
                "Description": f"{self.company_id.name} {self.reference} Payment", 
                "Amount": float(self.amount),
                "OtherURL": urls.url_join(base_url, "payment/choice/other" + '?reference=%s' % self.reference),
                "SuccessURL": urls.url_join(base_url, "payment/choice/success"+ '?reference=%s' % self.reference),
                "CancelURL": urls.url_join(base_url, "payment/choice/cancel" + '?reference=%s' % self.reference),
                "OrderNumber": self.reference,
                "OtherInfo": self.reference,
                "Customer":
                    {
                        "FirstName": self.partner_name.split(" ", 1)[0],
                        "LastName": self.partner_name.split(" ", 1)[1],
                        "Phone": re.sub('[^0-9]', '', self.partner_phone)[2:] or "0000000000",
                        "City": self.partner_city,
                        "Email": self.partner_email,
                        "Address1": self.partner_address,
                        "Zip": self.partner_zip,
                    }
                }
        _logger.info("********PAYLOAD: %s", payload)

       
        url = HOSTED_PAYMENT_PAGE_REQUEST_URL
        bearer_token = self._get_choice_bearer_token()
        headers = {
            'AUTHORIZATION': f'Bearer {bearer_token}',
            'content_type': 'application/json'
        }
        _logger.info("********HEADERS: %s", headers)

        res = requests.post(url=url, headers=headers, json=payload)
        response = res.json()
        _logger.info("********RESPONSE: %s", response)
        _logger.info("********PAYLOAD: %s", payload)
        if 'amount' in response and 'tempToken' in response:
            redirect_url = f"{HOSTED_PAYMENT_PAGE_URL}/{response['tempToken']}"
            payload.update({'api_url': '/payment/choice/redirect?redirect_url=%s' % redirect_url})
            _logger.info("********redirect_url: %s", redirect_url)

        else:
            _logger.info(_("Choice Error response: %s") % response)
            raise ValidationError(_("Choice is having some issues, contact us for support!"))
        return payload

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Choice data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        """        
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)

        if provider_code != 'choice' or len(tx) == 1:
            return tx

        reference = notification_data['otherInfo']
        _logger.info("Choice _get_tx_from_notification_data Reference: %s", reference)

        if not reference:
            raise ValidationError(
                "Choice: " + _(
                    "Received data with missing reference %(r)s.",
                    r=reference
                )
            )

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'choice')])
        if not tx:
            raise ValidationError(
                "Choice: " + _("No transaction found matching reference %s.", reference)
            )
        tx_sudo = self.sudo().search([('reference', '=', reference)])
        _logger.info("TX_SUDO: %s", tx_sudo)
        if "saleGuid" in notification_data:
            tx.write({'provider_reference': notification_data['saleGuid']})
        _logger.info("Provider Reference: %s" % tx.provider_reference)

        return tx
    
    def _process_notification_data(self, notification_data):
        """ Override to process the transaction based on Choice data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data are received.
        """
        super()._process_notification_data(notification_data)
        _logger.info("choice process notification data: provider_code: %s", self.provider_code)
        if self.provider_code != 'choice':
            return
        if "paymentType" not in notification_data and "cancelUrl" in notification_data:
            _logger.info("customer pressed cancel button")
            message = _("The customer left the payment page.")
            self._set_error(message)
            self._set_canceled()

            return request.redirect('/payment/status')
        _logger.info("*** NOT DATA *** %s", notification_data)

        if self.operation == 'refund':
            if notification_data['status'] == "Transaction - Approved" :
                _logger.info("PROCESS NOTIFICATION DATA CHOICE: REFUND REQUEST")
                _logger.info("NOTIFICATION_DATA: %s", notification_data)
                _logger.info("REF NUMBER: %s", notification_data['refNumber'])
                self.provider_reference = notification_data['refNumber']
                session_state = notification_data['status']
            else:
                _logger.error("choice process notification data status error")
                self._set_error(notification_data['message'])
                return
        else: 
            _logger.info("PROCESS NOTIFICATION DATA CHOICE: ONLINE_REDIRECT, ONLINE_TOKEN, OFFLINE")
            if "status" in notification_data and "paymentType" not in notification_data:
                response = self._retrieve_choice_checkout_session_credit_card()
            elif notification_data['paymentType'] == "Ach":
                response = self._retrieve_choice_checkout_session_bank_clearing()
            elif notification_data['paymentType'] == "Credit Card":
                response = self._retrieve_choice_checkout_session_credit_card()
           

            else:
                _logger.error('CHOICE _process_notification_data paymentType Not Found: %s', notification_data['paymentType'])
            _logger.info('CHOICE _process_notification_data response: %s', response)
            session_state = response['status']
            self.write({
                'source_transaction_id': response['refNumber']
            })

        if session_state == 'Transaction - Approved':
            if self.operation == 'refund':
                self.env.ref('payment.cron_post_process_payment_tx')._trigger()
                self._set_done()
            else:
                _logger.info('Choice payment for tx %s: set as DONE' % (self.reference))
                if self.tokenize:
                    self._choice_tokenize_from_notification_data(response, notification_data)
                self._set_done()
        else:
            msg = 'Received unrecognized response for Choice Payment %s, set as error' % (response['status'])
            _logger.info(msg)
            self.write({
                'state_message': msg
            })
            self._set_error(msg)
    
    def _send_refund_request(self, amount_to_refund=None):
        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        if self.provider_code != "choice":
            return refund_tx
        payload = { 
            "DeviceGuid": self.provider_id.choice_device_cc_guid,
            "SaleGuid": self.provider_reference,
            "Amount": amount_to_refund
        }
        bearer_token = self._get_choice_bearer_token()
        headers = {
            'AUTHORIZATION': f'Bearer {bearer_token}',
            'content_type': 'application/json'
        }
        url = RETURNS_URL
        _logger.info("SEND REFUND REQUEST PAYLOAD: %s", payload);
        res = requests.post(url=url, headers=headers, json=payload)
        _logger.info(
            "Refund request response for transaction wih reference %s:\n%s",
            self.reference, pprint.pformat(res.json())
        )
        notification_data = {}
        notification_data.update(res.json())
        refund_tx._handle_notification_data("choice", notification_data)
        return refund_tx

    def _choice_tokenize_from_notification_data(self, notification_data, initial_notification_data):
        """ Create a new token based on the notification data.

        :param dict notification_data: The notification data built with Choice objects.
                                       See `_process_notification_data`.
        :return: None
        """
        payment_method = initial_notification_data['paymentType']
        if payment_method == "Ach":
            _logger.warning("Requested Tokenization Of Non Recurring Payment Method")
            return

        if self.operation == 'online_redirect':
            payment_method_id = initial_notification_data['tokenizedCard']
        if not payment_method_id or not payment_method:
            _logger.warning("Requested Tokenization from Notification Data with missing payment method")
            return
        token = self.env['payment.token'].create({
            'provider_id': self.provider_id.id,
            'payment_details': notification_data['card']['last4'],
            'partner_id': self.partner_id.id,
            'provider_ref': notification_data['card']['customer']['guid'],
            'verified': True,
            'choice_payment_method': payment_method_id,
        })
        self.write({
            'token_id': token,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s from "
            "transaction with reference %(ref)s",
            {
                'token_id': token.id,
                'partner_id': self.partner_id.id,
                'ref': self.reference,
            },
        )

    def _send_payment_request(self):
        """ Override of payment to send a payment request to Choice with a confirmed PaymentIntent.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider_code != 'choice':
            return

        if not self.token_id:
            raise UserError("Choice: " + _("The transaction is not linked to a token."))
        
        payload = {
                "DeviceGuid" : self.provider_id.choice_device_cc_guid,
                "Amount": float(self.amount),
                "OrderNumber":  self.reference,
                "SendReceipt": False,
                "CustomerData": self.reference,
                "Card": {
                    "CardNumber": self.token_id.choice_payment_method
                }

                }
        _logger.info("********PAYLOAD: %s", payload)
        
        url = AUTHS_ONLY_URL
        bearer_token = self._get_choice_bearer_token()
        headers = {
            'AUTHORIZATION': f'Bearer {bearer_token}',
            'content_type': 'application/json'
        }
        _logger.info("********HEADERS: %s", headers)

        res = requests.post(url=url, headers=headers, json=payload)
        response = res.json()
        _logger.info("********SEND PAYMENT REQUEST...: %s", response)

        if response['status'] == "Transaction - Approved": 
            payload = {
                "DeviceGuid" : self.provider_id.choice_device_cc_guid,
                "AuthOnlyGuid": response['guid'],
                }
            _logger.info("********PAYLOAD: %s", payload)
            
            url = CAPTURES_URL
            bearer_token = self._get_choice_bearer_token()
            headers = {
                'AUTHORIZATION': f'Bearer {bearer_token}',
                'content_type': 'application/json'
            }
            _logger.info("********HEADERS: %s", headers)

            res = requests.post(url=url, headers=headers, json=payload)
            response = res.json()
            _logger.info("********SEND PAYMENT REQUEST...: %s", response)
            if response['status'] == "Transaction - Approved": 
                tx = self.search([('reference', '=', response['authOnly']['orderNumber']), ('provider_code', '=', 'choice')])
                tx.write({'provider_reference': response['saleGuid']})
                self._handle_notification_data('choice', response);
            else: 
                raise UserError("Choice: " + _("There was an issue with processing your payment please contact the company for more information."))
        
            
        else: 
            raise UserError("Choice: " + _("The Auth Only Service Has Failed Please Try Again Later."))



            

