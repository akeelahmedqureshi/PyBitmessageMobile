import time
from helper_sql import *
from helper_ackPayload import genAckPayload
from addresses import *
import ConfigParser
from bmconfigparser import BMConfigParser
from class_sqlThread import sqlThread
sqlLookup = sqlThread()
sqlLookup.start()

def send_apk_message():
    encoding = 3

    from bitmessageqt.account import accountClass
    message = "hello".encode('base64')
    sendMessageToPeople = True
    fromAddress = "BM-2cWYjpG3jK72mTcwGLjDhQPbx5eXjrqkaf"
    toAddresses = "BM-2cUUx8HDzZkD6RTR4N6av5oUJZtmZFe8oR"
    subject = 'subject!'.encode('base64')
    acct = accountClass(fromAddress)

    if sendMessageToPeople: # To send a message to specific people (rather than broadcast)
        toAddressesList = [s.strip()
                           for s in toAddresses.replace(',', ';').split(';')]
        toAddressesList = list(set(
            toAddressesList))  # remove duplicate addresses. If the user has one address with a BM- and the same address without the BM-, this will not catch it. They'll send the message to the person twice.
        for toAddress in toAddressesList:
            print(toAddress)
            if toAddress != '':

                status, addressVersionNumber, streamNumber, ripe = decodeAddress(
                    toAddress)
                print(status)
                if status == 'success':
                    try:
                        toAddress = unicode(toAddress, 'utf-8', 'ignore')
                    except:
                        pass
                    toAddress = addBMIfNotPresent(toAddress)
                    stealthLevel = BMConfigParser().safeGetInt(
                        'bitmessagesettings', 'ackstealthlevel')
                    ackdata = genAckPayload(streamNumber, stealthLevel)
                    t = ()
                    sqlExecute(
                        '''INSERT INTO sent VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        '',
                        toAddress,
                        ripe,
                        fromAddress,
                        subject,
                        message,
                        ackdata,
                        int(time.time()), # sentTime (this will never change)
                        int(time.time()), # lastActionTime
                        0, # sleepTill time. This will get set when the POW gets done.
                        'msgqueued',
                        0, # retryNumber
                        'sent', # folder
                        encoding, # encodingtype
                        BMConfigParser().getint('bitmessagesettings', 'ttl')
                        )

send_apk_message()
