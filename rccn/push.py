#!/usr/bin/env python
############################################################################
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

from config import *
import obscvty
import smtplib
import random
from optparse import OptionParser

def advise(msg):
    from email.mime.text import MIMEText
    text = """
Favor de intervenir y arreglar esta situacion manualmente.
    """
    mail = MIMEText(text + msg )
    mail['Subject'] = msg[:90]
    mail['From'] = 'postmaster@rhizomatica.org'
    mail['To'] = 'postmaster@rhizomatica.org'
    s = smtplib.SMTP('mail')
    s.sendmail('postmaster@rhizomatica.org', advice_email, mail.as_string())
    s.quit()

def check(auth, recent, hours=2, single=''):
    """ Get sub from the local PG db and see their status in riak """
    cur = db_conn.cursor()
    if single:
        cur.execute("SELECT msisdn,name,authorized FROM Subscribers WHERE msisdn=%s", [single])
    if recent == 0:
        cur.execute("SELECT msisdn,name,authorized FROM Subscribers WHERE authorized=%s", str(auth))
    if recent == 1:
        sql = "SELECT msisdn,name,authorized FROM Subscribers WHERE authorized=%s AND created > NOW() -interval '%s hours'" % (str(auth), hours)
        cur.execute(sql)
    if cur.rowcount > 0:
        print 'Subscriber Count: %s ' % (cur.rowcount)
        _subs=cur.fetchall()
        n=cur.rowcount
        for msisdn,name,authorized in _subs:
            print '----------------------------------------------------'
            print "%s: Checking %s %s" % (n, msisdn, name)
            imsi=osmo_ext2imsi(msisdn)
            if imsi:
                print "Local IMSI: \033[96m%s\033[0m" % (imsi)
                get(msisdn, imsi, authorized)
            else:
                msg="""
                Local Subscriber %s from PG Not Found on OSMO HLR!
                """ % msisdn
                advise(msg)
                print "\033[91;1mLocal Subscriber from PG Not Found on OSMO HLR!\033[0m"
            n=n-1
        print '----------------------------------------------------\n'
        

def imsi_clash(imsi, ext1, ext2):
    msg = """
    !! IMSI Clash between %s and %s for %s !! 

    Un IMSI no deberia de estar registrado y autorizado al mismo tiempo
    en mas que una comunidad.

    """ % (ext1,ext2,imsi)
    advise(msg)
    print "\033[91;1m" + msg + "\033[0m" 

def get(msisdn, imsi, auth):
    """Do the thing"""
    riak_client = riak.RiakClient(
    host=riak_ip_address,
    pb_port=8087,
    protocol='pbc')
    bucket = riak_client.bucket('hlr')
    sub = Subscriber()
    num = Numbering()
    try:
        # We can end up with indexes that point to non existent keys.
        # so this might fail, even though later get_index() will return an IMSI key.
        riak_obj = bucket.get(imsi, timeout=RIAK_TIMEOUT)
        if riak_obj.exists:
            riak_ext=riak_obj.data['msisdn']
            riak_auth=riak_obj.data['authorized']
        else:
            print "\033[91;1m!! Didn't get hlr key for imsi %s\033[0m" % imsi
            riak_ext = False

        if riak_ext and auth == 1 and riak_auth == 1 and (riak_ext != msisdn):
            imsi_clash(imsi, msisdn, riak_ext)
            return
        
        riak_imsi = bucket.get_index('msisdn_bin', msisdn, timeout=RIAK_TIMEOUT).results

        if riak_imsi and riak_imsi.count(riak_imsi[0]) != len(riak_imsi):
            print "\033[91;1m Different entries in this index! \033[0m"
            advise("!!More than ONE entry in this index: %s %s %s" % (msisdn,riak_imsi[0],riak_imsi[1]))
        if riak_imsi and len(riak_imsi) > 1 and riak_imsi.count(riak_imsi[0]) == len(riak_imsi):
            print "\033[91;1m Duplicate entries in this index. \033[0m"
            tmp_obj = bucket.get(riak_imsi[1])
            tmp_obj.remove_index()
            tmp_obj.add_index('modified_int', int(time.time()))
            tmp_obj.store()
        if not riak_ext or not len(riak_imsi):
            print '\033[93mExtension %s not found\033[0m, adding to D_HLR' % (msisdn)
            sub._provision_in_distributed_hlr(imsi, msisdn)
        else:
            # Already checked if the ext in the imsi key matches osmo extension.
            # Now check if the key pointed to by the extension index matches the osmo imsi
            if imsi != riak_imsi[0]:
                print "\033[91;1mIMSIs do not Match!\033[0m (%s)" % riak_imsi[0]  
                print "Riak's %s points to %s" % (riak_imsi[0], num.get_msisdn_from_imsi(riak_imsi[0]))
                return False
            print 'Extension: \033[95m%s\033[0m-%s-\033[92m%s\033[0m ' \
                  'has IMSI \033[96m%s\033[0m in Index' % (msisdn[:5], msisdn[5:6], msisdn[6:], riak_imsi[0])
            data = bucket.get(riak_imsi[0]).data
            if data['authorized'] == 1:
                print "Extension: Authorised"
            if data['authorized'] == 0:
                print "Extension: NOT Authorised"
            if data['authorized'] != auth:
                print "Extension: \033[91mAuthorisation Incorrect\033[0m, Fixing"
                data['authorized']=auth
                fix = bucket.new(imsi, data={"msisdn": msisdn, "home_bts": config['local_ip'], "current_bts": data['current_bts'], "authorized": data['authorized'], "updated": int(time.time()) })
                fix.add_index('msisdn_bin', msisdn)
                fix.add_index('modified_int', int(time.time()))
                fix.store()
            if msisdn[:6] == config['internal_prefix'] and data['home_bts'] != config['local_ip']:
                print "\033[91;1mHome BTS does not match my local IP! Fixing..\033[0m"
                fix = bucket.new(imsi, data={"msisdn": msisdn, "home_bts": config['local_ip'], "current_bts": data['current_bts'], "authorized": data['authorized'], "updated": int(time.time()) })
                fix.add_index('msisdn_bin', msisdn)
                fix.add_index('modified_int', int(time.time()))
                fix.store()
            try:
                host = socket.gethostbyaddr(data['home_bts'])
                home = host[0]
                host = socket.gethostbyaddr(data['current_bts'])
                current = host[0]
            except Exception as ex:
                home = data['home_bts']
                current = data['current_bts']
            print " Home BTS: %s" % (home)
            print "Last Seen: %s, %s" % ( 
                  current, 
                  datetime.datetime.fromtimestamp(data['updated']).ctime() )
    except Exception as ex:
        print ex


def osmo_ext2imsi(ext):
    try:
        vty = obscvty.VTYInteract('OpenBSC', '127.0.0.1', 4242)
        cmd = 'show subscriber extension %s' % (ext)
        t = vty.command(cmd)        
        m=re.compile('IMSI: ([0-9]*)').search(t)
        if m:
            return m.group(1)
        else: 
            return False
    except:
        print sys.exc_info()[1]
        return False

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-s", "--single", dest="single",
        help="Push a single number")
    parser.add_option("-c", "--cron", dest="cron", action="store_true",
        help="Running from cron, add a delay to not all hit riak at same time")
    parser.add_option("-r", "--recent", dest="recent",
        help="How many hours back to check for created Subscribers")
    parser.add_option("-n", "--noauth", dest="noauth", action="store_true",
        help="Push Not Authorized Subs to D_HLR")

    (options, args) = parser.parse_args()
    
    if options.noauth:
        auth=0
    else:
        auth=1
    if options.cron:
        wait=random.randint(0,15)
        print "Waiting %s seconds..." % wait
        time.sleep(wait)    
    if options.single:
        check(auth,-1,0,options.single)
        exit()
    if options.recent:
        check(auth,1,options.recent)
    else:
        check(auth,0)
