from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from os import environ

environ['HOME'] = '~/home/cis/Desktop/pybit'

from bmconfigparser import BMConfigParser
from helper_ackPayload import genAckPayload
from addresses import decodeAddress, addBMIfNotPresent
from class_sqlThread import sqlThread
from helper_sql import sqlQuery, sqlExecute, sqlExecuteChunked, sqlStoredProcedure
import time
statusIconColor = 'red'


class Login_Screen(BoxLayout):


    def send(self):

        fromAddress = "BM-2cXxMHUdyqGESttuTwzQUKCFLZNfVjoon2"
        toAddress = "BM-2cWF9TNuK5zfgnB6z4F7JJ5KizBRivDevp"
        message = self.ids.user_input.text
        subject = 'Test'
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4")
        print("################################################################")
        encoding = 3
        print("message: ", self.ids.user_input.text)
        sendMessageToPeople = True
        if sendMessageToPeople:
            if toAddress != '':
                status, addressVersionNumber, streamNumber, ripe = decodeAddress(toAddress)
                if status == 'success':
                    toAddress = addBMIfNotPresent(toAddress)

                    if addressVersionNumber > 4 or addressVersionNumber <= 1:
                        print("addressVersionNumber > 4 or addressVersionNumber <= 1")
                    if streamNumber > 1 or streamNumber == 0:
                        print("streamNumber > 1 or streamNumber == 0")
                    if statusIconColor == 'red':
                        print("shared.statusIconColor == 'red'")
                    stealthLevel = BMConfigParser().safeGetInt(
                        'bitmessagesettings', 'ackstealthlevel')
                    ackdata = genAckPayload(streamNumber, stealthLevel)
                    t = ()
                    sqlLookup = sqlThread()
                    sqlLookup.daemon = False  # DON'T close the main program even if there are threads left. The closeEvent should command this thread to exit gracefully.
                    sqlLookup.start()
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
                    print("sqlExecute successfully #######################")

                    aa = App.get_running_app()
                    aa.Exit()

class MainApp(App):

    def build(self):
        return Login_Screen()


if __name__ == '__main__':
    MainApp().run()
