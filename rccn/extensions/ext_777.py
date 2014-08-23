############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Reseller Shortcode
# This file is part of RCCN
#
# RCCN is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RCCN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

import sys
sys.path.append("..")
from config import *

def handler(session, *args):
    if session:
        log.debug('Calls to Reseller shortcode rejected')
        return
    log.debug('Reseller handler')
    
    reseller_msisdn = args[0]
    text = args[2]
    
    sms = SMS()
    reseller = Reseller()

    try:
        text_data = text.split('#')
        pin = text_data[0]
        subscriber_msisdn = text_data[1]
        amount = text_data[2]
    except IndexError:
        mess = reseller.get_message(1)
        if mess != None: 
            sms.send(config['smsc'], reseller_msisdn, mess)
        raise ExtensionException('Invalid format')

    if not pin or not subscriber_msisdn or not subscriber_msisdn.isdigit() or not amount or not amount.replace(".", "", 1).isdigit():
        # send notification invalid text format
        mess = reseller.get_message(1)
        if mess != None: 
            sms.send(config['smsc'], reseller_msisdn, mess)
        raise ExtensionException('Invalid format')
    
    res_log.info('Validate data')
    try:
        reseller.reseller_msisdn = reseller_msisdn
        reseller.subscriber_msisdn = subscriber_msisdn
        reseller.validate_data(pin)
    except ResellerException as e:
        mess = reseller.get_message(1)
        if mess != None: sms.send(config['smsc'], reseller_msisdn, mess)
        raise ExtensionException('Invalid data: %s' % e)
    
    try:
        reseller.check_balance(amount)
    except ResellerException as e:
        mess2 = reseller.get_message(2)
        mess3 = reseller.get_message(3)
        if mess2 != None: sms.send(config['smsc'], subscriber_msisdn, mess2)
        if mess3 != None: sms.send(config['smsc'], reseller_msisdn, mess3)
        raise ExtensionException('Error: %s' % e)

    try:
        reseller.add_subscriber_credit(amount)
        res_log.info('Amount of %s pesos successfully added to your account. New balance: %s' % (amount, reseller. subscriber_balance))

        mess4 = reseller.get_message(4)
        if mess4 != None: 
            mess4 = mess4.replace('[var1]', str(amount))
            mess4 = mess4.replace('[var2]', str(reseller. subscriber_balance))
            sms.send(config['smsc'], subscriber_msisdn, mess4)

        mess5 = reseller.get_message(5)
        if mess5 != None:
            mess5 = mess5.replace('[var1]', str(amount))
            mess5 = mess5.replace('[var3]', subscriber_msisdn)
            mess5 = mess5.replace('[var4]', str(reseller.balance))
            sms.send(config['smsc'], reseller_msisdn, mess5)
    except ResellerException as e:
        mess6 = reseller.get_message(6)
        if mess6 != None: 
            sms.send(config['smsc'], subscriber_msisdn, mess6)
            sms.send(config['smsc'], reseller_msisdn, mess6)
        raise ExtensionException('General error credit could not be added: %s' % e)

    try:
        res_log.info('Bill reseller for %s pesos' % amount) 
        reseller.bill(amount)
    except ResellerException as e:
        res_log.error('%s' % e)
        raise ExtensionException('Reseller could not be billed')
