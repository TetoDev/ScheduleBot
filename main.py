import discord
import csv
import pandas
import threading
import logging
from time import time, ctime, sleep
import datetime
from discord.utils import get
import asyncio
import json

json_file = open('data.json')
data = json.load(json_file)

help_embed = discord.Embed(title="Schedule help",description="Here is the list of commands you can do with Schedule:",color=discord.Color.dark_grey())
help_embed.add_field(name="!schedule or !s", value="It schedules a task. It takes 4 arguments: Task Name, Hour (00:00), Date (0-31), Days to repeat (In how many days it will repeat, 0 for a punctual task)",inline=False)
help_embed.add_field(name="!delete or !del",value="It removes all saved tasks with the inputted name (ignoring case). It takes 1 argument: Task name",inline=False)
help_embed.add_field(name="!list", value="It lists all your tasks. Takes no arguments.",inline=False)
help_embed.set_footer(text="Beta testing. If you find any bugs or error please DM Teto#8763. Also accepting suggestions ;)")

repeated_list = []


client = discord.Client()



def number_of_days():
    now = datetime.datetime.now()
    months_31=[1,3,5,7,8,10,12]

    if now.month in months_31:
        return 31 , now.day
    elif now.month == 2:
        leap = 0
        if now.year % 400 == 0:
            leap = 1
        elif now.year % 100 == 0:
            leap = 0
        elif now.year % 4 == 0:
            leap = 1
        return  (28+leap) , now.day
    else:
        return 30 , now.day

def scheduler(task,time,date,repeated,user):
    with open('schedule.csv', mode='a') as schedule:
        schedule_writer = csv.writer(schedule, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        schedule_writer.writerow([task,time,date,repeated,user])
        print("Scheduled task {}".format(task))


def remove_task (taskname,userid):

    removed_matches = 0

    df = pandas.read_csv('schedule.csv')
    
    for index, row in df.iterrows():
        if row[0].lower() == taskname.lower() and str(userid) == str(row[4]):
            df.drop(index, inplace=True , axis=0)
            removed_matches = removed_matches + 1
    
    df.to_csv('schedule.csv',index=False)
    return removed_matches

def repeat(name,hour,days,userid):
    task = [name,hour,days,userid,0]
    in_list = False
    
    for i in range((len(repeated_list))):
        if name == repeated_list[i][0] and hour == repeated_list[i][1] and userid == repeated_list[i][3]:
            in_list = True
            repeated_list[i][4] = repeated_list[i][4] + 1
            if repeated_list[i][4] > 10:
                remove_task(repeated_list[i][0],repeated_list[i][3])
                repeated_list.pop(i)
                
                
                

    if not in_list:
        repeated_list.append(task)
                
        

    month_days, now_day = number_of_days()

    if int(days) != 0:
        if (int(days) + now_day) > month_days:
            delta = month_days - now_day
            day = int(days) - delta
            scheduler(name,hour,day,days,userid)
        
        else:
            scheduler(name,hour,now_day+int(days),days,userid)
        
    
    




async def notify (task,time,date,userid,ctx):
    user = await ctx.fetch_user(userid)
    await user.send("You have pending '**{}**' now at **{}**!!!".format(task,time))
   

def get_time():
    useful_time = ctime(time()).split(" ")
    if len(useful_time) > 5:
        useful_time.pop(2)
    for i in [0,0,2]:
        useful_time.pop(i)
    useful_time[1] = useful_time[1][0:5]
    print(useful_time)
    return useful_time

def check_tasks(loop,time,ctx):
    with open('schedule.csv', mode='r') as tasks:
        csv_reader = csv.reader(tasks, delimiter=',')
        print(time)
        print(time[0])
        print(time[1])
        for row in csv_reader:
            if row != []:
                print("row != []")
                if str(row[1]) == str(time[1]):
                    if str(row[2]) == str(time[0]):
                        repeat(row[0],row[1],row[3],row[4])
                        asyncio.run_coroutine_threadsafe(notify(row[0],row[1],row[2],row[4],ctx),loop)
                    

    
def clock(loop,ctx):
    print("Initializing clock")
    while True:
        sleep(5)
        check_tasks(loop,get_time(),ctx) 




    

def str_schedule(userid):
    df = pandas.read_csv('schedule.csv')
    for index, row in df.iterrows():
        if row['User'] != userid:
            df.drop(index, inplace=True , axis=0)
    print('Printing task list')
    df.drop('User',inplace=True,axis=1)
    if df.empty:
        return "**You have no tasks scheduled!**"
    return df.to_string(index=False)


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game(name="DM me: !help | Global UTC-00:00 timezone"))
    clock_thread.start()
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg = message.content
    if ',' in msg:
            await message.channel.send("Detected invalid character 'comma' (,)")
            return

    if msg.startswith('!schedule') or msg.startswith('!s'):
        

        args = msg.split(' ')
        if len(args) < 5:
            await message.channel.send("Input all of the 4 required args: task, time, date, repeated")
            return
        elif len(args) > 5:
            await message.channel.send("Expected only 4 arguments: task name, time, date and days to repeat. Check if there is any spaces on your message.")
            return

        if len(args[2]) != 5 or not ':' in args[2]:
            await message.channel.send("Bad hour formatting, use format 00:00. (Examples: 08:30, 17:30)")
            return

        if int(args[3]) > 31:
            await message.channel.send("Enter a valid day (< 31)")
            return

        s_task_time = args[2].split(':')
        
        if int(s_task_time[0]) > 23 or int(s_task_time[1]) > 59:
            await message.channel.send("Enter a valid hour")
            return
        

        try:
            repeat_days = int(args[4])
        except ValueError:
            await message.channel.send('Last argument must be an integer.')
            return
        
        scheduler(args[1],args[2],args[3],args[4],message.author.id)
    
        if repeat_days == 0:
            repeatable_msg = "This won't repeat ever again."
        elif repeat_days == 1:
            repeatable_msg = "This will repeat every day."
        else:
            repeatable_msg = "This will repeat every {} days.".format(repeat_days)
        await message.channel.send("Task {} scheduled at {} of the {} succesfully. {}".format(args[1],args[2],args[3],repeatable_msg))


    if msg.startswith('!list'):
        await message.channel.send(str_schedule(message.author.id))


    if msg.startswith('!del') or msg.startswith('!remove') or msg.startswith('!delete'):
        args = msg.split(' ')
        if len(args) == 2:
            rm = remove_task(args[1],message.author.id)

            await message.channel.send('**Successfully removed {} tasks with the name of {}**'.format(rm,args[1]))
        else:
            await message.channel.send("Expected proper argument 'Task Name'")


    if msg.startswith('!help') or msg == '?' or msg.startswith('!h'):
        await message.channel.send(embed=help_embed)


clock_thread= threading.Thread(target=clock,args=(asyncio.get_event_loop(),client))



def main():
    
    client.run(data['token'])

main()
