import queues
import re
import sys
import inspect
# from helper_sql import *
from helper_sql import sqlQuery, sqlExecute, sqlExecuteChunked, sqlStoredProcedure
from bmconfigparser import BMConfigParser
import time
from addresses import decodeAddress
from foldertree import AccountMixin
from helper_ackPayload import genAckPayload
from openssl import OpenSSL
str_broadcast_subscribers = '[Broadcast subscribers]'


def accountClass(address):
    if not BMConfigParser().has_section(address):
        if address == str_broadcast_subscribers:
            subscription = BroadcastAccount(address)
            if subscription.type != AccountMixin.BROADCAST:
                return None
        else:
            subscription = SubscriptionAccount(address)
            if subscription.type != AccountMixin.SUBSCRIPTION:
                return NoAccount(address)
        return subscription
    try:
        gateway = BMConfigParser().get(address, "gateway")
        for name, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if issubclass(cls, GatewayAccount) and cls.gatewayName == gateway:
                return cls(address)
        return GatewayAccount(address)
    except:
        pass
    return BMAccount(address)
    
   
class BMAccount(object):
    def __init__(self, address = None):
        self.address = address
        self.type = AccountMixin.NORMAL
        if BMConfigParser().has_section(address):
            if BMConfigParser().safeGetBoolean(self.address, 'chan'):
                self.type = AccountMixin.CHAN
            elif BMConfigParser().safeGetBoolean(self.address, 'mailinglist'):
                self.type = AccountMixin.MAILINGLIST
        elif self.address == str_broadcast_subscribers:
            self.type = AccountMixin.BROADCAST
        else:
            queryreturn = sqlQuery(
                '''select label from subscriptions where address=?''', self.address)
            if queryreturn:
                self.type = AccountMixin.SUBSCRIPTION

    def getLabel(self, address = None):
        if address is None:
            address = self.address
        label = address
        if BMConfigParser().has_section(address):
            label = BMConfigParser().get(address, 'label')
        queryreturn = sqlQuery(
            '''select label from addressbook where address=?''', address)
        if queryreturn != []:
            for row in queryreturn:
                label, = row
        else:
            queryreturn = sqlQuery(
                '''select label from subscriptions where address=?''', address)
            if queryreturn != []:
                for row in queryreturn:
                    label, = row
        return label
        
    def parseMessage(self, toAddress, fromAddress, subject, message):
        self.toAddress = toAddress
        self.fromAddress = fromAddress
        if isinstance(subject, unicode):
            self.subject = str(subject)
        else:
            self.subject = subject
        self.message = message
        self.fromLabel = self.getLabel(fromAddress)
        self.toLabel = self.getLabel(toAddress)


class NoAccount(BMAccount):
    def __init__(self, address = None):
        self.address = address
        self.type = AccountMixin.NORMAL

    def getLabel(self, address = None):
        if address is None:
            address = self.address
        return address

        
class SubscriptionAccount(BMAccount):
    pass
    

class BroadcastAccount(BMAccount):
    pass
        
        
class GatewayAccount(BMAccount):
    gatewayName = None
    ALL_OK = 0
    REGISTRATION_DENIED = 1
    def __init__(self, address):
        super(GatewayAccount, self).__init__(address)
        
    def send(self):
        status, addressVersionNumber, streamNumber, ripe = decodeAddress(self.toAddress)
        stealthLevel = BMConfigParser().safeGetInt('bitmessagesettings', 'ackstealthlevel')
        ackdata = genAckPayload(streamNumber, stealthLevel)
        t = ()
        sqlExecute(
            '''INSERT INTO sent VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            '',
            self.toAddress,
            ripe,
            self.fromAddress,
            self.subject,
            self.message,
            ackdata,
            int(time.time()), # sentTime (this will never change)
            int(time.time()), # lastActionTime
            0, # sleepTill time. This will get set when the POW gets done.
            'msgqueued',
            0, # retryNumber
            'sent', # folder
            2, # encodingtype
            min(BMConfigParser().getint('bitmessagesettings', 'ttl'), 86400 * 2) # not necessary to have a TTL higher than 2 days
        )

        queues.workerQueue.put(('sendmessage', self.toAddress))
    
    def parseMessage(self, toAddress, fromAddress, subject, message):
        super(GatewayAccount, self).parseMessage(toAddress, fromAddress, subject, message)
