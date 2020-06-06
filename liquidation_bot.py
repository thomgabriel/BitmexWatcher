import telegram
from telegram.ext import Updater
import logging
import csv
from datetime import datetime as dt
import datetime
from time import sleep
from logging.handlers import RotatingFileHandler
import os
import schedule
import sys
from ws import BitMEXWebsocket

TOKEN_CHATBOT = "1009370354:AAHSwXPOTYJ1fnHRDETw9W9JrJWF96CvRQ8"
GROUP_CHAT_ID = "-1001373929421"
DATA_DIR = 'data/'

ws = BitMEXWebsocket()
liquidations = []
announcements = []

def setup_db(name, extension='.csv'):
    """Setup writer that formats data to csv, supports multiple instances with no overlap."""
    formatter = logging.Formatter(fmt='%(asctime)s,%(message)s', datefmt='%d-%m-%y,%H:%M:%S')
    date = dt.today().strftime('%Y-%m-%d')
    db_path = str(DATA_DIR + name + '/' + name + '_' + date + extension)

    handler = RotatingFileHandler(db_path, backupCount=1)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

def send_group_message(msg):
	bot = telegram.Bot(token=TOKEN_CHATBOT)
	bot.send_message(GROUP_CHAT_ID, text=msg)

def load_orders():
    global liquidations, announcements
    try:
        with open(DATA_DIR + 'liquidation/liquidation' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
            readcsv = csv.reader(f, delimiter=',')
            liquidations = [row for row in readcsv]
    except:
        liquidations = []  
    try:
        with open(DATA_DIR + 'announcements/announcements' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
            readcsv = csv.reader(f, delimiter=',')
            announcements = [row for row in readcsv]
    except:
        announcements = []       
    return 

def dailymessage():
    
    try:
        with open(DATA_DIR + 'liquidation/liquidation' + '_' + (dt.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') + '.csv' , 'r') as f:
            readcsv = csv.reader(f, delimiter=',')
            m_liquidations = [row for row in readcsv]
    except:
        m_liquidations = [] 

    dailymessage = (
        'Liquidation Daily Report:' + '\n' +
        ('⛔️⛔️⛔️') if (sum([float(order[6]) for order in m_liquidations if order[4] == ' Buy']) < sum([float(order[6]) for order in m_liquidations 
        if order[4] == ' Sell'])) else ('❎❎❎') + '\n' + '\n' +

        str(len(m_liquidations)) + ' Liquidations in total today, worth $' + str("{:,}".format(round(sum([float(order[6]) for order in m_liquidations]),2))) 
        + '.' + '\n' + '\n' +

        '🍏 $' + str("{:,}".format(round(sum([float(order[6]) for order in m_liquidations if order[4] == ' Buy']),2))) + ' in ' +  
        str(len([order for order in m_liquidations if order[4] == ' Buy'])) + ' Short contracts Liquidated. ' + '\n' + '\n' +

        '🍎 $' + str("{:,}".format(round(sum([float(order[6]) for order in m_liquidations if order[4] == ' Sell']),2))) + ' in ' +  
        str(len([order for order in m_liquidations if order[4] == ' Sell'])) + ' Long contracts Liquidated.')
    
    return dailymessage
 
def InitialiseBot():
    
    print('QuanLiquidationBot is running...')
    updater = Updater(TOKEN_CHATBOT, use_context=True)
    updater.start_polling()

    liquidation_logger = setup_db('liquidation_telegram')
    announcements_logger = setup_db('announcements_telegram')
        
   # Daily Report
    schedule.every().day.at("00:01").do(send_group_message, dailymessage())

    while (True):
        load_orders()
        schedule.run_pending()

        # If day changes, restart
        liq_path = str(DATA_DIR + 'liquidation_telegram/liquidation_telegram' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv')
        ann_path = str(DATA_DIR + 'announcements_telegram/announcements_telegram' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv')
        if not(os.path.exists(liq_path) or os.path.exists(ann_path)):
            liquidation_logger.removeHandler(liquidation_logger.handlers[0])
            announcements_logger.announcements_logger(announcements_logger.handlers[0])
            liquidation_logger = setup_db('liquidation_telegram')
            announcements_logger = setup_db('announcements_telegram')
        
        try:
            with open(DATA_DIR + 'liquidation_telegram/liquidation_telegram' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
                readcsv = csv.reader(f, delimiter=',')
                liquidation_csv = [row[2] for row in readcsv]
        except:
            liquidation_csv = [] 
        try:
            with open(DATA_DIR + 'announcements_telegram/announcements_telegram' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
                readcsv = csv.reader(f, delimiter=',')
                announcement_csv = [row[2] for row in readcsv]
        except:
            announcement_csv = []
            
        for order in liquidations:
            if float(order[6]) > 200000:
                if order[2] in liquidation_csv:
                    pass
                else:
                    if order[4] == ' Buy':
                        send_group_message(
                        '🍏 Liquidated Short: ' + str("{:,}".format(round(float(order[6]), 2))) + ' #XBT Contracts at $' + order[5])
                        liquidation_logger.info("%s" %(order[2]))
                        sleep(2)
                   
                    if order[4] == ' Sell':
                        send_group_message(
                        '🍎 Liquidated Long: ' + str("{:,}".format(round(float(order[6]), 2))) + ' #XBT Contracts at $' + order[5])
                        liquidation_logger.info("%s" %(order[2]))
                        sleep(2)

        for anun in announcements:
            if anun[2] in announcement_csv:
                pass
            else:
                send_group_message(
                    '❗️❗️❗️' + '\n' + '**' + anun[4] + '.**' + '\n' + 'Link: ' + anun[3]
                )
                announcements_logger.info("%s" %(order[2]))

        sleep(5)
                       
if __name__ == '__main__':
    try:
        InitialiseBot()
    
    except (KeyboardInterrupt, SystemExit):
            send_group_message('Error')
            sys.exit()