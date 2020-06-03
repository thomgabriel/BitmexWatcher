import websocket
import threading
import traceback
from time import sleep
import json
import logging
import urllib
import math
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt
import os
import csv

DATA_DIR = 'data/'
MAX_TABLE_LEN = 200

def setup_db(name, extension='.csv', getPath = False):
    """Setup writer that formats data to csv, supports multiple instances with no overlap."""
    formatter = logging.Formatter(fmt='%(asctime)s,%(message)s', datefmt='%d-%m-%y,%H:%M:%S')
    date = dt.today().strftime('%Y-%m-%d')
    db_path = str(DATA_DIR + name + '/' + name + '_' + date + extension)

    handler = RotatingFileHandler(db_path, backupCount=1)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    if getPath:
        return logger, db_path
    else:
        return logger

def is_file_empty(file_path):
    """ Check if file is empty by confirming if its size is 0 bytes"""
    return os.path.exists(file_path) and os.stat(file_path).st_size == 0

class BitMEXWebsocket:

    def __init__(self, wsURL = 'wss://www.bitmex.com/realtime?subscribe=liquidation:XBTUSD,announcement,tradeBin1m:XBTUSD'):
        '''Connect to the websocket and initialize data stores.'''
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing WebSocket.")

        self.data = {}
        self.keys = {}
        self.exited = False

        self.liquidation_logger, log_path = setup_db('liquidation', getPath=True)
        self.announcement_logger, log_path = setup_db('announcement', getPath=True)
        
        if log_path:
            if is_file_empty(log_path):
                self.logger.debug('Files empty, writing headers.')
                self.write_headers()
        
        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        
        self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL)
        self.logger.info('Connected to WS.')
        sleep(2)
        self.logger.info('Starting...')
        sleep(1)

    def reset(self):
        self.logger.warning('Websocket resetting...')
        self.ws.close()
        self.logger.info('Weboscket closed.')
        self.logger.info('Restarting...')
        self.__init__()

    def __connect(self, wsURL):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Starting thread")

        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error
                                         )
        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()
        self.logger.debug("Started thread")

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.reset()

    def __on_message(self, message):
     
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        
        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            if 'subscribe' in message:
                if message['success']:
                    self.logger.debug("Subscribed to %s." % message['subscribe'])
                else:
                    self.error("Unable to subscribe to %s. Error: \"%s\"" %
                               (message['request']['args'][0], message['error']))
            elif action:
                if table not in self.data:
                    self.data[table] = []

                elif action == 'insert':
                    self.logger.debug('%s: inserting %s' % (table, message['data']))
                    self.data[table] += message['data']
                    
                    if table == 'liquidation':
                        data = message['data'][0]
                        self.liquidation_logger.info('%s, %s, %s, %s, %s' % (data['orderID'], data['symbol'], 
                        data['side'], data['price'], data['leavesQty']))
                    elif table == 'announcement':
                        data = message['data'][0]
                        self.announcement_logger.info(' %s, %s, %s' %
                        (data['id'],data['link'], data['title']))

                    if len(self.data[table]) > MAX_TABLE_LEN:
                        self.data[table] = self.data[table][MAX_TABLE_LEN // 2:]    
        except:
            self.logger.error(traceback.format_exc())

    def __on_error(self, error):
        '''Called on fatal websocket errors. We exit on these.'''
        if not self.exited:
            self.logger.error("Error : %s" % error)
            raise websocket.WebSocketException(error)

    def __on_open(self):
        '''Called when the WS opens.'''
        self.logger.debug("Websocket Opened.")

    def __on_close(self):
        '''Called on websocket close.'''
        self.logger.info('Websocket Closed')

    def write_headers(self):
        self.liquidation_logger.info('%s, %s, %s, %s, %s' % ('orderID', 'symbol','side','price','leavesQty'))
        self.announcement_logger.info('%s, %s, %s' % ('id', 'link','title'))


