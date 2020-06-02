import telegram
from telegram.ext import Updater
import logging
import csv
from datetime import datetime as dt
from time import sleep
from logging.handlers import RotatingFileHandler
import os
import schedule
import sys
from ws import BitMEXWebsocket

TOKEN_CHATBOT = "1009370354:AAHSwXPOTYJ1fnHRDETw9W9JrJWF96CvRQ8"
GROUP_CHAT_ID = "-1001373929421"
DATA_DIR = 'data/'

liquidations = []
trades = []

def setup_db(name, extension='.csv'):
    """Setup writer that formats data to csv, supports multiple instances with no overlap."""
    formatter = logging.Formatter(fmt='%(asctime)s,%(message)s', datefmt='%d-%m-%y,%H:%M:%S')
    date = dt.today().strftime('%Y-%m-%d')
    db_path = str(DATA_DIR + name + '/' + name + '_' + date + extension)

    handler = RotatingFileHandler(db_path, backupCount=1)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if (logger.hasHandlers()):
        logger.handlers.clear()
        logger.addHandler(handler)
    else:
        logger.addHandler(handler)
    return logger

    liquidation_logger = setup_db('liquidation_telegram')
    trade_logger = setup_db('trade_telegram')
    ws = BitMEXWebsocket()

def send_group_message(msg):
	bot = telegram.Bot(token=TOKEN_CHATBOT)
	bot.send_message(GROUP_CHAT_ID, text=msg)

def load_orders():
    global liquidations, trades
    try:
        with open(DATA_DIR + 'liquidation/liquidation' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
            readcsv = csv.reader(f, delimiter=',')
            liquidations = [row for row in readcsv][1:]
    except:
        liquidations = []   

    try:
        with open(DATA_DIR + 'trade/trade' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
            readcsv = csv.reader(f, delimiter=',')
            trades = [row for row in readcsv][1:]
    except:
        trades = []      
    return 
        
def InitialiseBot():
    
    print('QuanLiquidationBot is running...')
    updater = Updater(TOKEN_CHATBOT, use_context=True)
    updater.start_polling()

    # Daily Report
    schedule.every().day.at("23:59").do(send_group_message,
        ('Liquidation Daily Report:' + '\n' +
        ('⛔️⛔️⛔️' if (sum([float(order[6]) for order in liquidations if order[4] == ' Buy']) < sum([float(order[6]) for order in liquidations 
        if order[4] == ' Sell'])) else '❎❎❎') + '\n' + '\n' +

        str(len(liquidations)) + ' Liquidations in total today worth $' + str("{:,}".format(round(sum([float(order[6]) for order in liquidations]),2))) 
        + '.' + '\n' + '\n' +

        '🍏 $' + str("{:,}".format(round(sum([float(order[6]) for order in liquidations if order[4] == ' Buy']),2))) + ' in ' +  
        str(len([order for order in liquidations if order[4] == ' Buy'])) + ' Short contracts Liquidated. ' + '\n' + '\n' +

        '🍎 $' + str("{:,}".format(round(sum([float(order[6]) for order in liquidations if order[4] == ' Sell']),2))) + ' in ' +  
        str(len([order for order in liquidations if order[4] == ' Sell'])) + ' Long contracts Liquidated.'))
        
    while (True):
        load_orders()
        schedule.run_pending()

        try:
            with open(DATA_DIR + 'liquidation_telegram/liquidation_telegram' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
                readcsv = csv.reader(f, delimiter=',')
                liquidation_csv = [row[2] for row in readcsv]
        except:
            liquidation_csv = [] 
        try:
            with open(DATA_DIR + 'trade_telegram/trade_telegram' + '_' + dt.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
                readcsv = csv.reader(f, delimiter=',')
                trade_csv = [row[2] for row in readcsv]
        except:
            trade_csv = []
            
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

        for order in trades:
                if order[2] in trade_csv:
                    pass
                else:
                    if order[4] == ' Buy':
                        send_group_message(
                        '🟢 Market Buy: ' + str("{:,}".format(round(float(order[6]), 2))) + ' #XBT Contracts bought at $' + order[5])
                        trade_logger.info("%s" %(order[2]))
                        sleep(2)
                   
                    if order[4] == ' Sell':
                        send_group_message(
                        '🔴 Market Sell: ' + str("{:,}".format(round(float(order[6]), 2))) + ' #XBT Contracts sold at $' + order[5])
                        trade_logger.info("%s" %(order[2]))
                        sleep(2)
        sleep(5)
                       
if __name__ == '__main__':
    try:
        InitialiseBot()
    
    except (KeyboardInterrupt, SystemExit):
            send_group_message('Error')
            sys.exit()