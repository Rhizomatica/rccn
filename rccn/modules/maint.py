############################################################################
#
# Copyright (C) 2019 <keith@rhizomatica.org>
#
# Maintenance module
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

from subprocess import Popen
import sys
sys.path.append("..")
from config import *

class MaintenanceException(Exception):
    pass

class Maintenance:
    '''
    Make a new table and copy the records to be deep archived.
    Export with pg_dump
    DELETE the archived records:
    '''
    def __init__(self):
        self.archive_dir = "/var/rhizo_backups/exported/"

    def dump(self, host, dbname, user, password, table, filename):
        command = ('pg_dump --host=%s '
                   '--username=%s '
                   '--no-password '
                   '-d %s '
                   '-t %s '
                   '--file=%s ' %
                   (host, dbname, user, table, self.archive_dir + filename)
                  )
        print(command)
        try:
            self.check_archive_file(filename)
        except Exception as error:
            raise

        try:
            proc = Popen(command, shell=True, env={'PGPASSWORD': password})
            proc.wait()
        except Exception:
            raise
        return True

    def check_archive_dir(self):
        if not os.path.isdir(self.archive_dir):
            try:
                os.mkdir(self.archive_dir)
            except OSError as error:
                print(error)
                return False
        return True

    def check_archive_file(self, filename):
        if os.path.isfile(self.archive_dir + filename):
            raise MaintenanceException('dump file exists')

    def sms_table_state(self):
        cur.execute("select MIN(send_stamp), MAX(send_stamp), count(*) FROM sms")
        if cur.rowcount > 0:
            row = cur.fetchone()
            db_conn.commit()
            return row

    def cdr_table_state(self):
        cur.execute("select MIN(start_stamp), MAX(start_stamp), count(*) FROM cdr")
        if cur.rowcount > 0:
            row = cur.fetchone()
            db_conn.commit()
            return row

    def get_state(self):
        s = self.sms_table_state()
        c = self.cdr_table_state()
        print ("\nOldest SMS has date %s.\n"
               "Latest SMS has date %s.\n"
               "%s SMS in the SMS database.\n\n"
               "Oldest Call Record has date %s.\n"
               "Latest Call Record has date %s.\n"
               "%s Records in the CDR database.\n\n" %
               (s[0], s[1], s[2], c[0], c[1], c[2])
              )

    def create_check_archive_table(self, table):
        '''
        Create the archive table, return false on error
        or if it has any rows (and existed)
        We do assume trusted input to this function somehow....
        '''
        if table != 'cdr' and table != 'sms':
            return -1
        sql_t = "CREATE TABLE IF NOT EXISTS %s_archive (LIKE %s including all)"

        if table == 'cdr':
            sql = (sql_t % (table, table))
        if table == 'sms':
            sql = (sql_t % (table, table))

        try:
            cur = db_conn.cursor()
            cur.execute(sql)
            cur.close()
            db_conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return False

        sql = ("SELECT count(*) from %s_archive" % table)

        try:
            cur = db_conn.cursor()
            cur.execute(sql)
            rows = cur.fetchone()
            cur.close()
            db_conn.commit()
            if rows is None or rows[0] != 0:
                return False
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return False

        return True

    def move_to_archive(self, table, start_year, start_month, n_of_months):
        '''
        We do assume trusted input to this function somehow....
        '''
        if table != 'cdr' and table != 'sms':
            return -1

        filename = table + "-" + str(start_year) + "-" + str(start_month) + "-" + str(n_of_months) + ".sql"
        try:
            self.check_archive_file(filename)
        except Exception as error:
            print(error)
            return False

        if table == 'cdr':
            stamp = 'start_stamp'

        if table == 'sms':
            stamp = 'send_stamp'


        date_s = ("'%s-%s-01'::timestamp" % (start_year, start_month))
        date_e = ("'%s-%s-01'::timestamp +interval '%s months'" % (start_year, start_month, n_of_months))

        s_from = ("from %s WHERE %s BETWEEN %s and %s" % (table, stamp, date_s, date_e))
        try:
            cur = db_conn.cursor()
            sql = ("INSERT INTO %s_archive SELECT * %s" % (table, s_from))
            print(sql)
            cur.execute(sql)
            cur.close()
            db_conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            db_conn.rollback()
            print(error)
            return False

        # Table is now ready for export.
        try:
            self.dump('localhost', pgsql_db, pgsql_user, pgsql_pwd, table+'_archive', filename)
        except Exception as error:
            print(error)
            return False

        try:
            cur = db_conn.cursor()
            sql = ("DELETE %s" % s_from)
            print(sql)
            cur.execute(sql)
            cur.close()
            db_conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            db_conn.rollback()
            print(error)
            return False

        try:
            cur = db_conn.cursor()
            sql = ("TRUNCATE table %s_archive" % table)
            print(sql)
            cur.execute(sql)
            cur.close()
            db_conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            db_conn.rollback()
            print(error)
            return False

        return True
