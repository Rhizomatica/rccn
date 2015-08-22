#!/usr/bin/env python 
# -*- coding: utf-8 -*-
############################################################################
# 
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# SMS module
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

import urllib, obscvty, time
from subscriber import Subscriber, SubscriberException 
from numbering import Numbering, NumberingException
from threading import Thread

class SMSException(Exception):
    pass

class SMS:

    def __init__(self):
        self.server = kannel_server
        self.port = kannel_port
        self.username = kannel_username
        self.password = kannel_password
        self.charset = 'UTF-8'
        self.coding = 2
        self.context = 'SMS_LOCAL'
        self.source = ''
        self.destination = ''
        self.text = ''
        self.save_sms = 1

        self.numbering = Numbering()


    def receive(self, source, destination, text, charset, coding):
        self.charset = charset
        self.coding = coding
        self.source = source
        self.destination = destination
        self.text = text

        sms_log.info('Received SMS: %s %s' % (source, destination))
        # SMS_LOCAL | SMS_INTERNAL | SMS_INBOUND | SMS_OUTBOUND | SMS_ROAMING

        try:
            # auth checks
            # get auth info
            sub = Subscriber()

            # check if source or destination is roaming
            try:
                if self.numbering.is_number_roaming(source):
                    sms_log.info('Source number is roaming')
                    self.roaming('caller')
		    return
            except NumberingException as e:
                sms_log.info('Sender unauthorized send notification message')
                self.context = 'SMS_UNAUTH'
                self.send(config['smsc'], source, config['sms_source_unauthorized'])
                return

            try:
                if self.numbering.is_number_roaming(destination):
                    sms_log.info('Destination number is roaming')
                    self.roaming('called')
                    return
            except NumberingException as e:
                sms_log.info('Destination unauthorized send notification message')
                self.context = 'SMS_UNAUTH'
                self.send(config['smsc'], source, config['sms_destination_unauthorized'])
                return

            try:
                source_authorized = sub.is_authorized(source, 0)
            except SubscriberException as e:
                source_authorized = False
            try:
                destination_authorized = sub.is_authorized(destination, 0)
            except SubscriberException as e:
                destination_authorized = False

            sms_log.info('Source_authorized: %s Destination_authorized: %s' % (str(source_authorized), str(destination_authorized)))


            if not source_authorized and not self.numbering.is_number_internal(source):
                sms_log.info('Sender unauthorized send notification message')
                self.context = 'SMS_UNAUTH'
                self.send(config['smsc'], source, config['sms_source_unauthorized'])
                return

            if self.numbering.is_number_local(destination):
                sms_log.info('SMS_LOCAL check if subscriber is authorized')
                # get auth info
                sub = Subscriber()
                source_authorized = sub.is_authorized(source, 0)
                destination_authorized = sub.is_authorized(destination, 0)
                try:
                    if source_authorized and destination_authorized:
                        sms_log.info('Forward SMS back to BSC')
                        # number is local send SMS back to SMSc
                        self.context = 'SMS_LOCAL'
                        self.send(source, destination, text)
                    else:
                        if not self.numbering.is_number_local(source) and destination_authorized:
                            sms_log.info('SMS_INTERNAL Forward SMS back to BSC')
                            self.context = 'SMS_INTERNAL'
                            self.send(source, destination, text)
                        else:
                            if destination_authorized and not self.numbering.is_number_local(source):
                                sms_log.info('SMS_INBOUND Forward SMS back to BSC')
                                # number is local send SMS back to SMSc
                                self.context = 'SMS_INBOUND'
                                self.send(source, destination, text)
                            else:
                                self.charset = 'UTF-8'
                                self.coding = 2
                                self.save_sms = 0
                                self.context = 'SMS_UNAUTH'
                                if not source_authorized:
                                    sms_log.info('Sender unauthorized send notification message')
                                    self.send(config['smsc'], source, config['sms_source_unauthorized'])
                                else:
                                    sms_log.info('Destination unauthorized inform sender with a notification message')
                                    self.send(config['smsc'], source, config['sms_destination_unauthorized'])

                except SubscriberException as e:
                    raise SMSException('Receive SMS error: %s' % e)
            else:
        
                # dest number is not local, check if dest number is a shortcode
                if destination in extensions_list:
                    sms_log.info('Destination number is a shortcode, execute shortcode handler')
                    extension = importlib.import_module('extensions.ext_'+destination, 'extensions')
                    try:
                        sms_log.debug('Exec shortcode handler')
                        extension.handler('', source, destination, text)
                    except ExtensionException as e:
                        raise SMSException('Receive SMS error: %s' % e)
                else:
                    # check if sms is for another location
                    if self.numbering.is_number_internal(destination) and len(destination) == 11:
                        sms_log.info('SMS is for another site')
                        try:
                            site_ip = self.numbering.get_site_ip(destination)
                            sms_log.info('Send SMS to site IP: %s' % site_ip)
                            self.context = 'SMS_INTERNAL'
                            self.send(source, destination, text, site_ip)
                        except NumberingException as e:
                            raise SMSException('Receive SMS error: %s' % e)
                    else:
                        # dest number is for an external number send sms to sms provider
                        self.context = 'SMS_OUTBOUND'
                        sms_log.info('SMS is for an external number send SMS to SMS provider')

        except NumberingException as e:
            raise SMSException('Receive SMS Error: %s' % e)
    
    def send(self, source, destination, text, server=config['local_ip']):
        enc_text = urllib.urlencode({'text': text })
        if server == config['local_ip']:
            try:
                sms_log.info('Send SMS: %s %s' % (source, destination))
                res = urllib.urlopen(
                    "http://%s:%d/cgi-bin/sendsms?username=%s&password=%s&charset=%s&coding=%s&to=%s&from=%s&%s"\
                    % (self.server, self.port, self.username, self.password, self.charset, self.coding, destination, source, enc_text)
                ).read()
                if self.save_sms:
                    sms_log.info('Save SMS in the history')
                    self.save(source, destination, self.context)
            except IOError:
                raise SMSException('Error connecting to Kannel to send SMS')
        else:
            try:
                sms_log.info('Send SMS to %s: %s %s' % (server, source, destination))
                values = {'source': source, 'destination': destination, 'charset': self.charset, 'coding': self.coding, 'text': text }
                data = urllib.urlencode(values)
                res = urllib.urlopen('http://%s:8085/sms' % server, data).read()
                if self.save_sms:
                    sms_log.info('Save SMS in the history')
                    self.save(source, destination, self.context)
            except IOError:
                raise SMSException('Error sending SMS to site %s' % server)

    def roaming(self, subject):
        
        self.numbering = Numbering()
        self.subscriber = Subscriber()

        if subject == 'caller':
            # calling number is roaming 
            # check if destination number is roaming as well
            if self.numbering.is_number_roaming(self.destination):
                # well destination number is roaming as well send SMS to current_bts where the subscriber is roaming
                try:
                    current_bts = self.numbering.get_current_bts(self.destination)
                    sms_log.info('Destination number is roaming send SMS to current_bts: %s' % current_bts)
                    if current_bts == config['local_ip']:
                        log.info('Current bts same as local site send call to local Kannel')
                        self.context = 'SMS_ROAMING_LOCAL'
                        self.send(self.source, self.destination, self.text)
                    else:
                        # send sms to destination site
                        self.context = 'SMS_ROAMING_INTERNAL'
                        self.send(self.source, self.destination, self.text, current_bts)
                except NumberingException as e:
                    sms_log.error(e)
            else:
                # destination is not roaming check if destination if local site
                if self.numbering.is_number_local(self.destination) and len(self.destination) == 11:
                    sms_log.info('Destination is a local number')

                    if self.subscriber.is_authorized(self.destination, 0):
                        sms_log.info('Send sms to local kannel')
                        self.context = 'SMS_ROAMING_LOCAL'
                        self.send(self.source, self.destination, self.text)
                    else:
                        # destination cannot receive SMS inform source
                        self.context = 'SMS_ROAMING_UNAUTH'
                        self.receive(config['smsc'], source, config['sms_destination_unauthorized'], self.charset, self.coding)
                else:
                    # number is not local check if number is internal
                    if self.numbering.is_number_internal(self.destination) and len(self.destination) == 11:
                        # number is internal send SMS to destination site
                        current_bts = self.numbering.get_site_ip(self.destination)
                        self.context = 'SMS_ROAMING_INTERNAL'
                        self.send(self.source, self.destination, self.text, current_bts)
                    else:
                        # check if number is for outbound.
                        # not implemented yet. just return
                        sms_log.info('Invalid destination for SMS')
                        return
        else:
            # the destination is roaming send call to current_bts
            try:
                current_bts = self.numbering.get_current_bts(self.destination)
                if current_bts == config['local_ip']:
                    sms_log.info('Destination is roaming on our site send SMS to local kannel')
                    self.context = 'SMS_ROAMING_LOCAL'
                    self.send(self.source, self.destination, self.text)
                else:
                    sms_log.info('Destination is roaming send sms to other site')
                    self.context = 'SMS_ROAMING_INTERNAL'
                    self.send(self.source, self.destination, self.text, current_bts)
            except NumberingException as e:
                sms_log.error(e)
                

    def save(self, source, destination, context):
        # insert SMS in the history
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO sms(source_addr,destination_addr,context) VALUES(%s,%s,%s)', (source, destination, context))
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise SMSException('PG_HLR error saving SMS in the history: %s' % e)
        finally:
            cur.close()
            db_conn.commit()

    def send_immediate(self, num, text):
        appstring = 'OpenBSC'
        appport = 4242
        vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
        cmd = 'subscriber extension %s sms sender extension %s send %s' % (num, config['smsc'], text)
        vty.command(cmd)

    def broadcast_to_all_subscribers(self, text, btype):
        sub = Subscriber()
        if btype == 'all':
            subscribers_list = sub.get_all()
        elif btype == 'notpaid':
            subscribers_list = sub.get_all_notpaid()
        elif btype == 'unauthorized':
            subscribers_list = sub.get_all_unauthorized()
        elif btype == 'extension':
            subscribers_list = sub.get_all_5digits()

        for mysub in subscribers_list:
            self.send(config['smsc'], mysub[1], text)
            sms_log.debug('Broadcast message sent to %s' % mysub[1])
            time.sleep(1)

    def send_broadcast(self, text, btype):
        sms_log.info('Send broadcast SMS to all subscribers. text: %s' % text)
        t = Thread(target=self.broadcast_to_all_subscribers, args=(text, btype, ))
        t.start()

    
if __name__ == '__main__':
    sms = SMS()
    try:
        sms.send('10000', '66666248674', 'test')
        #sms.receive('68820132107','777','3010#68820135624#10','UTF-8',2)
        #sms.send_broadcasit('antani')
    except SMSException as e:
        print "Error: %s" % e
