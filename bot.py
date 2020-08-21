import discord
from discord.ext import commands, tasks
from discord.utils import get
import pdb
import copy
from datetime import datetime

client = commands.Bot(command_prefix = '.')
#ticket id + number needed
tickets = []
queue = []
called = {}
inRaids = []
ongoingTickets = []

@client.event
async def on_ready():
    callNextBooster.start()
    removeAFK.start()

async def callBoosters(channelMention,booster=None, number=None, calledByTimer=False):
    queueIter = queue.copy() #deep copy
    totalNeeded = sum(int(ticket['needed']) for ticket in tickets)
    if totalNeeded > len(called) or calledByTimer:
        #fill
        if number is not None:
            for queueBooster in queueIter[:number]:
                await queueBooster.send(f'{channelMention} requires a team, would you like to join?')
                called[queueBooster.id] = {'booster': queueBooster, 'joined': datetime.now()}
                queue.remove(queue[0])
        else:
            #join or leav
            await booster.send(f'{channelMention} requires a team, would you like to join?')
            called[booster.id] = {'booster': booster, 'joined': datetime.now()}
            queue.remove(queue[0])

@client.command()
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
async def showongoing(ctx):
    data = ''
    index = 1
    for ticket in ongoingTickets:
        ticketMention = ticket['channel'].mention
        boosters = ticket['needed']  
        team = ticket['team']
        data = data + f'ticket: {ticketMention} needed: {boosters} current team: {[booster.mention for booster in team]}\n'
        index = index+1
    await ctx.send(f'current ongoing tickets are:\n{data}')

@client.command()
async def join(ctx):
    booster = ctx.author
    okayToJoin = True
    for member in queue:
        if booster.id == member.id:
            await ctx.send(f' {member.name} has already joined the queue!')
            okayToJoin = False
    if booster in inRaids:
        await ctx.send(f' {booster.name} is already in a raid. end the raid if you would like to rejoin!')
        okayToJoin = False
    if okayToJoin:
        queue.append(booster)
        await ctx.send(f' {booster.name} has joined the queue with poisition {len(queue)}!')
    if len(tickets) > 0:
        await callBoosters(tickets[0]['ticketMention'], booster=ctx.author)

@client.command()
async def showqueue(ctx):
    data = ''
    index = 1
    for booster in queue:
        data = data + f'{index} {booster.mention}\n'
        index = index+1
    await ctx.send(f'current queue is:\n{data}')

@client.command()
async def showtickets(ctx):
    data = ''
    index = 1
    for ticket in tickets:
        ticketMention = ticket['ticketMention']
        boosters = ticket['needed']  
        team = ticket['team']
        data = data + f'ticket: {ticketMention} needed: {boosters} current team: {[booster.mention for booster in team]}\n'
        index = index+1
    await ctx.send(f'current available tickets are:\n{data}')

@client.command()
async def leave(ctx):
    #if ongoing ticket, move to open tickets
    #if open ticket, remove from team increase needed
    #ongoing ticket
    channel = get(ctx.message.guild.channels, name='tob-chat', type=discord.ChannelType.text)
    for ticketIndex in range(0,len(tickets)):
        if ctx.author in tickets[ticketIndex]['team']:
            ticketToUpdate = tickets[ticketIndex].copy() #deepcopy
            ticketToUpdate['team'].remove(ctx.author)
            inRaids.remove(ctx.author)
            ticketToUpdate['needed'] = ticketToUpdate['needed']+1
            tickets[ticketIndex] = ticketToUpdate
            needed, ticketChannel = ticketToUpdate['needed']+1, ticketToUpdate['channel'].mention
            await channel.send(f'{needed} boosters needed for {ticketChannel}')
            await callBoosters(tickets[0]['ticketMention'], number=1)

    for ticket in ongoingTickets:
        if ctx.author in ticket['team']:
            ticket['team'].remove(ctx.author)
            inRaids.remove(ctx.author)
            ongoingTickets.remove(ticket)
            tickets.append({'channel': ticket['channel'], 'ticketMention':ticket['channel'].mention, 'needed':ticket['needed']+1, 'team': ticket['team']})
            needed, ticketChannel = ticket['needed']+1, ticket['channel'].mention
            await channel.send(f'{needed} boosters needed for {ticketChannel}')
            await callBoosters(tickets[0]['ticketMention'], number=1)


@client.command()
async def fill(ctx, number, ticketOverride=None):
    channel = get(ctx.message.guild.channels, name='tob-chat', type=discord.ChannelType.text)
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
    await channel.send(f'{number} boosters needed for {ctx.message.channel.mention }')
    await callBoosters(ctx.channel.mention, number=int(number))

@client.command()
async def add(ctx, number):
    if 'Staff' in [role.name for role in ctx.author.roles] and ctx.author not in inRaids:
        notExisting = True
        for ticketIndex in tickets:
            ticketToUpdate = tickets[ticketIndex].copy()
            if ticketToUpdate['channel'] == ctx.channel:
                notExisting = True
                ticketToUpdate['team'].add(ctx.author)
                ticketToUpdate['needed'] = ticketToUpdate['needed']-1
                tickets[ticketIndex] = ticketToUpdate
                inRaids.append(ctx.author)
                if ctx.author in queue:
                    queue.remove(ctx.author)
                await fill(ctx, ticketToUpdate['needed'])
        if notExisting:
            inRaids.append(ctx.author)
            ticketToAdd = {'channel': ctx.channel, 'ticketMention':ctx.channel.mention, 'needed':int(number), 'team': [ctx.author]}
            if ctx.author in queue:
                queue.remove(ctx.author)
            await fill(ctx, number, ticketToAdd)
    else:
        await ctx.author.send(f'You do not have the correct privelages to add, or you might be in a raid already')

@client.command()
async def accept(ctx):
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
        else:
            await booster.send('You have not been called yet')
    else:
        if booster.id in called.keys():
            called.pop(booster.id, None)
            queue.insert(0,booster)
            await booster.send('no tickets available to accept currently, added to the front of queue')
        else:
            await booster.send('You have not been called yet')

@tasks.loop(seconds=10)
async def callNextBooster():
    now = datetime.now()
    localCalled = called.copy()
    for boosterid in localCalled.copy():
        delta = now - localCalled[boosterid]['joined']
        if delta.total_seconds() > 10 and len(queue) > 0:
            await callBoosters(tickets[0]['ticketMention'],booster=queue[0],calledByTimer=True)
    print('tick')

@tasks.loop(seconds=30)
async def removeAFK():
    now = datetime.now()
    localCalled = called.copy()
    for boosterid in localCalled.copy():
        delta = now - localCalled[boosterid]['joined']
        if delta.total_seconds() > 30:
            called.pop(boosterid)
            await localCalled[boosterid]['booster'].send('You have been removed from the called list as you were AFK for too long')
    print('tick')

client.run('NzQ1Mzc2NjI5OTkxNDA3Njc2.Xzw4FQ.vjmg4uhYokG8SlHvWaPeBphzdnQ') 