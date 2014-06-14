############################################################################
# 
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Statistics module
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

class StatisticException(Exception):
    pass

class CallsStatistics:

    def get_total_calls(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT count(*) FROM cdr')
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total calls: %s' % e)

    def get_total_minutes(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT sum(billsec)/60 FROM cdr')
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total minutes: %s' % e)

    def get_average_call_duration(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT round(avg(billsec),2) FROM cdr')
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total minutes: %s' % e)

    def get_total_calls_by_context(self, context):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT count(*) FROM cdr WHERE context=%(context)s', {'context': context})
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total minutes: %s' % e)
    
    def get_calls_stats(self, time_range):
        if time_range == '7d':
            query = "select to_char(date_trunc('day', start_stamp),'DD-MM-YY'),count(*) from cdr where start_stamp >= (now() - interval '7 day') group by date_trunc('day',start_stamp) order by date_trunc('day', start_stamp) asc"
        if time_range == '4w':
            query = "select to_char(date_trunc('week', start_stamp),'WW'),count(*) from cdr group by date_trunc('week',start_stamp) order by date_trunc('week', start_stamp) asc offset 0 limit 6"
        if time_range == 'm':
            query = "select to_char(date_trunc('month', start_stamp),'MM'),count(*) from cdr group by date_trunc('month', start_stamp) order by date_trunc('month', start_stamp) asc offset 0 limit 6"
        
        try:
            cur = db_conn.cursor()
            cur.execute(query)
            data = cur.fetchall()
            if data == []:
                raise StatisticException('No calls data found')
            else:
                return data
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error. time range: %s query: %s db error: %s' % (time_range, query, e))

    def get_calls_minutes_stats(self, time_range):
        if time_range == '7d':
            query = "select to_char(date_trunc('day', start_stamp),'DD-MM-YY'),sum(billsec)/60 from cdr where start_stamp >= (now() - interval '7 day') group by date_trunc('day',start_stamp) order by date_trunc('day', start_stamp) asc"
        if time_range == '4w':
            query = "select to_char(date_trunc('week', start_stamp),'WW'),sum(billsec)/60 from cdr group by date_trunc('week',start_stamp) order by date_trunc('week', start_stamp) asc offset 0 limit 6"
        if time_range == 'm':
            query = "select to_char(date_trunc('month', start_stamp),'MM'),sum(billsec)/60 from cdr group by date_trunc('month', start_stamp) order by date_trunc('month', start_stamp) asc offset 0 limit 6"
        
        try:
            cur = db_conn.cursor()
            cur.execute(query)
            data = cur.fetchall()
            if data == []:
                raise StatisticException('No calls minutes data found')
            else:
                return data
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error. time range: %s query: %s db error: %s' % (time_range, query, e))

    def get_calls_context_stats(self, time_range):
        if time_range == '7d':
            query = "select to_char(date_trunc('day',start_stamp),'DD-MM-YY'),count(*),context from cdr where start_stamp >= (now() - interval '7 day') group by date_trunc('day',start_stamp),context order by date_trunc('day',start_stamp) asc"
        if time_range == '4w':
            query = "select to_char(date_trunc('week', start_stamp),'WW'),count(*),context from cdr group by date_trunc('week',start_stamp) order by date_trunc('week', start_stamp),context asc offset 0 limit 6"
        if time_range == 'm':
            query = "select to_char(date_trunc('month', start_stamp),'MM'),count(*).context from cdr group by date_trunc('month', start_stamp) order by date_trunc('month', start_stamp),context asc offset 0 limit 6"
        
        try:
            cur = db_conn.cursor()
            cur.execute(query)
            data = cur.fetchall()
            if data == []:
                raise StatisticException('No calls context data found')
            else:
                return data
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error. time range: %s query: %s db error: %s' % (time_range, query, e))


class CostsStatistics:

    def get_total_spent(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT round(sum(cost),2) FROM cdr')
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total spent: %s' % e)

    def get_average_call_cost(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT round(avg(cost),2) FROM cdr')
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total spent: %s' % e)

    def get_total_spent_credits(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT sum(amount) FROM credit_history')
            data = cur.fetchone()
            return data[0]
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total spent on credits: %s' % e)

    def get_top_destinations(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT destination_name,round(sum(cost),2) FROM cdr WHERE cost IS NOT NULL GROUP BY destination_name ORDER BY sum(cost) DESC OFFSET 0 LIMIT 9')
            data = cur.fetchall()
            if data == []:
                raise StatisticException('No top destinations found')
            else:                   
                return data
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error getting total spent: %s' % e)

    def get_costs_stats(self, time_range):
        if time_range == '7d':
            query = "select to_char(date_trunc('day',start_stamp),'DD-MM-YY'),round(sum(cost),2) from cdr where cost is not null and start_stamp >= (now() - interval '7 day') group by date_trunc('day',start_stamp) order by date_trunc('day',start_stamp) asc"
        if time_range == '4w':
            query = "select to_char(date_trunc('week', start_stamp),'WW'),round(sum(cost),2) from cdr where cost is not null group by date_trunc('week',start_stamp) order by date_trunc('week', start_stamp) asc offset 0 limit 6"
        if time_range == 'm':
            query = "select to_char(date_trunc('month', start_stamp),'MM'),round(sum(cost),2) from cdr where cost is not null group by date_trunc('month', start_stamp) order by date_trunc('month', start_stamp) asc offset 0 limit 6"
        
        try:
            cur = db_conn.cursor()
            cur.execute(query)
            data = cur.fetchall()
            if data == []:
                raise StatisticException('No costs data found')
            else:
                return data
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error. time range: %s query: %s db error: %s' % (time_range, query, e))

    def get_credits_stats(self, time_range):
        if time_range == '7d':
            query = "select to_char(date_trunc('day',created),'DD-MM-YY'),round(sum(amount),2) from credit_history where created >= (now() - interval '7 day') group by date_trunc('day',created) order by date_trunc('day',created) asc"
        if time_range == '4w':
            query = "select to_char(date_trunc('week', created),'WW'),round(sum(amount),2) from credit_history group by date_trunc('week',created) order by date_trunc('week', created) asc offset 0 limit 6"
        if time_range == 'm':
            query = "select to_char(date_trunc('month', created),'MM'),round(sum(amount),2) from credit_history group by date_trunc('month', created) order by date_trunc('month', created) asc offset 0 limit 6"
        
        try:
            cur = db_conn.cursor()
            cur.execute(query)
            data = cur.fetchall()
            if data == []:
                raise StatisticException('No credits data found')
            else:
                return data
        except psycopg2.DatabaseError as e:
            raise StatisticException('Database error. time range: %s query: %s db error: %s' % (time_range, query, e))


if __name__ == '__main__':

    stat = CallsStatistics()
    try:
        #dataz = stat.get_calls_stats('7d')
        #print dataz
        print stat.get_total_calls()
        print stat.get_total_minutes()
        print stat.get_average_call_duration()
        print stat.get_total_calls_by_context('OUTBOUND')

    except StatisticException as e:
        print "Error: %s" % e

    cost = CostsStatistics()
    try:
        print cost.get_total_spent()
        print cost.get_average_call_cost()
        print cost.get_total_spent_credits()
        print cost.get_top_destinations()
        print cost.get_costs_stats('7d')
    except StatisticException as e:
        print "Error: %s" % e
    
