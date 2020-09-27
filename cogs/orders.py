from discord.ext import commands, tasks
from discord.utils import get
import json
from os import listdir
from os.path import isfile, join
import discord
import pdb
from datetime import datetime, timedelta
import re
import helpers as helper
from queueBot import ongoingTickets, config
import pandas as pd
ORDERS = "orders/"
CHANNELS = "channels/"
ASSOCIATIONS = 'associations.json'

class order(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def load(self, ctx, orderid, tickettype, team_size=None):
        channelID = ctx.channel.id
        if tickettype not in ["teacher","regular","t","r"]:
            ctx.send("incorrect ticket type passed. ACCEPTED values: teacher, regular, r, t")
            return
        try:
            if team_size is not None:
                team_size = int(team_size)
        except:
            ctx.send("incorrect team size passed")
            return         
        if helper.is_valid_id(orderid, ORDERS):
            #load order details
            orderdata = helper.get_order(orderid, ORDERS)
            associations = helper.get_associations(ASSOCIATIONS)
            remaining, total = helper.get_remaining_boosts(orderdata)
            orderdetails = {"order_id":str(orderid),"type":tickettype,"kc":int(remaining),"progress":0,"total_kc":int(total),
                            "is_active":bool(orderdata["order"]["is_active"])}
            foundorder = False
            if orderid.count("TOB") > 0:
                team_size = team_size if team_size is not None else 4
            else:
                team_size = None        
            if helper.is_valid_id(channelID,CHANNELS):
                channeldata = helper.get_order(channelID, CHANNELS)
                for orderindx in range(0,len(channeldata['orders'])):
                    if orderid == channeldata['orders'][orderindx]['order_id']:
                        foundorder = True
                if not foundorder:
                    associations['orders'][f'{orderid}'] = {'channel':channelID}
                    channeldata["orders"].append(orderdetails)
                    if team_size is not None:
                        channeldata["team_size"] = team_size
                    helper.update_channel_entry(channelID,channeldata)
                    helper.create_associations_entry(associations)
            else:
                associations['orders'][f'{orderid}'] = {'channel':channelID}
                helper.create_channel_entry(channelID,orderdetails,team_size=team_size)
                helper.create_associations_entry(associations)
        await ctx.message.delete()

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def unprocessed(self, ctx, number=None):
        orders = [f for f in listdir(CHANNELS) if isfile(join(CHANNELS, f))]
        results = []
        for channel in orders:
            channelID = channel.split('.')[0]
            channeldata = helper.get_order(channelID, CHANNELS)
            if channeldata['processed'] == False:
                results.append(f'<#{channelID}>')
                results.append(f'{channelID}')
        embedMsg = helper.get_embed(ctx)
        embedMsg.add_field(name='Unprocessed tickets',value='\u200b',inline=False)
        for chanid in results:
            embedMsg.add_field(name='\u200b',value=chanid,inline=False)
        await ctx.author.send(embed = embedMsg)

    @commands.command()
    @commands.has_any_role(*config['pvm'])
    async def kcn(self, ctx, number=None):
        try:
            if number is not None:
                int(number)
        except:
            await ctx.send("incorrect number passed")
            return
        channelID = ctx.channel.id
        boosterList = None
        for ticket in ongoingTickets:
            if channelID == ticket['channel'].id:
                boosterList = ticket['team']
        if helper.is_valid_id(channelID,CHANNELS) and boosterList is not None:
            channeldata = helper.get_order(channelID, CHANNELS)
            raidnumber = len(channeldata["raids"].keys())
            order,orderIndex = helper.get_channel_order(channeldata["orders"],"regular")
            if order is not None:
                total = order['total_kc']
                channeldata, order = helper.get_raids(raidnumber,orderIndex, channeldata,order, boosterList,total,number)
                if order["progress"]+order["kc"]>total:
                    await ctx.send("You have reached the total boosts allowed for this order")
                    return
                channeldata["processed"] = False
                helper.update_channel_entry(channelID,channeldata)
                data = f'{order["progress"]+order["kc"]}/{total} regular boosts'
                embedMsg = discord.Embed(color=0x00ff00)
                boosters = ''
                index = 0
                for boost in boosterList:
                    boosters = boosters + f' {boost.name}'
                    if index < len(boosterList)-1:
                        boosters = boosters + ' ・ '
                    index = index + 1
                embedMsg.add_field(name=f'{boosters}',value=data,inline=True)
                await ctx.send(embed =embedMsg)
            else:
                await ctx.send("no regular boosts available on this ticket")
                return				
        else:
            await ctx.send("ticket does not have any orders added to it, please load orders to the ticket or ticket is not ongoing")
        await ctx.message.delete()

    @commands.command()
    @commands.has_any_role(*config['pvm'])
    async def kc(self, ctx):
        channelID = ctx.channel.id
        boosterList = None
        for ticket in ongoingTickets:
            if channelID == ticket['channel'].id:
                boosterList = ticket['team']
        if helper.is_valid_id(channelID,CHANNELS) and boosterList is not None:
            channeldata = helper.get_order(channelID, CHANNELS)
            raidnumber = len(channeldata["raids"].keys())
            order,orderIndex = helper.get_channel_order(channeldata["orders"],"regular")
            if order is not None:
                total = order['total_kc']
                channeldata, order = helper.get_raids(raidnumber,orderIndex, channeldata,order, boosterList,total,None)
                if order["progress"]+order["kc"]>total:
                    await ctx.send("You have reached the total boosts allowed for this order")
                    return
                channeldata["processed"] = False
                helper.update_channel_entry(channelID,channeldata)
                data = f'{order["progress"]+order["kc"]}/{total} regular boosts'
                embedMsg = discord.Embed(color=0x00ff00)
                boosters = ''
                index = 0
                for boost in boosterList:
                    boosters = boosters + f' {boost.name}'
                    if index < len(boosterList)-1:
                        boosters = boosters + ' ・ '
                    index = index + 1
                embedMsg.add_field(name=f'{boosters}',value=data,inline=True)
                await ctx.send(embed =embedMsg)
            else:
                await ctx.send("no regular boosts available on this ticket")
                return				
        else:
            await ctx.send("ticket does not have any orders added to i or does not have a team assigned")
        await ctx.message.delete()

    @commands.command()
    @commands.has_any_role(*config['pvm'])
    async def undo(self, ctx):
        channelID = ctx.channel.id
        if helper.is_valid_id(channelID,CHANNELS):
            channeldata = helper.get_order(channelID, CHANNELS)
            raidnumber = len(channeldata["raids"].keys())
            order,orderIndex = helper.get_channel_order(channeldata["orders"],"regular")
            if raidnumber > 0 and order["progress"] > 0:
                raids = channeldata["raids"]
                raids.pop(str(raidnumber))
                channeldata["raids"] = raids
                order["progress"] = order["progress"] - 1
                channeldata["orders"][orderIndex] = order
                total = order['total_kc']
                data = f'{order["progress"]+order["kc"]}/{total} regular boosts'
                embedMsg = discord.Embed(color=0x00ff00)
                embedMsg.add_field(name='Removed 1 KC, new progress:',value=data,inline=True)
                await ctx.send(embed =embedMsg)
                helper.update_channel_entry(channelID,channeldata)
            else:
                await ctx.send('No progress made on this session')
        else:
                await ctx.send('This channel has no orders loaded')
        await ctx.message.delete()

    @commands.command()
    @commands.has_any_role(*config['general'])
    async def teacher(self, ctx):
        channelID = ctx.channel.id
        boosterList = None
        for ticket in ongoingTickets:
            if channelID == ticket['channel'].id:
                boosterList = ticket['team']
        if helper.is_valid_id(channelID,CHANNELS) and boosterList is not None:
            channeldata = helper.get_order(channelID, CHANNELS)
            raidnumber = len(channeldata["raids"].keys())
            order,orderIndex = helper.get_channel_order(channeldata["orders"],"teacher")
            if order is not None:
                total = order['total_kc']
                channeldata, order = helper.get_raids(raidnumber,orderIndex, channeldata,order, boosterList,total,None)
                if order["progress"]+order["kc"]+1>total:
                    await ctx.send("You have reached the total boosts allowed for this order")
                channeldata["processed"] = False
                helper.update_channel_entry(channelID,channeldata)
                data = f'{order["progress"]+order["kc"]}/{total} teacher boosts'
                embedMsg = discord.Embed(color=0x00ff00)
                boosters = ''
                index = 0
                for boost in boosterList:
                    boosters = boosters + f' {boost.name}'
                    if index < len(boosterList)-1:
                        boosters = boosters + ' ・ '
                    index = index + 1
                embedMsg.add_field(name=f'{boosters}',value=data,inline=True)
                await ctx.send(embed =embedMsg)
            else:
                await ctx.send("no teacher boosts available on this ticket")
                return				
        else:
            await ctx.send("ticket does not have any orders added to it or does not have a team assigned")
        await ctx.message.delete()

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def process(self, ctx):
        channelID = ctx.channel.id           
        if helper.is_valid_id(channelID,CHANNELS):
            channeldata = helper.get_order(channelID, CHANNELS)
            raids = {}
            boostOrder = {"order":[],"count":[],"team":[]}
            for raidNumber in channeldata["raids"].keys():
                raid = channeldata["raids"].get(raidNumber)
                if not raid["processed"]:
                    raid["boosters"].sort()
                    boostOrder["order"].append(str(raid['order']))
                    boostOrder["count"].append(1)
                    team = ''
                    for booster in raid["boosters"]:
                        team += f'<@{booster}> '
                    boostOrder["team"].append(team)
                    raid["processed"]=True
                raids[raidNumber] = raid
            data = helper.get_boost_commands(pd.DataFrame(data=boostOrder))
            embedMsg = helper.get_embed(ctx)
            embedMsg.add_field(name='Commands to run',value='\u200b',inline=False)
            if len(data) > 0:
                for command in data:
                    embedMsg.add_field(name='\u200b',value=f'<#{channelID}>',inline=False)
                    embedMsg.add_field(name='\u200b',value=command,inline=False)
            else:
                data = '\u200b'
                embedMsg.add_field(name="No completed boosts",value=data,inline=False)
            channeldata["raids"] = raids
            helper.update_channel_entry(channelID,channeldata)
            await ctx.author.send(embed = embedMsg)

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def boost(self, ctx, *args):
        #get channel associated with this order
        order_id = args[0]
        boosters = args[2:]
        for boost in boosters:
            char_list = ['<','@','!','>']
            try:
                user = self.client.get_user(int(re.sub("|".join(char_list), "", boost)))
            except:
                return
        num_boosts = abs(int(args[1]))
        if helper.is_valid_id(order_id, ORDERS):
            associations = helper.get_associations(ASSOCIATIONS)
            if order_id in associations['orders'].keys():
                channelID = associations['orders'][order_id]["channel"]
                if helper.is_valid_id(channelID,CHANNELS):
                    channeldata = helper.get_order(channelID, CHANNELS)
                    ordertoupdate = None
                    for orderIndex in range(0,len(channeldata["orders"])):
                        if channeldata["orders"][orderIndex]["order_id"] == order_id:
                            ordertoupdate = channeldata["orders"][orderIndex]
                            validBoost = (ordertoupdate['kc'] + num_boosts) <= ordertoupdate['total_kc']
                            #found order in the channel
                            ordertoupdate['progress'] = 0
                            ordertoupdate['kc'] += num_boosts
                            if ordertoupdate['kc'] == ordertoupdate['total_kc']:
                                ordertoupdate["is_active"] = False
                            channeldata["orders"][orderIndex] = ordertoupdate
                            channeldata["processed"] = True
                            if validBoost:
                                helper.update_channel_entry(channelID,channeldata)

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def update(self, ctx, order_id, num_kills: int, num_amount):
        #get channel associated with this order
        num_kills = abs(num_kills)
        if helper.is_valid_id(order_id, ORDERS) and num_amount.lower()[-1] in ["m"]:
            associations = helper.get_associations(ASSOCIATIONS)
            if order_id in associations['orders'].keys():
                channelID = associations['orders'][order_id]["channel"]
                if helper.is_valid_id(channelID,CHANNELS):
                    channeldata = helper.get_order(channelID, CHANNELS)
                    ordertoupdate = None
                    for orderIndex in range(0,len(channeldata["orders"])):
                        if channeldata["orders"][orderIndex]["order_id"] == order_id:                    
                            ordertoupdate = channeldata["orders"][orderIndex]
                            ordertoupdate['total_kc'] += num_kills
                            remaining = ordertoupdate['total_kc'] - ordertoupdate['kc']
                            if remaining > 0:
                                ordertoupdate["is_active"] = True
                            channeldata["orders"][orderIndex] = ordertoupdate
                            helper.update_channel_entry(channelID,channeldata)                            

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def complete(self, ctx, order_id: str):
        if helper.is_valid_id(order_id, ORDERS):
            associations = helper.get_associations(ASSOCIATIONS)
            if order_id in associations['orders'].keys():
                channelID = associations['orders'][order_id]["channel"]
                if helper.is_valid_id(channelID,CHANNELS):
                    channeldata = helper.get_order(channelID, CHANNELS)
                    for orderIndex in range(0,len(channeldata["orders"])):
                        if channeldata["orders"][orderIndex]["order_id"] == order_id:
                            ordertoupdate = channeldata["orders"][orderIndex]
                            ordertoupdate["is_active"] = False
                            helper.update_channel_entry(channelID,channeldata)
def setup(client):
    client.add_cog(order(client))