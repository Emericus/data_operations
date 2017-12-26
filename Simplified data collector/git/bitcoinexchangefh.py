#!/bin/python

import sys

from exchange import ExchangeGateway
# from exch_bitmex import ExchGwBitmex
from exch_bitfinex import ExchGwBitfinex
# from exch_kraken import ExchGwKraken
# from exch_gdax import ExchGwGdax
# from exch_bitstamp import ExchGwBitstamp
# from exch_poloniex import ExchGwPoloniex
# from exch_bittrex import ExchGwBittrex
# from exch_cryptopia import ExchGwCryptopia
from mysql_client import MysqlClient
from subscription_manager import SubscriptionManager
from util import Logger


def main2(**kwargs):
    output = kwargs['output']
    mysqldest = kwargs['mysqldest']
    mysql = kwargs['mysql']
    mysqlschema = kwargs['mysqlschema']
    instmts = kwargs['instmts']
    exchtime = kwargs['exchtime']
    Logger.init_log(output)

    db_clients = []
    is_database_defined = False
    if mysql:
        db_client = MysqlClient()
        logon_credential = mysqldest.split('@')[0]
        connection = mysqldest.split('@')[1]
        db_client.connect(host=connection.split(':')[0],
                          port=int(connection.split(':')[1]),
                          user=logon_credential.split(':')[0],
                          pwd=logon_credential.split(':')[1],
                          schema=mysqlschema)
        db_clients.append(db_client)
        is_database_defined = True

    if not is_database_defined:
        print('Error: Please define which database is used.')
        sys.exit(1)

    # Subscription instruments
    if instmts is None or len(instmts) == 0:
        print('Error: Please define the instrument subscription list. You can refer to subscriptions.ini.')
        sys.exit(1)

    # Use exchange timestamp rather than local timestamp
    if exchtime:
        ExchangeGateway.is_local_timestamp = False

    # Initialize subscriptions
    subscription_instmts = SubscriptionManager(instmts).get_subscriptions()
    if len(subscription_instmts) == 0:
        print('Error: No instrument is found in the subscription file. ' +
              'Please check the file path and the content of the subscription file.')
        sys.exit(1)

    # Initialize snapshot destination
    ExchangeGateway.init_snapshot_table(db_clients)

    Logger.info('[main]', 'Subscription file = %s' % instmts)
    log_str = 'Exchange/Instrument/InstrumentCode:\n'
    for instmt in subscription_instmts:
        log_str += '%s/%s/%s\n' % (instmt.exchange_name, instmt.instmt_name, instmt.instmt_code)
    Logger.info('[main]', log_str)

    exch_gws = []
    exch_gws.append(ExchGwBitfinex(db_clients))
    threads = []
    for exch in exch_gws:
        for instmt in subscription_instmts:
            if instmt.get_exchange_name() == exch.get_exchange_name():
                Logger.info("[main]", "Starting instrument %s-%s..." % \
                            (instmt.get_exchange_name(), instmt.get_instmt_name()))
                threads += exch.start(instmt)


if __name__ == '__main__':
    # main()
    main2(output='log.txt', mysqldest='user:pw@url:3306',
          mysql=True, mysqlschema='schema_name', instmts='subscriptions.ini', exchtime=False)

