import discord
import os
import json
from discord.ext import commands
import random
import logging

from discord import Member, Embed
from discord.ext.commands import Cog, BucketType, bot

from keep_alive import keep_alive


logger = logging.getLogger('discord')
handler = logging.FileHandler(filename='discord.log',
                              encoding='utf-8',
                              mode='w')
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = commands.Bot(command_prefix="£")

########################################

mainshop = [
  {"name": "watch", "price": 100, "description": "Time"},
  {"name": "pc", "price": 700, "description": "MacBook Pro"},
  {"name": "hoodie", "price": 175, "description": "Supreme Box Logo"}
          ]

########################################
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


########################################

@client.command()
async def bal(ctx):  
    await open_account(ctx.author)

    user = ctx.author
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    em = discord.Embed(title=f"{ctx.author.name}'s balance",
                       color=discord.Color.green())
    em.add_field(name="Wallet Balance:", value=wallet_amt)
    em.add_field(name="Bank Balance:", value=bank_amt)

    await ctx.send(embed=em)

########################################
@client.command()
async def shop(ctx):
  
  em = discord.Embed(title = "Shop")

  for item in mainshop:
    name = item["name"]
    price = item["price"]
    description = item["description"]

    em.add_field(name = name, value = f"£{price} | {description}")

  await ctx.send(embed = em)

########################################
@client.command()
async def buy(ctx,item,amount = 1):
    await open_account(ctx.author)

    res = await buy_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That Object isn't there!")
            return
        if res[1]==2:
            await ctx.send(f"You don't have enough money in your wallet to buy {amount} {item}")
            return


    await ctx.send(f"You just bought {amount} {item}")

########################################
@client.command()
async def sell(ctx,item,amount = 1):
    await open_account(ctx.author)

    res = await sell_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That Object isn't there!")
            return
        if res[1]==2:
            await ctx.send(f"You don't have {amount} {item} in your bag.")
            return
        if res[1]==3:
            await ctx.send(f"You don't have {item} in your bag.")
            return

    await ctx.send(f"You just sold {amount} {item}.")

async def sell_this(user,item_name,amount,price = None):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            if price==None:
                price = 0.9* item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt - amount
                if new_amt < 0:
                    return [False,2]
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            return [False,3]
    except:
        return [False,3]    

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost,"wallet")

    return [True,"Worked"]

########################################

@client.command()
async def bag(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    try:
        bag = users[str(user.id)]["bag"]
    except:
        bag = []


    em = discord.Embed(title = "Bag")
    for item in bag:
        name = item["item"]
        amount = item["amount"]

        em.add_field(name = name, value = amount)    

    await ctx.send(embed = em)      

########################################

async def buy_this(user,item_name,amount):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            price = item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)

    if bal[0]<cost:
        return [False,2]


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt + amount
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            obj = {"item":item_name , "amount" : amount}
            users[str(user.id)]["bag"].append(obj)
    except:
        obj = {"item":item_name , "amount" : amount}
        users[str(user.id)]["bag"] = [obj]        

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost*-1,"wallet")

    return [True,"Worked"]


########################################
@client.command()

async def balance(ctx, member: discord.Member):
    await open_account(member)

    user = member
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    em = discord.Embed(title=f"{member.name}'s balance",
                       colour=discord.Color.purple())
    em.add_field(name="Wallet Balance:", value=wallet_amt)
    em.add_field(name="Bank Balance:", value=bank_amt)

    await ctx.send(embed=em)


########################################
@client.command()
async def beg(ctx):

    global cooldown
    await open_account(ctx.author)

    users = await get_bank_data()

    user = ctx.author

    earning = random.randrange(100)
    await ctx.send(f"Someone gave you £{earning}!")

    users[str(user.id)]["wallet"] += earning

    commands.cooldown

    with open("bank.json", "w") as f:
        json.dump(users, f)


########################################


@client.command()
async def withdraw(ctx, amount=None):

    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Please enter the amout to withdraw:")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[1]:
        await ctx.send("You're too broke!")
        return

    if amount < 0:
        await ctx.send("Amount must be greater than Zero!")
        return

    await update_bank(ctx.author, amount)
    await update_bank(ctx.author, -1 * amount, "bank")
    await ctx.send(f"You withdrew {amount} coins!")


########################################


@client.command()
async def dep(ctx, amount=None):

    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Please enter the amout to deposit!")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[0]:

        await ctx.send("Not enough money to deposit!")
        return

    if amount < 0:
        await ctx.send("Amount must be positive")
        return

    await update_bank(ctx.author, -1 * amount)
    await update_bank(ctx.author, amount, "bank")
    await ctx.send(f"You deposited {amount} coins!")


########################################


@client.command()
async def send(ctx, member: discord.Member, amount=None):

    await open_account(ctx.author)
    await open_account(member)

    if amount == None:
        await ctx.send("Please enter the amout to send!")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[1]:
        await ctx.send("Not enough bread!")
        return

    if amount < 0:
        await ctx.send("Amount must be positive")
        return

    await update_bank(ctx.author, -1 * amount, "bank")
    await update_bank(member, amount, "bank")

    await ctx.send(f"You sent {member} {amount} coins!")


########################################


@client.command()
async def slots(ctx, amount=None):

    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Please enter the amout to deposit!")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send("Not enough money to withdraw!")
        return

    if amount < 0:
        await ctx.send("Amount must be positive")
        return

    final = []
    for i in range(3):

        a = random.choice(["X", "O", "Q"])
        final.append(a)

    await ctx.send(str(final))

    if final[0] == final[1] and final[0] == final[2] and final[1] == final[2]:

        earning = random.randrange(51)

        await update_bank(ctx.author, (2 * amount) + earning)
        await ctx.send("You won!")

    else:

        await update_bank(ctx.author, -1 * amount)
        await ctx.send("You Lost!")


########################################


@client.command()
async def rob(ctx, member: discord.Member):

    await open_account(ctx.author)
    await open_account(member)

    robbee = await update_bank(member)
    theirBal = await update_bank(member)

    robber = await update_bank(ctx.author)

    #bal = await update_bank(member)

    if (robbee[0] < 150):
        await ctx.send("Cannot rob them, they're too poor!")
        return

    elif ((robbee[0] > 150) and (robber[0] > 199)):

        earnings = random.randrange(0, theirBal[0])

        await update_bank(ctx.author, earnings, "wallet")
        await update_bank(member, -1 * earnings, "wallet")

        await ctx.send(f"{member} has been sucked!")
        return

    else:

        await ctx.send("Get your bread up before you rob someone!")

    #await ctx.send(f"You sent {member}  coins!")


########################################


async def open_account(user):

    users = await get_bank_data()

    if str(user.id) in users:  #if user is in 'users' don't do anything
        return False

    else:  #create an json.id for them

        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0
        users[str(user.id)]["bank"] = 0

    with open("bank.json", "w") as f:
        json.dump(users, f)

    return True


########################################


async def get_bank_data():  #reads the json file
    with open("bank.json", "r") as f:
        users = json.load(f)

    return users


########################################


async def update_bank(user, change=0, mode="wallet"):
    users = await get_bank_data()

    users[str(user.id)][mode] += change

    with open("bank.json", "w") as f:
        json.dump(users, f)

    balance = users[str(user.id)]["wallet"], users[str(user.id)]["bank"]
    return balance


########################################

keep_alive()

client.run(os.getenv('TOKEN'))  #gets the value of the varibale in env
