############################################################################
#
# Copyright (C) 2014 Ruben Pollan <meskio@sindominio.net>
# Copyright (C) 2014 tele <tele@rhizomatica.org>
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
"""
rhizomatica roaming checker
"""

from config import *
import urllib2

def update_foreign_subscribers():
    sub = Subscriber()
    try:
        unregistered = sub.get_all_unregistered()
        if len(unregistered) == 0:
            roaming_log.info('No Unregisted Subscribers')
            return
        update_list(unregistered, True)
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of unregistered: %s" % e)

    try:
        foreign = sub.get_all_foreign()
        if len(foreign) == 0:
            roaming_log.info('No Foreign Subscribers')
            return
        update_list(foreign)
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of unregistered: %s" % e)


def update_list(subscribers, welcome=False):
    numbering = Numbering()
    sub = Subscriber()
    for msisdn,imsi in subscribers:
        try:
            riak_data =  numbering.get_dhlr_record(imsi)
            number=riak_data["msisdn"]


            # check if subscriber pg_hlr[current_bts] != rk_hlr[current_bts]
            pg_hlr_current_bts = numbering.get_current_bts(number)
            rk_hlr_current_bts = numbering.get_bts_distributed_hlr(str(imsi), 'current_bts')
            rk_hlr_current_bts = riak_data["current_bts"]

            if pg_hlr_current_bts != rk_hlr_current_bts:
                # riak has a different idea about current_bts to our local hlr.
                # the rhs sync job should be making that not happen.
                # update subscriber location
                roaming_log.info('Subscriber %s in roaming, update location' % number)
                roaming_log.info('PG says %s, Riak says %s' % (pg_hlr_current_bts, rk_hlr_current_bts))
                sub.update(msisdn, "roaming number", number)
            else:
                if welcome:
                    roaming_log.info('Subscriber %s in roaming, update location' % number)
                    roaming_log.info('PG says %s, Riak says %s' % (pg_hlr_current_bts, rk_hlr_current_bts))
                    # Question this: we've already done it above:
                    sub.update(msisdn, "roaming number", number)
                    roaming_log.info('Send roaming welcome message to %s' % number)
                    send_welcome_sms(number)
                    # They are here, so expire them in osmo on their home_bts
                    # really, this needs to be the last place they were seen.
                    rk_hlr_home_bts = numbering.get_bts_distributed_hlr(str(imsi), 'home_bts')
                    print 'Would PUT to http://%s:8085/subscriber/offline with msisdn=%s' % (rk_hlr_home_bts, number)
                    #try:
                    #    values = '{"msisdn": "%s"}' % number
                    #    opener = urllib2.build_opener(urllib2.HTTPHandler)
                    #    request = urllib2.Request('http://%s:8085/subscriber/offline' % rk_hlr_home_bts, data=values)
                    #    request.add_header('Content-Type', 'application/json')
                    #    request.get_method = lambda: 'PUT'
                    #    res = opener.open(request).read()
                    #    if 'success' in res:
                    #            roaming_log.info('LAC successfully updated on %s for roaming subscriber %s' % (rk_hlr_home_bts, number))
                    #    else:
                    #            roaming_log.error('Error Updating LAC on %s for roaming subscriber %s' % (rk_hlr_home_bts, number))
                    #except IOError:
                    #    roaming_log.error('Error connect to site %s to expire subscriber %s' % (server,number) )

                else:
                    # update only location and not the timestamp in rk_hlr
                    sub.update_location(imsi, number, False)
                    roaming_log.info('Subscriber %s is roaming' % number)


        except NumberingException as e:
            roaming_log.debug("Couldn't retrieve msisdn %s from the imsi: %s" % (msisdn,e))
        except SubscriberException as e:
            roaming_log.error("An error ocurred adding the roaming number %s: %s" % (number, e))

def send_welcome_sms(number):
    try:
        sms = SMS()
        sms.send(smsc_shortcode, number, sms_welcome_roaming)
    except SMSException as e:
        roaming_log.error("An error ocurred sending welcome sms to %s: %s" % (number, e))

def update_local_subscribers():
    sub = Subscriber()
    subscribers = sub.get_all_roaming()
    for imsi in subscribers:
        try:
            msisdn = sub.get_local_msisdn(imsi)
        except SubscriberException as e:
            roaming_log.info("Couldn't retrieve the msisdn %s from imsi %s: %s" % (msisdn, imsi, e))
            continue
        try:
            roaming_log.info('Subscriber %s is back at home_bts, update location' % msisdn)
            sub.update_location(imsi, msisdn, True)
        except SubscriberException as e:
            roaming_log.error("An error ocurred updating the location of %s: %s" % (imsi, e))

def update_local_connected():
    sub = Subscriber()
    num = Numbering()
    roaming_log.info('Getting all local (our) connected subscribers')
    try:
        c = sub.get_all_connected()
    except SubscriberException as e:
        roaming_log.info("Error getting Connected Subscribers: %s" % e)
        return
    roaming_log.info("Got %s connected Subscribers" % len(c))
    try:
        for msisdn in c:
            bts = num.get_current_bts(msisdn)
            roaming_log.info("%s is at %s acording to local hlr" % (msisdn[0], bts))
            if  bts != config['local_ip']:
                try:
                    imsi = sub._get_imsi(msisdn[0])
                except SubscriberException as e:
                    roaming_log.info("Error getting IMSI for %s: %s" % (str(msisdn[0]), e))
                    continue
                roaming_log.info("Moving %s IMSI:%s home (was %s)" % (msisdn[0], imsi, bts))
                sub.update_location(imsi, msisdn[0], True)
    except SubscriberException as e:
        roaming_log.info("Error updating DHLR for %s: %s" % (msisdn[0], e))

def purge_inactive_subscribers():
    sub = Subscriber()
    try:
        inactive = sub.get_all_inactive_roaming_since(3)
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of inactive: %s" % e)
        return

    for msisdn in inactive:
        try:
            sub.purge(msisdn)
            roaming_log.info("Roaming Subscriber %s purged" % msisdn)
        except SubscriberException as e:
            roaming_log.error("An error ocurred on %s purge: %s" % (msisdn, e))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        update_foreign_subscribers()
        update_local_connected()
        purge_inactive_subscribers()
    else:
        if sys.argv[1] == 'f':
            update_foreign_subscribers()
        elif sys.argv[1] == 'u':
            update_local_connected()
        elif sys.argv[1] == 'p':
            purge_inactive_subscribers()
        else:
            print ("Unknown Option: %s" % sys.argv[1])
