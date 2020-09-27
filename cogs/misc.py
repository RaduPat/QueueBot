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

deposits = "../tob-boost/wallets/deposit.json"
class Deposits(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.depositRoles = {        
        config["2B"]: 2000,
        config["1B"]: 1000,
        config["500M"]: 500,
        config["300M"]: 300,
        config["200M"]: 200,
        config["100M"]: 100
        }
        self.roleIDS = [config["2B"],config["1B"],config["500M"],config["300M"],config["200M"],config["100M"]]

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def adddeposit(self, ctx, user, amount):
        guild = self.client.get_guild(config['guild_id'])
        try:
            char_list = ['<','@','!','>']
            user = guild.get_member(int(re.sub("|".join(char_list), "", user)))
            amount = int(helper.get_num_from_amount(amount.lower()))/1000000
        except:
            return
        all_roles = user.roles
        userDepositRoles = []
        totalDeposit = 0
        for role in all_roles:
            if role.id in self.roleIDS:
                userDepositRoles.append(guild.get_role(role.id))
                totalDeposit += self.depositRoles[role.id]
        totalDeposit += amount
        currentDeposit = totalDeposit
        rolesToAdd = []
        for role in self.roleIDS:
            if self.depositRoles[role] <= currentDeposit:
                currentDeposit = currentDeposit - self.depositRoles[role]
                rolesToAdd.append(guild.get_role(role))
        #remove roles
        await user.remove_roles(*userDepositRoles)
        #addNewRoles
        await user.add_roles(*rolesToAdd)

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def removedeposit(self, ctx, user, amount):
        guild = self.client.get_guild(config['guild_id'])
        try:
            char_list = ['<','@','!','>']
            user = guild.get_member(int(re.sub("|".join(char_list), "", user)))
            amount = int(helper.get_num_from_amount(amount.lower()))/1000000
        except:
            return
        all_roles = user.roles
        userDepositRoles = []
        totalDeposit = 0
        for role in all_roles:
            if role.id in self.roleIDS:
                userDepositRoles.append(guild.get_role(role.id))
                totalDeposit += self.depositRoles[role.id]
        totalDeposit -= amount
        currentDeposit = totalDeposit
        rolesToAdd = []
        for role in self.roleIDS:
            if self.depositRoles[role] <= currentDeposit:
                currentDeposit = currentDeposit - self.depositRoles[role]
                rolesToAdd.append(guild.get_role(role))
        #remove roles
        await user.remove_roles(*userDepositRoles)
        #addNewRoles
        await user.add_roles(*rolesToAdd)

    @commands.command()
    @commands.has_any_role(*config['staff'])
    async def owed(self, ctx, user, amount):
        with open(name, 'r') as f:
            data = json.load(f)
        deposit_total += sum(data.values())
        dario = data['273187933714907146']
        niki = data['735972062560124948']
        pdb.set_trace()

def setup(client):
    client.add_cog(Deposits(client))
