from bmconfigparser import BMConfigParser
from helper_sql import *


class AccountMixin(object):
    ALL = 0
    NORMAL = 1
    CHAN = 2
    MAILINGLIST = 3
    SUBSCRIPTION = 4
    BROADCAST = 5