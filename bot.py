import discord
from discord.ext import commands, tasks
from discord.utils import get
import pdb
import copy
from datetime import datetime
import re
client = commands.Bot(command_prefix = '-')
#ticket id + number needed
tickets = []
queue = []
called = {}
inRaids = []
ongoingTickets = []

@client.event
async def on_ready():
    callNextBooster.start()

async def callBoosters(channelMention,booster=None, number=None, calledByTimer=False):
    queueIter = queue.copy() #deep copy
    totalNeeded = sum(int(ticket['needed']) for ticket in tickets)
    if (totalNeeded > len(called) and len(queue)>0) or calledByTimer:
        #fill
        if number is not None:
            for queueBooster in queueIter[:number]:
                await queueBooster.send(f'{channelMention} needs a booster. are you here? -here to join the ticket')
                called[queueBooster.id] = {'booster': queueBooster, 'joined': datetime.now()}
                queue.remove(queue[0])
        else:
            #join
            await booster.send(f'{channelMention} needs a booster. are you here? -here to join the ticket')
            called[booster.id] = {'booster': booster, 'joined': datetime.now()}
            queue.remove(queue[0])

@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def end(ctx):
    for ticket in ongoingTickets:
        if ticket['channel'] == ctx.channel:
            for booster in ticket['team']:
                inRaids.remove(booster)
            ongoingTickets.remove(ticket)
    for ticket in tickets:
        if ticket['channel'] == ctx.channel:
            tickets.remove(ticket)
            for booster in ticket['team']:
                inRaids.remove(booster)

@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def join(ctx):
    booster = ctx.author
    okayToJoin = True
    for member in queue:
        if booster.id == member.id:
            await ctx.send(f'{member.mention} has already joined the queue!')
            okayToJoin = False
    if booster in inRaids:
        await ctx.send(f' {booster.mention} is already in a raid. end the raid if you would like to rejoin!')
        okayToJoin = False
    if okayToJoin:
        queue.append(booster)
        await ctx.send(f'{booster.mention} has joined the queue with position {len(queue)}!')
    if len(tickets) > 0:
        await callBoosters(tickets[0]['ticketMention'], booster=ctx.author)

@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def q(ctx):
    index = 1
    boosters = ''
    embedMsg = discord.Embed(color=0x00ff00)
    embedMsg.set_author(name=ctx.author.name,icon_url= ctx.author.avatar_url)
    embedMsg.set_thumbnail(url='https://cdn.discordapp.com/attachments/725874308089643112/747078186411491429/pvmservicesgif.gif')
    if len(queue) > 0:
        for booster in queue:
            boosters = boosters + f'**{index}.** {booster.name}\n'
            index = index+1
    else:
        boosters = '\u200b'
    embedMsg.add_field(name="Queue",value=boosters,inline=False)
    await ctx.send(embed = embedMsg)

@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def showtickets(ctx):
    data = ''
    embedMsg = discord.Embed(color=0x00ff00)
    embedMsg.set_author(name=ctx.author.name,icon_url= ctx.author.avatar_url)
    embedMsg.set_thumbnail(url='https://cdn.discordapp.com/attachments/725874308089643112/747078186411491429/pvmservicesgif.gif')
    if len(tickets) > 0:
        for ticket in tickets:
            ticketMention = ticket['channel'].mention
            boosters = ticket['needed']  
            team = ticket['team']
            currentTeam = ','.join([booster.name for booster in team])
            data = data + f'**ticket:** {ticketMention} **needed:** {boosters} **current team:** {currentTeam}\n'
    else:
        data = '\u200b'
    embedMsg.add_field(name="Current available tickets",value=data,inline=False)
    data = ''
    if len(ongoingTickets) > 0:
        for ticket in ongoingTickets:
            ticketMention = ticket['channel'].mention
            boosters = ticket['needed']  
            team = ticket['team']
            currentTeam = ','.join([booster.name for booster in team])
            data = data + f'**ticket:** {ticketMention} **needed:** {boosters} **current team:** {currentTeam}\n'
    else:
        data = '\u200b'
    embedMsg.add_field(name="On-going tickets",value=data,inline=False)
    await ctx.send(embed=embedMsg)

@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def qhelp(ctx):
    embedMsg = discord.Embed(title="Queue commands",color=0x00ff00)
    embedMsg.set_author(name=ctx.author.name,icon_url= ctx.author.avatar_url)
    embedMsg.set_thumbnail(url='https://cdn.discordapp.com/attachments/725874308089643112/747078186411491429/pvmservicesgif.gif')
    embedMsg.add_field(name="Booster Commands",value="** **",inline=False)
    embedMsg.add_field(name="-join",value="join the queue to wait for a ticket",inline=False)
    embedMsg.add_field(name="-leave",value="leave the queue, or leave the ticket you are currently on",inline=False)
    embedMsg.add_field(name="-here",value="join a ticket if you are called upon by the bot",inline=False)
    embedMsg.add_field(name="-showtickets",value="show the current open/ongoing tickets available",inline=False)
    embedMsg.add_field(name="-q",value="show the current queue",inline=False)
    embedMsg.add_field(name="-end",value="Ticket is done for now, will allow everyone on the team to reapply for the queue",inline=False)
    embedMsg.add_field(name="Staff Commands",value="** **",inline=False)
    embedMsg.add_field(name="-findteam X",value="find X number of boosters to join a ticket. \nUSAGE: -findteam 2",inline=False)
    embedMsg.add_field(name="-addtoq Booster X",value="add booster to queue. if X is empty, append to end of queue else insert at that postion of queue\nUSAGE: -addtoq @booster 0",inline=False)
    embedMsg.add_field(name="-createteam *boosters number",value="Create a ticket with a predefined team. if number is blank, inputted team is the set team. If number is a valid int it will look for that many boosters to join \nUSAGE: -createteam @booster1 @booster2 2",inline=False)
    await ctx.author.send(embed=embedMsg)

@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def leave(ctx):
    #if ongoing ticket, move to open tickets
    #if open ticket, remove from team increase needed
    #ongoing ticket
    channel = get(ctx.message.guild.channels, id=712383579719467146, type=discord.ChannelType.text)
    #channel = get(ctx.message.guild.channels, id=745417713421123614, type=discord.ChannelType.text)
    booster = ctx.author
    for boosterIndx in queue:
        if booster.id == boosterIndx.id:
            queue.remove(boosterIndx)
            await ctx.send(f'``` {booster.name} has left the queue!```')
            await q(ctx)
    for ticketIndex in range(0,len(tickets)):
        if ctx.author in tickets[ticketIndex]['team']:
            ticketToUpdate = tickets[ticketIndex].copy() #deepcopy
            ticketToUpdate['team'].remove(ctx.author)
            inRaids.remove(ctx.author)
            ticketToUpdate['needed'] = ticketToUpdate['needed']+1
            tickets[ticketIndex] = ticketToUpdate
            tickets.sort(key = lambda x : x['needed'])
            needed, ticketChannel = ticketToUpdate['needed'], ticketToUpdate['channel'].mention
            await channel.send(f'{needed} boosters needed for {ticketChannel} <@&712383579480653873>')
            await callBoosters(tickets[0]['ticketMention'], number=1)

    for ticket in ongoingTickets:
        if ctx.author in ticket['team']:
            ticket['team'].remove(ctx.author)
            inRaids.remove(ctx.author)
            ongoingTickets.remove(ticket)
            tickets.append({'channel': ticket['channel'], 'ticketMention':ticket['channel'].mention, 'needed':ticket['needed']+1, 'team': ticket['team']})
            tickets.sort(key = lambda x : x['needed'])
            needed, ticketChannel = ticket['needed']+1, ticket['channel'].mention
            await channel.send(f'{needed} boosters needed for {ticketChannel} <@&712383579480653873>')
            await callBoosters(tickets[0]['ticketMention'], number=1)

@client.command()
@commands.has_any_role(712383579505819719)
async def addtoq(ctx, booster, index=None):
    char_list = ['<','@','!','>']
    user = client.get_user(int(re.sub("|".join(char_list), "", booster)))
    if user is not None:
        if index == None:
            queue.append(user)
        else:
            try:
                queue.insert(int(index),user)
            except:
                print('invalid index passed or user passed')

@client.command()
@commands.has_any_role(712383579505819719)
async def findteam(ctx, number, ticketOverride=None):
    channel = get(ctx.message.guild.channels, id=712383579719467146, type=discord.ChannelType.text)
    #channel = get(ctx.message.guild.channels, id=745417713421123614, type=discord.ChannelType.text)
    okayToAddTicket = True
    for ticket in tickets:
        if ticket['ticketMention'] == ctx.channel.mention:
            okayToAddTicket = False
    if okayToAddTicket:
        if ticketOverride is None:
            tickets.append({'channel': ctx.channel, 'ticketMention':ctx.channel.mention, 'needed':int(number), 'team': []})
        else:
            tickets.append(ticketOverride)
        tickets.sort(key = lambda x : x['needed'])
    await channel.send(f'{number} boosters needed for {ctx.message.channel.mention } <@&712383579480653873>')
    await ctx.send(f'```Finding you a team!```')
    await callBoosters(ctx.channel.mention, number=int(number))

@client.command()
@commands.has_any_role(712383579505819719)
async def createteam(ctx, *boosters):
    char_list = ['<','@','!','>']
    team = []
    okayToAdd = True
    number = boosters[len(boosters)-1]
    try:
        number = int(number)
        boosters = boosters[:len(boosters)-1]
    except:
        number = None
        pass
    for booster in boosters:
        user = client.get_user(int(re.sub("|".join(char_list), "", booster)))
        if user not in inRaids:
            for ticket in tickets:
                if ticket['ticketMention'] == ctx.channel.mention:
                    okayToAdd = False
                    await ctx.send(f'ticket is already opened. -end to recreate')
            for ticket in ongoingTickets:
                if ticket['channel'] == ctx.channel:
                    okayToAdd = False
                    await ctx.send(f'ticket is already ongoing. -end to recreate')
            team.append(user)
        else:
            okayToAdd = False
            await ctx.send(f'{user.name} is already in a raid, ask them to leave their raid before creating the team with them')
            break
    if okayToAdd:
        for user in team:
            if user in queue:
                queue.remove(user)
            if user.id in called.keys():
                called.pop(user.id)
            inRaids.append(user)
        if number is None:
            ongoingTickets.append({'channel': ctx.channel, 'needed':0, 'team': team})
        else:
            await findteam(ctx, int(number), {'channel': ctx.channel, 'ticketMention':ctx.channel.mention, 'needed':int(number), 'team': team})
         
@client.command()
@commands.has_any_role(712383579480653873,712383579505819719)
async def here(ctx):
    channel = get(ctx.message.guild.channels, id=712383579719467146, type=discord.ChannelType.text)
    booster = ctx.author
    if len(tickets) > 0:
        if booster.id in called.keys():
            ticket = tickets[0]
            ticket['needed'] = ticket['needed']-1
            ticket['team'].append(booster)
            if ticket['needed'] == 0:
                team = ticket['team']
                data = 'Your team is '
                for boost in team:
                    data = data + f'{boost.mention} '
                await ticket['channel'].send(data)
                ongoingTickets.append({'channel':ticket['channel'],'needed':0, 'team': [booster for booster in ticket['team']]})
                del tickets[0]
                called.pop(booster.id, None)
            else:
                tickets[0] = ticket
                called.pop(booster.id, None)
            inRaids.append(booster)
            channelMention = ticket['channel'].mention
            await channel.send(f'{booster.mention} has joined the team for {channelMention}')
        else:
            await booster.send('You have not been called yet')
    else:
        if booster.id in called.keys():
            called.pop(booster.id, None)
            queue.insert(0,booster)
            await booster.send('no tickets available to accept currently, added to the front of queue')
        else:
            await booster.send('You have not been called yet')

@tasks.loop(seconds=60)
async def callNextBooster():
    now = datetime.now()
    localCalled = called.copy()
    for boosterid in localCalled:
        delta = now - localCalled[boosterid]['joined']
        if delta.total_seconds() > 120 and len(queue) > 0 and len(tickets) >0:
            await callBoosters(tickets[0]['ticketMention'],booster=queue[0],calledByTimer=True)
        if delta.total_seconds() > 600:
            called.pop(boosterid)
            await localCalled[boosterid]['booster'].send('You have been removed from the called list as you were AFK for too long')
    print(f'callnext +{now}')

client.run('')