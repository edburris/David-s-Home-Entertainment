# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Meadowlark Technology Solutions LLC
#
# Author: Meadowlark Technology Solutions LLC
#
# Released under the GNU General Public License
#

from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(cr, registry):
    setup_provider(cr, registry, 'choice')


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'choice')
