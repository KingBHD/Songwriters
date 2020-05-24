from configparser import ConfigParser
from discord.ext import commands
from collections import Counter
from datetime import datetime
import platform
import discord
import logging

log = logging.getLogger(__name__)

parser = ConfigParser()
parser.read('config.ini')
INTRODUCTION_CHANNEL_ID = parser.getint('introduction', 'introduction-channel-id')


class Information(commands.Cog, name='Information'):
    """Retrieve information about various items."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='whois', aliases=["who", "whoimi", "iam"])
    async def userinfo(self, ctx, user: discord.Member = None):
        """Throws out a detailed information about a user"""
        if user is None:
            user = ctx.message.author
        if user.activity is not None:
            game = user.activity.name
        else:
            game = None
        voice_state = None if not user.voice else user.voice.channel
        embed = discord.Embed(timestamp=ctx.message.created_at, colour=self.bot.color)
        embed.add_field(name='**User ID**', value=user.id, inline=True)
        embed.add_field(name='**Nick**', value=user.nick, inline=True)
        embed.add_field(name='**Status**', value=user.status, inline=True)
        embed.add_field(name='**On Mobile**', value=user.is_on_mobile(), inline=True)
        embed.add_field(name='**In Voice**', value=voice_state, inline=True)
        embed.add_field(name='**Game**', value=game, inline=True)
        embed.add_field(name='**Highest Role**', value=user.top_role.name, inline=True)
        embed.add_field(name='**Account Created**', value=user.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        embed.add_field(name='**Join Date**', value=user.joined_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))

        self.bot.cur.execute(f"SELECT state, staff_id, embed_id FROM introductions WHERE user_id = {user.id}")
        user_intro = self.bot.cur.fetchone()
        if user_intro is not None:
            embed.add_field(name='**Status:**', value=user_intro[0], inline=True)
            if user_intro[1] is not None:
                embed.add_field(name='**Approved by:**', value=f"<@{int(user_intro[1])}>")
            intro_channel = ctx.guild.get_channel(INTRODUCTION_CHANNEL_ID)
            intro_msg = await intro_channel.fetch_message(user_intro[2])
            embed.add_field(name='**Introduction:**', value=f"[Jump to Intro]({intro_msg.jump_url})")

        embed.set_thumbnail(url=user.avatar_url)
        embed.set_author(name=user, icon_url=user.avatar_url)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)
        log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Checked the user info of -> {user}!')

    @commands.command(name='serverstatus', aliases=["stats", "whereami"])
    async def serverinfo(self, ctx):
        """Throws out a detailed information about the server."""
        role_count = len(ctx.guild.roles)
        emoji_count = len(ctx.guild.emojis)
        channel_count = len([x for x in ctx.guild.channels if isinstance(x, discord.channel.TextChannel)])
        embed = discord.Embed(color=self.bot.color, timestamp=ctx.message.created_at)
        embed.add_field(name='**Name (ID)**', value=f"{ctx.guild.name} ({ctx.guild.id})")
        embed.add_field(name='**Owner**', value=ctx.guild.owner, inline=False)
        embed.add_field(name='**Members**', value=ctx.guild.member_count)
        embed.add_field(name='**Text Channels**', value=str(channel_count))
        embed.add_field(name='**Region**', value=ctx.guild.region)
        embed.add_field(name='**Verification Level**', value=str(ctx.guild.verification_level))
        embed.add_field(name='**Highest role**', value=ctx.guild.roles[-1])
        embed.add_field(name='**Number of roles**', value=str(role_count))
        embed.add_field(name='**Number of emotes**', value=str(emoji_count))
        embed.add_field(name='**Created At**', value=ctx.guild.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)
        log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Checked the server of -> {ctx.guild}!')

    @commands.command(name='bot', aliases=["botstatus", "info"])
    async def info_bot(self, ctx):
        """Give the bot's details like bot version, python version, creator and other details."""
        versioninfo = platform.sys.version_info
        major = versioninfo.major
        minor = versioninfo.minor
        micro = versioninfo.micro
        with open('.version', encoding='utf-8') as version:
            botVersion = version.read()
        embed = discord.Embed(title='Bot Information', description='Created by ɃĦɃĦĐ#2224',
                              color=self.bot.color)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(text=f'{self.bot.user.name}',
                         icon_url=self.bot.user.avatar_url)
        embed.add_field(name='**Total Guilds**', value=f'`{len(list(self.bot.guilds))}`', inline=True)
        embed.add_field(name='**Total Users**', value=f'`{len(list(self.bot.users))}`', inline=True)
        channel_types = Counter(isinstance(c, discord.TextChannel) for c in self.bot.get_all_channels())
        text = channel_types[True]
        embed.add_field(name='**Total Channels**', value=f'`{text}`', inline=True)
        embed.add_field(name='**Python Version**', value=f'`{major}.{minor}.{micro}`',
                        inline=True)
        embed.add_field(name='**Discord.py Version**', value=f'`{discord.__version__}`', inline=True)
        embed.add_field(name='**Bot Version**', value=f'`{botVersion}`', inline=True)
        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)
        log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Seen the bot stats and details!')


def setup(bot):
    bot.add_cog(Information(bot))
    log.info(f'Information Cog/Module Successfully Loaded!')
