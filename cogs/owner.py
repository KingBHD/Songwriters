# !/usr/bin/python3
from sys import platform, exit as shutdown
from discord.ext import commands
from datetime import datetime
from discord.ext import tasks
from .utils import time
import platform
import logging
import discord
import os

log = logging.getLogger(__name__)
directory = os.path.dirname(os.path.realpath(__file__))
with open(f".version") as f:
    __version__ = f.read().rstrip("\n").rstrip("\r")


def restart():
    os.chdir(directory)
    python = "python" if platform == "win32" else "python3"
    cmd = os.popen(f"nohup {python} launcher.py &")
    cmd.close()


class Owner(commands.Cog, name='Owner'):
    """Owner-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        # self.updates.start()

    async def get_latest(self):
        data = await self.bot.session.get(
            "https://raw.githubusercontent.com/BHBHD/Songwriters/master/.version"
        )
        res = await data.text()
        return res

    async def check_for_updates(self):
        # Get latest version from GitHub repo and checks it against the current one
        latest = await self.get_latest()
        if latest > __version__:
            return latest
        return False

    def get_bot_uptime(self, *, brief=False):
        return time.human_timedelta(self.bot.uptime, accuracy=None, brief=brief, suffix=False)

    @tasks.loop(seconds=30)
    async def updates(self):
        # Sends a reminder once a day if there are updates available
        new_version = await self.check_for_updates()
        if new_version:
            print(f"An update is available. Download Songwriters v{new_version} at "
                  f"https://github.com/BHBHD/Songwriters "
                  f"or simply use `!update` (only works with git installations).\n\n")

    @commands.command(hidden=True)
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
            log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Trying to Load -> {module}!')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
            log.exception(f'User: {ctx.author} (ID: {ctx.author.id}) - Failed to Load -> {module}!')
        else:
            await ctx.send('\N{OK HAND SIGN}')
            log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Successfully Loaded -> {module}!')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
            log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Trying to Unload -> {module}!')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
            log.exception(f'User: {ctx.author} (ID: {ctx.author.id}) - Failed to Unload -> {module}!')
        else:
            await ctx.send('\N{OK HAND SIGN}')
            log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Successfully Unloaded -> {module}!')

    @commands.group(name='reload', hidden=True, invoke_without_command=True)
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.reload_extension(module)
            log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Trying to Reload -> {module}!')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
            log.exception(f'User: {ctx.author} (ID: {ctx.author.id}) - Failed to Reload -> {module}!')
        else:
            await ctx.send('\N{OK HAND SIGN}')
            log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Successfully Reloaded -> {module}!')

    @_reload.command(name='all')
    async def reload(self, ctx):
        """Reloads all module."""
        for ext in self.bot.cogsList:
            try:
                if hasattr(self, "bot"):
                    self.bot.reload_extension(ext)
                else:
                    self.bot.reload_extension(ext)
                log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Successfully to Reload all!')
            except Exception as e:
                log.error(f"ERROR: FAILED to load extension: {ext}")
                log.error(f"\t{e.__class__.__name__}: {e}\n")

    @commands.command(name='shutdown', aliases=["sd", "kill", "quit"], hidden=True)
    @commands.is_owner()
    async def shutdown_cmd(self, ctx):
        """Shuts the bot down."""
        e = discord.Embed(color=self.bot.color)
        e.timestamp = datetime.utcnow()
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        log.info(f'User: {ctx.author} (ID: {ctx.author.id}) - Shutdowns the {self.bot.user}!')
        e.description = "Goodbye!"
        await ctx.send(embed=e)
        await self.bot.logout()

    @commands.is_owner()
    @commands.command(name='restart', aliases=["reboot", "reset", "reignite"], hidden=True)
    async def restart_cmd(self, ctx):
        e = discord.Embed(color=self.bot.color)
        e.timestamp = datetime.utcnow()
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        if platform != "win32":
            restart()
            e.description = "Restarting..."
            await ctx.send(embed=e)
            shutdown()
        else:
            e.description = "I cannot do this on Windows."
            await ctx.send(embed=e)

    @commands.command(name='activity', aliases=["botactivity", "presence"], hidden=True)
    @commands.is_owner()
    async def activity_bot(self, ctx):
        e = discord.Embed(color=self.bot.color)
        e.timestamp = datetime.utcnow()
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.description = "```1 - Playing\n" \
                        "2 - Listening \n" \
                        "3 - Watching\n" \
                        "4 - Nothing (Empty)```"
        que = await ctx.send(embed=e)
        none = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
        e.description = "```Type a status activity that you want to show after playing ... ```"
        await que.edit(embed=e)
        await none.delete()
        activity = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
        await activity.delete()
        await self.bot.change_presence(activity=discord.Activity(type=none.content,
                                                                 name=activity.content),
                                       status=discord.Status.online)
        e.description = 'Done, My status is changed!'
        await que.edit(embed=e)
        self.bot.maintain_presence.cancel()
        log.info(f'User: {ctx.author} (ID: {ctx.author.id}) - Changed the bot status to {self.bot.activity}!')

    @commands.group(name='cycle', aliases=["botstatuscycle", "presencecycle"], hidden=True, invoke_without_command=True)
    @commands.is_owner()
    async def activity_cycle_bot(self, ctx):
        e = discord.Embed(color=self.bot.color)
        e.timestamp = datetime.utcnow()
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        try:
            self.bot.maintain_presence.start()
            e.description = 'Starting..'
            await ctx.send(embed=e)
            log.info(f'User: {ctx.author} (ID: {ctx.author.id}) - Starts the bot presence cycle!')
        except RuntimeError:
            e.description = 'Task is already running!'
            await ctx.send(embed=e)

    @activity_cycle_bot.command(name='stop', hidden=True)
    @commands.is_owner()
    async def activity_cycle_bot_stop(self, ctx):
        e = discord.Embed(color=self.bot.color)
        e.timestamp = datetime.utcnow()
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        try:
            self.bot.maintain_presence.stop()
            e.description = 'Stopped!'
            await ctx.send(embed=e)
            log.info(f'User: {ctx.author} (ID: {ctx.author.id}) - Stop the bot presence cycle!')
        except Exception as e:
            e.description = f'{str(e)}'
            await ctx.send(embed=e)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def uptime(self, ctx):
        """Tells you how long the bot has been up for."""
        await ctx.send(f'Uptime: **{self.get_bot_uptime()}**')
    
    @commands.command(name='purge', aliases=["removemsg", "rm"])
    async def prune(self, ctx, count: int):
        """Deletes a specified amount of messages. (Max 100)"""
        e = discord.Embed(color=self.bot.color)
        if ctx.author.guild_permissions.manage_message or ctx.author.id == self.bot.owner.id:
            if count > 100:
                count = 100
            await ctx.message.channel.purge(limit=count, bulk=True)
            e.title = f"SUCCESS: Purge {count} msgs"
            await ctx.send(embed=e, delete_after=3)
            log.info(f'User: {ctx.author} (ID: {ctx.author.id}) - prune {count} messages in {ctx.channel}')
        else:
            e.title = 'Oof, You don\'t have `manage messages` perms'
            await ctx.send(embed=e)

    @commands.command(name='clear', aliases=["removebot", "brm"])
    async def clean(self, ctx):
        """Cleans the chat of the bot's messages."""
        e = discord.Embed(color=self.bot.color)
        if ctx.author.guild_permissions.manage_message or ctx.author.id == self.bot.owner.id:
            def is_me(m):
                return m.author == self.bot.user

            await ctx.message.channel.purge(limit=100, check=is_me)
            log.info(f'User: {ctx.author} (ID: {ctx.author.id}) - clean bot messages in {ctx.channel}')
        else:
            e.title = 'Oof, You don\'t have `manage messages` perms'
            await ctx.send(embed=e)

    @commands.command(name="update")
    @commands.is_owner()
    async def update(self, ctx):
        if platform != "win32":
            await ctx.send("Attempting update...")
            # os.chdir(directory)
            cmd = os.popen("git fetch")
            cmd.close()
            cmd = os.popen("git pull")
            cmd.close()
            # restart()
            await ctx.send("Restarting...")
            # shutdown()  # sys.exit()
        else:
            await ctx.send("I cannot do this on Windows.")

    @commands.command(name="version")
    async def print_version(self, ctx):
        latest = await self.get_latest()
        await ctx.send(f"I am currently running v{__version__}. The latest available version is v{latest}.")


def setup(bot):
    bot.add_cog(Owner(bot))
    log.debug(f'Owner Cog/Module Loaded Successfully!')
