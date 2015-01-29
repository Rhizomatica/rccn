############################################################################
# 
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Credit module
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

from reseller import Reseller, ResellerException
from subscriber import Subscriber, SubscriberException 
from sms import SMS, SMSException

class CreditException(Exception):
    pass

class Credit:

    def add(self, msisdn, credit):
        sub = Subscriber()
        sms = SMS();
        try:
            mysub = sub.get(msisdn)
        except SubscriberException as e:
            raise CreditException(e)

        current_balance = sub.get_balance(msisdn)
        new_balance = Decimal(str(credit)) + Decimal(str(current_balance))

        # update subscriber balance
        try:
            cur = db_conn.cursor()
            cur.execute('UPDATE subscribers SET balance=%(new_balance)s WHERE msisdn=%(msisdn)s', {'new_balance': Decimal(str(new_balance)), 'msisdn': msisdn})
            sms.send(config['smsc'], msisdn, sms_credit_added % (credit, new_balance))
        except psycopg2.DatabaseError as e:
            raise CreditException('PG_HLR error updating subscriber balance: %s' % e)

        # insert transaction into the credit history
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO credit_history(msisdn,previous_balance,current_balance,amount) VALUES(%s,%s,%s,%s)', (msisdn, current_balance, new_balance, credit))
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise CreditException('PG_HLR error inserting invoice in the history: %s' % e)
        finally:
            db_conn.commit()

    def add_to_reseller(self, msisdn, credit):
        reseller = Reseller()
        try:
            myres = reseller.get(msisdn)
        except ResellerException as e:
            raise CreditException(e)

        reseller.reseller_msisdn = msisdn
        current_balance = reseller.get_balance()
        new_balance = Decimal(str(credit)) + Decimal(str(current_balance))

        # update subscriber balance
        try:
            cur = db_conn.cursor()
            cur.execute('UPDATE resellers SET balance=%(new_balance)s WHERE msisdn=%(msisdn)s', {'new_balance': Decimal(str(new_balance)), 'msisdn': msisdn})
        except psycopg2.DatabaseError as e:
            raise CreditException('PG_HLR error updating reseller balance: %s' % e)

        # insert transaction into the credit history
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO resellers_credit_history(msisdn,previous_balance,current_balance,amount) VALUES(%s,%s,%s,%s)', (msisdn, Decimal(str(current_balance)), 
            Decimal(str(new_balance)), Decimal(str(credit))))
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise CreditException('PG_HLR error inserting reseller invoice in the history: %s' % e)
        finally:
            db_conn.commit()

if __name__ == '__main__':
    credit = Credit()
    #sub.set_balance('68820110010',3.86)
    try:
        #sub.add('37511','Antanz',4.00)
        #sub.edit('68820137511','Antanz_edit',3.86)
        credit.add('68820137514', 1.00)
        #a = sub.get('68820137511')
        #print a
        #sub.delete('68820137511')
    except CreditException as e:
        print "Error: %s" % e
