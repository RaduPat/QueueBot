from discord.ext import commands, tasks
from discord.utils import get
import json
from os import listdir
from os.path import isfile, join
import discord
import pdb
from datetime import datetime, timedelta

import re


ORDERS = "orders/"
CHANNELS = "channels/"
ASSOCIATIONS = 'associations.json'
def get_order(order_id, folder):
    filename = f"{order_id}.json"
    try:
        with open(f"{folder}{filename}", "r") as f:
            data = json.load(f)
            f.close()
            return data
    except:
        return None

def getticket(channel, tickets):
    for ticket in tickets:
        if ticket['ticketMention'] == channel.mention:
            return ticket
    return None

def get_associations(file_path):
    with open(f"{file_path}", "r") as f:
        data = json.load(f)
        f.close()
        return data

def is_valid_id(order_id, folder):
    filename = f"{order_id}.json"
    orders = [f for f in listdir(folder) if isfile(join(folder, f))]
    return True if filename in orders else False

def get_num_from_amount(str_amount):
    multi = 1
    if str_amount[-1] == "k":
        multi = 1000
    elif str_amount[-1] == "m":
        multi = 1000000
    return float(str_amount[:-1]) * multi

def get_raids(raidNumber,orderIndex, channeldata,order,boosterList,total, number = None):
    if number is None:
        channeldata["raids"][str(raidNumber+1)] = {"boosters":[booster.id for booster in boosterList],"type":"regular",
                    "kc_number":order["progress"]+1,"order":order["order_id"],"processed":False}
        channeldata["orders"][orderIndex] = order
        order["progress"]+=1
        if (order["progress"] + order["kc"]) == order["total_kc"]:
            order["is_active"] = False        
        return channeldata,order
    else:
        for i in range(1,int(number)+1):
            channeldata["raids"][str(raidNumber+i)] = {"boosters":[booster.id for booster in boosterList],"type":"regular",
            "kc_number":order["progress"]+1,"order":order["order_id"],"processed":False}
            channeldata["orders"][orderIndex] = order
            order["progress"]+=1
            if (order["progress"] + order["kc"]) == order["total_kc"]:
                order["is_active"] = False    
        return channeldata,order

    

def get_remaining_boosts(data):
    req_boosts = int(data["order"]["req_boosts"])
    if "boosts" not in data:
        com_boosts = 0
    else:
        com_boosts = len(data["boosts"])
    return com_boosts, req_boosts

def create_channel_entry(channelID, data, isAssociation=False, team_size=None):
    filename = f"{channelID}.json"
    with open(f"{CHANNELS}{filename}", "w") as f:
        if isAssociation:
            dumpdata = data
        else:
            if team_size is None:
                dumpdata = {"orders":[data],"raids":{},"processed":True}
            else:
                dumpdata = {"orders":[data],"raids":{},"processed":True,"team_size":team_size}
        json.dump(dumpdata,f,indent=4)

def create_associations_entry(data):
    with open(f"{ASSOCIATIONS}", "w") as f:
        dumpdata = data
        json.dump(dumpdata,f,indent=4)

def update_channel_entry(channelID, data):
    filename = f"{channelID}.json"
    with open(f"{CHANNELS}{filename}", "w") as f:
        json.dump(data,f,indent=4)
    
def get_channel_order(orders, ordertype):
    active_orders = []
    for orderIndex in range(0,len(orders)):
        order = orders[orderIndex]
        if order['is_active']:
            if ordertype == order['type']:
                return order, orderIndex
    return None, None

def get_boost_commands(df):
    result = df.groupby(['order', 'team']).agg({'count': ['sum']}).reset_index()
    commands = []
    for index in range(0,len(result)):
        order = result['order']._get_value(index)
        team = result['team']._get_value(index)
        count = result['count']['sum']._get_value(index)
        commands.append(f'-boost {order} {count} {team}')
    return commands


def get_embed(ctx):
    embedMsg = discord.Embed(color=0x00ff00)
    embedMsg.set_author(name=ctx.author.name,icon_url= ctx.author.avatar_url)
    embedMsg.set_thumbnail(url='https://cdn.discordapp.com/attachments/725874308089643112/747078186411491429/pvmservicesgif.gif')
    return embedMsg