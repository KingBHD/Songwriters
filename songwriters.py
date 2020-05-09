from discord.ext import commands
from cogs.utils import context
from discord.ext import tasks
from collections import deque
from itertools import cycle
import configparser
import traceback
import datetime
import logging
import discord
import aiohttp
import json
import sys
import csv


parser = configparser.ConfigParser()
parser.read('config.ini')
ACTIVITY_INTERVAL = parser.getint('default', 'activity-change-time-interval')

description = "A discord bot made py ɃĦɃĦĐ#2224 using discord.py API by Rapptz"
activities = []
initial_extensions = ['cogs.owner', 'cogs.errors',
                      'cogs.introduction']

with open("src/activities.csv", "r", encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=",")
    for rows in reader:
        for row in rows:
            activity = row
            activities.append(activity)
activities = cycle(activities)


class songwriter(commands.AutoShardedBot):

    def __init__(self):
        super().__init__(command_prefix=(parser.get('default', 'prefix')), description=description,
                         owner_id=parser.getint('discord', 'owner-id'), case_insensitive=False)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.uptime = datetime.datetime.utcnow()
        self._prev_events = deque(maxlen=10)
        self.cogsList = initial_extensions
        self.color = 0x95efcc

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                self.log.error(f'Failed to load extension {extension}, {e}', file=sys.stderr)
                traceback.print_exc()

    @tasks.loop(seconds=ACTIVITY_INTERVAL)
    async def maintain_presence(self):
        current_activity = next(activities)
        await super().change_presence(activity=discord.Game(name=current_activity))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()
        self.maintain_presence.start()

        print(f'Ready: {self.user} (ID: {self.user.id})')

    async def on_resumed(self):
        print('resumed...')

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        try:
            await self.invoke(ctx)
        except Exception as e:
            print(e)

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def close(self):
        await super().close()
        await self.session.close()
        print('Sessions closed!')

    def run(self):
        try:
            super().run(parser.get('discord', 'token'), reconnect=True)
        finally:
            with open('logs/prev_events.log', 'w', encoding='utf-8') as fp:
                for data in self._prev_events:
                    try:
                        x = json.dumps(data, ensure_ascii=True, indent=4)
                    except Exception as e:
                        fp.write(f'{data}\n')
                        print(f'Data written in {fp} with Exception{e}')
                    else:
                        fp.write(f'{x}\n')

    @property
    def config(self):
        return __import__('config')

