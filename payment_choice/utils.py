# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Meadowlark Technology Solutions LLC
#
# Author: Meadowlark Technology Solutions LLC
#
# Released under the GNU General Public License
#

def get_choice_user_name(provider_sudo):
    """ Return the user name for Choice.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The user name
    :rtype: str
    """
    return provider_sudo.choice_user_name


def get_choice_password(provider_sudo):
    """ Return the super secret password for Choice.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The super secret password
    :rtype: str
    """
    return provider_sudo.choice_password

def get_choice_merchant_guid(provider_sudo):
    """ Return the merchant guid for Choice.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The merchant guid
    :rtype: str
    """
    return provider_sudo.choice_merch_guid

def get_choice_device_cc_guid(provider_sudo):
    """ Return the CNP credit card guid for Choice.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The cnp credit card guid
    :rtype: str
    """
    return provider_sudo.choice_device_cc_guid

def get_choice_device_ach_guid(provider_sudo):
    """ Return the ach guid for Choice.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The ach guid
    :rtype: str
    """
    return provider_sudo.choice_device_ach_guid
