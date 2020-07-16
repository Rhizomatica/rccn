############################################################################
# 
# Copyright (C) 2013 tele <tele@rhizomatica.org>
# Copyright (C) 2017 Keith Whyte <keith@rhizomatica.org>
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

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
sys.path.append("..")
from config import *

from modules.reseller import Reseller, ResellerException
from modules.subscriber import Subscriber, SubscriberException
from modules.sms import SMS, SMSException

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
            db_conn.commit()
            sms.send(config['smsc'], msisdn, sms_credit_added % (credit, new_balance))
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
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

    def get_all_credit_allocated(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT authorized,subscription_status,SUM(balance) FROM subscribers GROUP BY authorized,subscription_status')
            result = cur.fetchall()
            db_conn.commit()
            cur.close()
        except psycopg2.DatabaseError as e:
            raise CreditException('PG_HLR getting sum of balance: %s' % e)
        return result

    def get_month_credit(self, year, month):
        try:
            result=[]
            cur = db_conn.cursor()
            # Get credit allocated this month:
            fr = year+'-'+month+'-01'
            if month == '12':
                to = str(int(year)+1)+'-01-01'
            else:
                to = year+'-'+str((int(month)+1)).zfill(2)+'-01'
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM credit_history "
                        "WHERE created >= %s AND created < %s ", (fr, to) )
            result.append(cur.fetchone())
            cur.execute("SELECT COALESCE(sum(cost),0) FROM cdr "
                        "WHERE cost is not null "
                        "AND start_stamp >= %s and start_stamp < %s", (fr, to) )
            result.append(cur.fetchone())
            cur.execute("SELECT count(id) FROM cdr "
                        "WHERE cost is not null "
                        "AND start_stamp >= %s and start_stamp < %s", (fr, to) )
            result.append(cur.fetchone())
            db_conn.commit()
            cur.close()
        except psycopg2.DatabaseError as e:
            raise CreditException('PG_HLR getting monthly credit details: %s' % e)
        return result

    def get_credit_records(self, year):
        try:
            result=[]
            fr = year+'-01-01'
            to = str(int(year)+1)+'-01-01'
            cur = db_conn.cursor()
            sql="""
            SELECT
            COALESCE(a.y,b.y)::int as y, COALESCE(a.m,b.m)::int as m,
            COALESCE(recarga,0) as recarga, COALESCE(gasto,0) as gasto,
            b.call_count as call_count
            FROM (
            SELECT date_part('YEAR', created)::varchar AS y,
            date_part('MONTH', created)::varchar AS m,
            COALESCE(SUM(amount),0)::int AS recarga,
            NULL as call_count
            FROM credit_history
            WHERE created >= %(fr)s AND created < %(to)s
            GROUP BY y,m) a
            FULL OUTER JOIN (
            SELECT date_part('YEAR', start_stamp)::varchar AS y,
            date_part('MONTH', start_stamp)::varchar AS m,
            COALESCE(sum(cost),0)::int AS gasto,
            count(id) as call_count
            FROM cdr
            WHERE cost is not null
            AND start_stamp >= %(fr)s AND start_stamp < %(to)s
            GROUP BY y,m) b
            ON a.y=b.y and a.m=b.m
            ORDER BY y,m;
            """
            data={ 'fr': fr, 'to': to}
            cur.execute(sql, data)
            result = cur.fetchall()
            db_conn.commit()
            cur.close()
            """
            cur.execute("SELECT date_part('YEAR', created)::varchar as y,"
                        "date_part('MONTH', created)::varchar AS m,"
                        "COALESCE(SUM(amount),0) as saldo "
                        "FROM credit_history "
                        "WHERE created >= %s AND created < %s "
                        "GROUP BY y,m ORDER BY y,m;", (fr, to)
                        )
            result.append(cur.fetchall())
            cur.execute("SELECT date_part('YEAR', start_stamp)::varchar AS y,"
                        "date_part('MONTH', start_stamp)::varchar AS m,"
                        "COALESCE(sum(cost),0) AS cost "
                        "FROM cdr "
                        "WHERE start_stamp >= %s AND start_stamp < %s "
                        "GROUP BY y,m ORDER BY y,m", (fr, to)
                        )
            result.append(cur.fetchall())
            """
            #code.interact(local=dict(globals(),**locals()))

        except psycopg2.DatabaseError as e:
            raise CreditException('PG_HLR getting all credit records: %s' % e)
        return result
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
        print("Error: %s" % e)
