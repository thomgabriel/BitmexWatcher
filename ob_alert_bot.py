import telegram
from telegram.ext import Updater
import logging
import csv
import datetime as dt
from time import sleep
from logging.handlers import RotatingFileHandler
import os
import bitmex

TOKEN_CHATBOT = "1221497425:AAG_mEqgR-AtLKUZL6Jq3SA3UxvBRRwKIFs"
GROUP_CHAT_ID = "-1001373929421"
DATA_DIR = 'data/'

def setup_db(name, extension='.csv', getPath = False):
    """Setup writer that formats data to csv, supports multiple instances with no overlap."""
    formatter = logging.Formatter(fmt='%(asctime)s,%(message)s', datefmt='%d-%m-%y,%H:%M:%S')
    date = dt.datetime.today().strftime('%Y-%m-%d')
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
    
    if getPath:
        return logger, db_path
    else:
        return logger

def send_group_message(msg):
	bot = telegram.Bot(token=TOKEN_CHATBOT)
	bot.send_message(GROUP_CHAT_ID, text=msg)

def load_orders():
    try:
        with open(DATA_DIR + 'orders/orders' + '_' + dt.datetime.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
            readcsv = csv.reader(f, delimiter=',')
            orders = [row for row in  readcsv]
    except:
        orders = []        
    return orders

def InitialiseBot():
    
    print('QuanOrderBot is running...')
    
    updater = Updater(TOKEN_CHATBOT, use_context=True)
    updater.start_polling()
    while True:
        sleep(5)
        csv_logger = setup_db('order_telegram')
        try:
            with open(DATA_DIR + 'order_telegram/order_telegram' + '_' + dt.datetime.today().strftime('%Y-%m-%d') + '.csv' , 'r') as f:
                readcsv = csv.reader(f, delimiter=',')
                orderscsv = [row[2] for row in readcsv]
        except:
            ordercsv = []

        for order in load_orders():
            if order[4] in orderscsv:
                pass
            else:
                if float(order[5]) >= 0.08:
                    send_group_message(
                    '🐋🚨🚨🚨🚨🦏' + '\n' + 'There is a ' + order[3] + ' #XBT ' + ('BIDs' if float(order[2]) > float(order[6]) else 'ASKs') + 
                    ' at $' + order[2] + ' level.' + 
                    '\n' + str(round(((float(order[2])-float(order[6]))/float(order[6])*100),2)) + '%' + ' From Market Price.')
                    csv_logger.info("%s" %(order[4]))
                    sleep(1)
                elif 0.07<= float(order[5]) < 0.08:
                    send_group_message(
                    '🐋🚨🚨🚨🦏' + '\n' + 'There is a ' + order[3] + ' #XBT ' + ('BIDs' if float(order[2]) > float(order[6]) else 'ASKs') + 
                    ' at $' + order[2] + ' level.' + 
                    '\n' + str(round(((float(order[2])-float(order[6]))/float(order[6])*100),2)) + '%' + ' From Market Price.')
                    csv_logger.info("%s" %(order[4]))
                    sleep(1)
                elif 0.06<= float(order[5]) < 0.07:
                    send_group_message(
                    '🐋🚨🚨🦏' + '\n' + 'There is a ' + order[3] + ' #XBT ' + ('BIDs' if float(order[2]) > float(order[6]) else 'ASKs') + 
                    ' at $' + order[2] + ' level.' + 
                    '\n' + str(round(((float(order[2])-float(order[6]))/float(order[6])*100),2)) + '%' + ' From Market Price.')
                    csv_logger.info("%s" %(order[4]))
                    sleep(1)
                elif 0.05<= float(order[5]) < 0.06:
                    send_group_message(
                    '🐋🚨🦏' '\n' + 'There is a ' + order[3] + ' #XBT ' + ('BIDs' if float(order[2]) > float(order[6]) else 'ASKs') + 
                    ' at $' + order[2] + ' level.' + 
                    '\n' + str(round(((float(order[2])-float(order[6]))/float(order[6])*100),2)) + '%' + ' From Market Price.')
                    csv_logger.info("%s" %(order[4]))
                    sleep(1)

if __name__ == '__main__':
    InitialiseBot()
