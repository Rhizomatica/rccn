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

import sys, ESL, code, yaml
sys.path.append("..")
from config import *
import xml.etree.ElementTree as ET

class StatisticException(Exception):
    pass

class LiveStatistics:

    def monitor_feed(self):
        data={}
        sub = Subscriber()
        data['mp']=config['internal_prefix']
        data['o']=sub.get_online()
        data['r']=sub.get_roaming()
        data['pa']=sub.get_paid_subscription()
        data['sp']=self.get_sms_pending()
        data['spr']=self.get_sms_pending_not_local()
        data['lt']=self.get_recent_call_count('10 mins')
        data['ld']=self.get_recent_call_count('1 day')
        data['ls']=self.get_recent_call_count('7 days')
        data['ut']=self.get_uptime()
        data['la']=os.getloadavg()
        data['v']=self.get_linev()
        data['p']=self.get_puppet_lr()
        fs_con=ESL.ESLconnection("127.0.0.1", "8021", "ClueCon")
        data['c']=self.get_fs_calls(fs_con)
        data['gw']=self.get_fs_status(fs_con)
        fs_con.disconnect()
        return data

    def get_puppet_lr(self):
        puppet_lr='/var/lib/puppet/state/last_run_summary.yaml'
        with open(puppet_lr) as stream:
            y=yaml.load(stream)
        p={}
        try:
            p['lr']=y['time']['last_run']
            p['f']=y['events']['failure']
        except:
            pass
        return p

    def get_fs_status(self,fs_con):
        e = fs_con.api("sofia xmlstatus")
        ss=ET.fromstring(e.getBody())
        gwstat={}
        try:
            for gateway in ss.findall('gateway'):
                gwstat[gateway.find('name').text]=gateway.find('state').text
            return gwstat
        except:
            pass

    def get_fs_calls(self,fs_con):

        e = fs_con.api("show calls")
        fs_calls=e.getBody()
        calls=[]
        lines=fs_calls.split('\n')
        for line in lines:
            if line != '' and line.find(' total.') == -1:
                values=line.split(',')
                if values[0]=='uuid':
                    keys=values
                    continue
                call={}
                for i,val in enumerate(values):
                    call[keys[i]]=val
                calls.append(call)
        return calls
        call_data_to_send=[]
        for call in calls:
            c={}
            c['name']=call['name']
            c['b_name']=call['b_name']
            call_data_to_send.append(c)
        return call_data_to_send

    def get_sms_pending(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select count(*) from SMS where sent isnull")
            pending = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return pending[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise StatisticException('SQ_HLR error: %s' % e.args[0])

    def get_sms_pending_not_local(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select count(*) from SMS where dest_addr not like ? and sent isnull", ([config['internal_prefix']+'%']) )
            pending = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return pending[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise StatisticException('SQ_HLR error: %s' % e.args[0])

    def get_recent_call_count(self,ago):
        # This is too hard on PS on sites with largc cdr. need to clean up 1st
        return 0
        try:
            cur = db_conn.cursor()
            cur.execute("SELECT count (id) FROM cdr WHERE end_stamp > current_timestamp - interval %(ago)s", { 'ago': ago } )
            if cur.rowcount > 0:
                sub = cur.fetchone()
                return sub[0]
            else:
                raise StatisticException('PG_HLR No rows found')
        except psycopg2.DatabaseError, e:
            raise StatisticException('PG_HLR error: %s' % e)

    def get_uptime(self):
        with open('/proc/uptime', 'r') as f:
            return float(f.readline().split()[0])

    def get_linev(self):
        try:
            with open('/tmp/voltage', 'r') as f:
                return f.readline()
        except IOError:
            return ''

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
    
