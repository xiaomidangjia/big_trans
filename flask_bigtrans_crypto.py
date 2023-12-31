
# coding: utf-8

import json
import base64
from flask import Flask, request
import requests
import numpy as np
import pandas as pd
import csv
from datetime import datetime
import sys
import os
import urllib
import time
import random
import hmac
import datetime as dt
app = Flask(__name__)

# 第二个log日志打印接口,每隔60s打印一次
def get_timestamp():
    return int(time.time() * 1000)
def sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)
def pre_hash(timestamp, method, request_path, body):
    return str(timestamp) + str.upper(method) + request_path + body
def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'
    return url[0:-1]
def get_header(api_key, sign, timestamp, passphrase):
    header = dict()
    header['Content-Type'] = 'application/json'
    header['ACCESS-KEY'] = api_key
    header['ACCESS-SIGN'] = sign
    header['ACCESS-TIMESTAMP'] = str(timestamp)
    header['ACCESS-PASSPHRASE'] = passphrase
    # header[LOCALE] = 'zh-CN'
    return header

@app.route("/dy_crypto_bigtrans", methods=['post'])
def dy_crypto_bigtrans():
    date = request.form.get('date')
    api_key_value = request.form.get('api_key')
    order_value = request.form.get('order_value')
    ip_addr = request.remote_addr
    api_key = 'JnpWaymbVKZs'
    API_URL = 'https://api.bitget.com'
    API_SECRET_KEY = "1f5394353875eb7589595285a1396845b9edccf3f7c308d83643427f61596e1d"
    API_KEY = "bg_c405cd3c115a6b1832c43cf1fad261f5"
    PASSPHRASE = "MMClianghua666"
    # 读取历史开单记录
    p = []
    with open("/root/whale-alert/res_alert.csv", 'r', encoding="UTF-8") as fr:
        reader = csv.reader(fr)
        for index, line in enumerate(reader):
            if index == 0:
                continue
            p.append(line)
    res_data = pd.DataFrame(p)
    res_data['date'] = res_data.iloc[:,0]
    res_data['crypto'] = res_data.iloc[:,1]
    res_data['exchange'] = res_data.iloc[:,2]
    res_data['number'] = res_data.iloc[:,3]
    res_data['value'] = res_data.iloc[:,4]
    res_data['hash'] = res_data.iloc[:,5]
    res_data = res_data[['date','crypto','exchange','number','value','hash']]
    res_data['value'] = res_data['value'].apply(lambda x:float(x))
    res_data['exchange'] = res_data['exchange'].apply(lambda x:x.lower())
    res_data = res_data[res_data.exchange=='coinbase']
    res_data['date'] = pd.to_datetime(res_data['date'])
    res_data = res_data.sort_values(by='date')
    res_data = res_data.reset_index(drop=True)
    now_time = str(datetime.utcnow())[0:19]
    up_time = res_data['date'][len(res_data)-1]
    end_time= datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')
    start_time= datetime.strptime(str(up_time), '%Y-%m-%d %H:%M:%S')
    # 计算时间差
    time_diff= end_time- start_time
    # 将时间差转换为分钟数
    minutes= time_diff.total_seconds() // 60
    if minutes >100:
        res_dict = {'value':'wrong','crypto_id':'A01','crypto_start_time':1,'crypto_time':'2023-01-01 10:20:30','crypto_direction':'other','crypto_open':1,'crypto_win':1,'crypto_loss':1,'finish':1}
    else:
        now_time1 = str(datetime.utcnow())[0:19]
        up_time1 = pd.to_datetime(now_time1) + dt.timedelta(hours=-1)
        sub_res_data_1 = res_data[res_data.date>up_time1]
        if len(sub_res_data_1) ==0:
            res_dict = {'value':'wrong','crypto_id':'A02','crypto_start_time':1,'crypto_time':'2023-01-01 10:20:30','crypto_direction':'other','crypto_open':1,'crypto_win':1,'crypto_loss':1,'finish':1}
        else:
            # 判断btc，usdt,usdc 的条数
            number = sub_res_data_1.groupby(['crypto'],as_index=False)['hash'].count()
            number = number.reset_index(drop=True)
            if len(number) == 1:
                w1 = 0 
                while w1 == 0:
                    timestamp = get_timestamp()
                    response = None
                    request_path = "/api/mix/v1/market/ticker"
                    url = API_URL + request_path
                    params = {"symbol":"BTCUSDT_UMCBL"}
                    request_path = request_path + parse_params_to_str(params)
                    url = API_URL + request_path
                    body = ""
                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                    response = requests.get(url, headers=header)
                    ticker = json.loads(response.text)
                    btc_price = float(ticker['data']['last'])
                    if btc_price > 0:
                        w1 = 1
                    else:
                        w1 = 0
                # 是稳定币
                if number['crypto'][0]=='USDT' or number['crypto'][0]=='USDC':
                    timestamp = int(time.time() * 1000)
                    c_id = 'A' + str(timestamp)
                    res_dict = {'value':'wrong','crypto_id':c_id,'crypto_start_time':timestamp,'crypto_time':now_time1,'crypto_direction':'open_long','crypto_open':btc_price,'crypto_win':1*1.005,'crypto_loss':1*0.985,'finish':0}
                else:
                # 是btc
                    sub_res_data_2 = sub_res_data_1[(sub_res_data_1.exchange=='coinbase') & (sub_res_data_1.value<3000)]
                    if len(sub_res_data_2) == 0:
                        # 不开
                        res_dict = {'value':'wrong','crypto_id':'A03','crypto_start_time':1,'crypto_time':'2023-01-01 10:20:30','crypto_direction':'other','crypto_open':1,'crypto_win':1,'crypto_loss':1,'finish':1}   
                    else:
                        # 开空
                        timestamp = int(time.time() * 1000)
                        c_id = 'A' + str(timestamp)
                        res_dict = {'value':'wrong','crypto_id':c_id,'crypto_start_time':timestamp,'crypto_time':now_time1,'crypto_direction':'open_short','crypto_open':btc_price,'crypto_win':1*0.995,'crypto_loss':1*1.015,'finish':0}
            else:
                res_dict = {'value':'wrong','crypto_id':'A04','crypto_start_time':1,'crypto_time':'2023-01-01 10:20:30','crypto_direction':'other','crypto_open':1,'crypto_win':1,'crypto_loss':1,'finish':1}                

    ans_str = json.dumps(res_dict)

    return ans_str

if __name__ == '__main__':
    app.run("0.0.0.0", port=5010)


