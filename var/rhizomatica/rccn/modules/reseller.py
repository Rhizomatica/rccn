############################################################################
# Copyright (C) 2014 tele <tele@rhizomatica.org>
#
# Reseller module
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
from subscriber import Subscriber, SubscriberException

class ResellerException(Exception):
    pass

class Reseller:

    def __init__(self):
        self.reseller_msisdn = ''
        self.subscriber_msisdn = ''
        self.previous_balance = 0
        self.balance = 0
        self.subscriber_balance = 0


    def get_all(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM resellers')
            if cur.rowcount > 0:
                res = cur.fetchall()
                return res
            else:
                raise ResellerException('PG_HLR No resellers found')
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting resellers: %s' % e)

    def get(self, msisdn):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM resellers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
                sub = cur.fetchone()
                return sub
            else:
                raise ResellerException('PG_HLR No reseller found')
        except psycopg2.DatabaseError as e:
            raise ResellerException('PG_HLR error getting reseller: %s' % e)

    def get_messages(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM resellers_configuration')
            if cur.rowcount > 0:
                messages = cur.fetchone()
                return messages
            else:
                raise ResellerException('PG_HLR messages found')
        except psycopg2.DatabaseError as e:
            raise ResellerException('PG_HLR error getting reseller messages: %s' % e)
    
    def add(self, msisdn, pin, balance):
        # check if subscriber exists
        try:
            sub = Subscriber()
            sub.get(msisdn)
        except SubscriberException as e:
            raise ResellerException('Invalid subscriber: %s' % e)

        # provision the reseller
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO resellers(msisdn,pin,balance) VALUES(%(msisdn)s,%(pin)s,%(balance)s)', {'msisdn': msisdn, 'pin': pin, 'balance': Decimal(str(balance))})
            db_conn.commit()
        except psycopg2.DatabaseError as e:
            raise ResellerException('PG_HLR error provisioning reseller: %s' % e)

    def delete(self, msisdn):
        try:
            cur = db_conn.cursor()
            cur.execute('DELETE FROM resellers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                raise ResellerException('PG_HLR No reseller found')
        except psycopg2.DatabaseError as e:
            raise ResellerException('PG_HLR error deleting reseller: %s' % e)
    
    def edit(self, msisdn, pin, balance):
        try:
            cur = db_conn.cursor()
            if balance != '':
                cur.execute('UPDATE resellers SET msisdn=%(msisdn)s,pin=%(pin)s,balance=%(balance)s WHERE msisdn=%(msisdn2)s', {'msisdn': msisdn, 'name': name, 
                'balance': Decimal(str(balance)), 'msisdn2': msisdn})
            else:
                cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,pin=%(pin)s WHERE msisdn=%(msisdn2)s', {'msisdn': msisdn, 'pin': pin, 'msisdn2': msisdn})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                raise ResellerException('PG_HLR No reseller found')
        except psycopg2.DatabaseError as e:
            raise ResellerException('PG_HLR error updating reseller data: %s' % e)

    def edit_messages(self, mess1, mess2, mess3, mess4, mess5, mess6):
        try:
            cur = db_conn.cursor()
            cur.execute('UPDATE resellers_configuration SET message1=%(mess1)s,message2=%(mess2)s,message3=%(mess3)s,message4=%(mess4)s,message5=%(mess5)s,message6=%(mess6)s',
            {'mess1': mess1, 'mess2': mess2, 'mess3': mess3, 'mess4': mess4, 'mess5': mess5, 'mess6': mess6})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                raise ResellerException('Error configuring notification messages')
        except psycopg.DatabaseError as e:
            raise ResellerException('Error updating reseller notification messages: %s' % e)
            

    def validate_data(self, pin):
        res_log.debug('Check PIN length')
        if len(pin) > 4 or len(pin) < 4:
            raise ResellerException('PIN invalid length')
    
    
        res_log.debug('Check if Reseller exists')
        # check if reseller exists in the database and the PIN is valid
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT msisdn,pin FROM resellers WHERE msisdn=%(msisdn)s', {'msisdn': str(self.reseller_msisdn)})
            if cur.rowcount > 0:
                res_log.debug('Valid Reseller found')
                res_log.debug('Auth PIN')
                data = cur.fetchone()
                if data[1] != pin:
                    raise ResellerException('Invalid PIN!')
                res_log.debug('Check if subscriber is valid')
                # check if subscriber exists
                try:
                    sub = Subscriber()
                    sub.get(self.subscriber_msisdn)
                except SubscriberException as e:
                    raise ResellerException('Invalid subscriber')
        
            else:
                raise ResellerException('Invalid Reseller')
        except psycopg2.DatabaseError as e:
            raise ResellerException('Database error getting reseller msisdn: %s' % e)


    def get_balance(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT balance FROM resellers WHERE msisdn=%(msisdn)s', {'msisdn': str(self.reseller_msisdn)})
            balance = cur.fetchone()
            if balance != None:
                return balance[0]
            else:
                raise ResellerException('Error getting Reseller balance')
        except psycopg2.DatabaseError as e:
            raise ResellerException('Database error getting Reseller balance: %s' % e)


    def get_message(self, id):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT message'+str(id)+' FROM resellers_configuration')
            message = cur.fetchone()
            if message != None:
                return message[0]
            else:
                return None
        except psycopg2.DatabaseError as e:
            return None

    
    def check_balance(self, amount):
        self.balance = self.get_balance()
        self.previous_balance = self.balance
        balance_after_sale = Decimal(str(self.balance)) - Decimal(str(amount))
        if balance_after_sale < 0.00:
            res_log.info('Reseller doesn\'t have enough funds to add credit to the subscriber')
            raise ResellerException('Not enough funds to add the credit')
        else:
            res_log.info('Reseller has enough balance %s, total balance after billing will be: %s' % (self.balance, balance_after_sale))
            self.balance = balance_after_sale

    def add_subscriber_credit(self, amount):
        res_log.info('Add %s to subscriber %s' % (amount, self.subscriber_msisdn))
        try:
            sub = Subscriber()
            from credit import Credit, CreditException
            credit = Credit()
            res_log.debug('Get current subscriber balance')
            current_subscriber_balance = sub.get_balance(self.subscriber_msisdn)
            res_log.debug('Current subscriber balance: %s' % current_subscriber_balance)
            new_balance = Decimal(str(current_subscriber_balance)) + Decimal(str(amount))
            res_log.debug('New balance: %s' % new_balance)
            credit.add(self.subscriber_msisdn, amount)  
            self.subscriber_balance = new_balance
        except SubscriberException as e:
            raise ResellerException('Error getting subscriber balance: %s' % e)
        except CreditException as e:
            raise ResellerException('Error adding credit to subscriber: %s' % e)
    
    def bill(self, amount):
        try:
            cur = db_conn.cursor()
            cur.execute('UPDATE resellers SET balance=%(balance)s, total_sales = total_sales + 1 WHERE msisdn = %(msisdn)s', 
            {'balance': Decimal(str(self.balance)), 'msisdn': self.reseller_msisdn})
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise ResellerException('Error in setting Reseller balance')
        
        try:
            cur.execute('INSERT INTO resellers_credit_history(msisdn,previous_balance,current_balance) VALUES(%(r_msisdn)s,%(prev_balance)s,%(curr_balance)s)', 
            {'r_msisdn': self.reseller_msisdn, 'prev_balance': Decimal(str(self.previous_balance)), 'curr_balance': Decimal(str(self.balance))})
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise ResellerException('Error creating invoice for reseller: %s' % e)

        try:
            cur.execute('INSERT INTO resellers_transactions(reseller_msisdn,subscriber_msisdn,amount) values(%(r_msisdn)s,%(s_msisdn)s,%(amount)s)', 
            {'r_msisdn': self.reseller_msisdn, 's_msisdn': self.subscriber_msisdn, 'amount': Decimal(str(amount))})
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise ResellerException('Error adding reseller subscriber credit history')
        finally:    
            db_conn.commit()
