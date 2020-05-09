from configparser import ConfigParser
from discord.ext import commands
from datetime import datetime
from .utils import checks
import logging
import sqlite3
import discord
import re

conn = sqlite3.connect('src/songwriters.db')
cursor = conn.cursor()
cursor.execute(f"CREATE TABLE IF NOT EXISTS introductions ('state' TEXT, 'msg' TEXT, 'embed_id' INT, 'user_id' INT, "
               f"'staff_embed_id' INT, 'staff_id' INT)")
cursor.close()
conn.commit()

patten = re.compile(r'^(//edit(\s)?)(.+)')
user_reactions = ('👍', '👎')
staff_reactions = ('✅', '❎', '🗑️')

parser = ConfigParser()
parser.read('config.ini')

INTRODUCTION_ROLE_ID = parser.getint('introduction', 'introduction-role-id')
INTRODUCTION_CHANNEL_ID = parser.getint('introduction', 'introduction-channel-id')
INTRODUCTION_STAFF_CHANNEL_ID = parser.getint('introduction', 'introduction-staff-channel-id')


log = logging.getLogger(__name__)


async def add_reaction(user, staff):
    for emoji in user_reactions:
        await user.add_reaction(emoji)

    for emoji in staff_reactions:
        await staff.add_reaction(emoji)


class Intro(commands.Cog, name='Introduction'):
    """Handle the all the introduction related commands and events."""

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        conn.close()

    async def intro_approve(self, member, staff):
        cur = conn.cursor()
        cur.execute(f"SELECT embed_id, staff_embed_id, msg FROM introductions WHERE user_id = {member.id}")
        userData = cur.fetchone()
        if userData is None:
            return
        channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_CHANNEL_ID)
        staff_channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_STAFF_CHANNEL_ID)

        user_intro = await channel.fetch_message(int(userData[0]))
        staff_intro = await staff_channel.fetch_message(int(userData[1]))

        e = await self.change_embed(user_intro, userData[2], discord.Color.green(), member)
        e.add_field(name=f"*Approved By:* ", value=f"{staff.name}")
        e.add_field(name=f"*Note:* ", value=f"Ayy, Now you have full access of this server. Enjoy your stay! :D")
        await user_intro.edit(content=f"{member.mention}", embed=e)
        e = await self.change_embed(staff_intro, userData[2], discord.Color.green(), member)
        e.add_field(name=f"*Approved By:* ", value=f"{staff.name}")
        e.add_field(name=f"*Note:* ", value=f"Tell them to be active!")
        await staff_intro.clear_reactions()
        await staff_intro.edit(content=f"{member.mention}", embed=e)
        cur.execute(f"UPDATE introductions SET state = 'Approved', staff_id = {staff.id} WHERE user_id = {member.id}")
        conn.commit()
        cur.close()
        role = discord.utils.get(member.guild.roles, id=INTRODUCTION_ROLE_ID)
        await member.remove_roles(role)

    async def intro_deny(self, member, staff):
        cur = conn.cursor()
        cur.execute(f"SELECT embed_id, staff_embed_id, msg FROM introductions WHERE user_id = {member.id}")
        userData = cur.fetchone()
        if userData is None:
            return
        channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_CHANNEL_ID)
        staff_channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_STAFF_CHANNEL_ID)

        user_intro = await channel.fetch_message(int(userData[0]))
        staff_intro = await staff_channel.fetch_message(int(userData[1]))

        e = await self.change_embed(staff_intro, userData[2], discord.Color.red(), member)
        e.add_field(name=f"*Denied By:* ", value=f"{staff.name}")
        e.add_field(name=f"*Note:* ", value=f"Well, They can re-introduce help them with syntax! :expressionless:")
        await staff_intro.clear_reactions()
        await staff_intro.edit(content=f"{member.mention}", embed=e)
        e = await self.change_embed(user_intro, userData[2], discord.Color.red(), member)
        e.add_field(name=f"*Denied By:* ", value=f"{staff.name}")
        e.add_field(name=f"*Note:* ", value=f"You can just re-introduce your self with proper 'syntax'")
        await user_intro.clear_reactions()
        await user_intro.edit(content=f"{member.mention}", embed=e)
        cur.execute(f"DELETE FROM introductions WHERE user_id = {member.id}")
        conn.commit()
        cur.close()

    async def change_embed(self, message, msg, color, user):
        e = discord.Embed(color=color)

        e.set_thumbnail(url=user.avatar_url)
        e.set_author(name=f"{user.name}'s introduction!", icon_url=user.avatar_url)
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.timestamp = datetime.utcnow()

        e.description = f"```{msg}```"
        return e

    async def embed(self, message, msg):
        e = discord.Embed(color=discord.Color.gold())
        e.set_thumbnail(url=message.author.avatar_url)
        e.set_author(name=f"{message.author.name}'s introduction!", icon_url=message.author.avatar_url)
        e.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.timestamp = datetime.utcnow()

        e.description = f"```{msg}```"
        e.add_field(name="*Note:* ", value="Please wait couple of hours our staff will go through your introduction.\n"
                                           "Make sure to use proper format. If you wants to edit or rewrite your "
                                           "introduction Please use `//edit` before your introduction starts. : ) "
                                           "(See pins for an example)")

        channel = discord.utils.get(message.guild.channels, id=INTRODUCTION_CHANNEL_ID)
        staff_channel = discord.utils.get(message.guild.channels, id=INTRODUCTION_STAFF_CHANNEL_ID)
        embed = await channel.send(embed=e)

        e.clear_fields()
        e.add_field(name="*Note:* ", value=f"Only one member allowed to react. You cannot un-react the emoji "
                                           f"to undo what you have done so be careful.")

        staff = await staff_channel.send(f"{message.author.mention}", embed=e)
        return embed, staff

    async def edit_embed(self, idS, newMsg, message):
        channel = discord.utils.get(message.guild.channels, id=INTRODUCTION_CHANNEL_ID)
        staff_channel = discord.utils.get(message.guild.channels, id=INTRODUCTION_STAFF_CHANNEL_ID)
        user_intro = await channel.fetch_message(int(idS[0]))
        await user_intro.delete()
        staff_intro = await staff_channel.fetch_message(int(idS[1]))
        await staff_intro.delete()
        return await self.embed(message, newMsg)

    async def set_introduction(self, message):
        if discord.utils.find(lambda r: r.id == INTRODUCTION_ROLE_ID, message.author.roles):
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM introductions WHERE user_id = {message.author.id}")
            user = cur.fetchone()
            if user is None:
                await message.delete()
                embed, staff = await self.embed(message, message.content)
                cur.execute(f'INSERT INTO introductions (state, msg, embed_id, user_id, staff_embed_id) '
                            f'VALUES ("Pending", "{message.content}", {embed.id}, {message.author.id}, {staff.id})')
                conn.commit()
                await add_reaction(embed, staff)
            elif user is not None:
                if patten.match(message.content):
                    data = patten.match(message.content)
                    await message.delete()
                    cur = conn.cursor()
                    cur.execute(f'SELECT embed_id, staff_embed_id FROM introductions '
                                f'WHERE user_id = {message.author.id}')
                    idS = cur.fetchone()
                    user, staff = await self.edit_embed(idS, data.group(3), message)
                    cur.execute(f'UPDATE introductions SET msg = "{data.group(3)}", embed_id = {user.id}, '
                                f'staff_embed_id = {staff.id} WHERE user_id = {message.author.id}')
                    conn.commit()
                    await add_reaction(user, staff)
                else:
                    if not message.author.guild_permissions.manage_messages:
                        channel = discord.utils.get(message.guild.channels, id=message.channel.id)
                        await message.delete()
                        await channel.send(f"{message.author.mention} You already introduced yourselves "
                                           f"You cannot chat here anymore!\n"
                                           "If you wants to edit or re-introduce your self please use "
                                           "`//edit before your intro starts ...`", delete_after=5)

    async def member_remove(self, member):
        cur = conn.cursor()
        cur.execute(f"SELECT embed_id, staff_embed_id, msg FROM introductions WHERE user_id = {member.id}")
        userData = cur.fetchone()
        if userData is None:
            return
        channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_CHANNEL_ID)
        staff_channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_STAFF_CHANNEL_ID)

        user_intro = await channel.fetch_message(int(userData[0]))
        await user_intro.delete()
        staff_intro = await staff_channel.fetch_message(int(userData[1]))
        await staff_intro.clear_reactions()

        e = await self.change_embed(staff_intro, userData[2], discord.Color.red(), member)
        e.add_field(name=f"*Note:* ", value=f"They might left the server, or you react with Dust-Bin! :triumph:")
        await staff_intro.edit(embed=e)
        cur.execute(f"DELETE FROM introductions WHERE user_id = {member.id}")
        conn.commit()
        cur.close()

    @commands.group(name='introduction', aliases=['intro', 'itd'], case_insensitive=False, invoke_without_command=True)
    @commands.guild_only()
    @checks.is_mod()
    async def intro_group(self, ctx):
        """Introduction is a group of command and handle the all the introduction's of a new user/newcomer."""
        e = discord.Embed(color=self.bot.color)
        e.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.timestamp = datetime.utcnow()

        e.description = f"Introduction module or group of commands is responsible to handle all the user's " \
                        f"introduction. If a user did not introduce themselves bot will not give them permission to " \
                        f"many channels and limit there access to limited channels like <#587969535802474511>"

        e.add_field(name="*Commands:* ", value=f"> `{ctx.prefix}role` - Create a new introduction role.\n"
                                               f"> `{ctx.prefix}show <member#1234>` - Show there introduction, "
                                               f"and staff who responsible for approval\n"
                                               f"> `{ctx.prefix}info` - Show the channel and role set for the "
                                               f"introduction'")
        await ctx.send(embed=e)
        log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Ask for introduction group!')

    @intro_group.command(name='role', aliases=['createRole'])
    async def intro_role(self, ctx):
        """Create introduction role for each channels. Note: You have to remove the role from the channels where you
         want user to get access of."""
        e = discord.Embed(color=self.bot.color)
        e.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.timestamp = datetime.utcnow()

        role = await ctx.guild.create_role(name='*', color=discord.Color.light_grey())
        e.description = f"Create & Setting roles. Please wait.."
        msg = await ctx.send(embed=e)
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, read_messages=True, send_messages=False)
        e.description = f'\u2705 **`SUCCESS`**: Role CREATED: `{role.name} (ID: {role.id})`'
        await msg.edit(embed=e)
        log.debug(f'User: {ctx.author} (ID: {ctx.author.id}) - Create a new introduction role!')

    @intro_group.command(name='show', aliases=['s'])
    async def intro_show(self, ctx, member: discord.User):
        """Show the user's introduction message and who approved with various other details about the user."""
        e = discord.Embed(color=self.bot.color)
        e.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.timestamp = datetime.utcnow()

        # TODO: Add introduction show.

    @intro_group.command(name='info', aliases=['information', 'details'])
    async def intro_info(self, ctx):
        """Show the current role and channel set for the introduction."""
        e = discord.Embed(color=self.bot.color)
        e.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        e.timestamp = datetime.utcnow()

        guild = self.bot.get_guild(ctx.guild.id)
        channel = guild.get_channel(INTRODUCTION_CHANNEL_ID)
        role = guild.get_role(INTRODUCTION_ROLE_ID)

        e.description = f"Introduction Channel: {channel.mention}\n" \
                        f"Introduction Role: {role.mention}"
        await ctx.send(embed=e)

    # Listeners
    @commands.Cog.listener()
    @commands.guild_only()
    async def on_member_join(self, member):
        """This listener is suppose to give a role to a new user on arrival."""
        channel = discord.utils.get(member.guild.channels, id=INTRODUCTION_CHANNEL_ID)
        role = discord.utils.get(member.guild.roles, id=INTRODUCTION_ROLE_ID)
        await member.add_roles(role)
        await channel.send(f"Hey {member.mention}, Please introduce yourself here it will give you "
                           f"full access of this server! (See the pin)",
                           delete_after=300)
        self.bot._prev_events.append("on_member_join - introduction.py")

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_member_remove(self, member):
        """This listener is suppose to delete there introduction from introduction channel and from database."""
        await self.member_remove(member)
        self.bot._prev_events.append("on_member_remove - introduction.py")

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        """This listener will trigger whenever a member sends a message in a guild."""
        if message.author.bot:
            return
        if isinstance(message.channel.type, discord.DMChannel):
            return

        if message.channel.id == INTRODUCTION_CHANNEL_ID:
            await self.set_introduction(message)
            self.bot._prev_events.append("on_message - introduction.py")

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_raw_reaction_add(self, reaction):
        """This call then a user react with emoji to a introduction."""
        if reaction.user_id == self.bot.user.id:
            return

        if reaction.channel_id != INTRODUCTION_STAFF_CHANNEL_ID:
            return

        guild = self.bot.get_guild(reaction.guild_id)
        react_user = guild.get_member(reaction.user_id)
        react_channel = guild.get_channel(reaction.channel_id)
        react_msg = await react_channel.fetch_message(reaction.message_id)

        cur = conn.cursor()
        cur.execute(f"SELECT state, embed_id, user_id, staff_id FROM introductions "
                    f"WHERE staff_embed_id = {reaction.message_id}")
        intro = cur.fetchone()

        if intro is None:
            return

        if intro[0] != 'Pending':
            return

        if not react_user.guild_permissions.manage_messages:
            await react_msg.remove_reaction(reaction.emoji, react_user)
            return

        if intro[3] is not None:
            await react_msg.remove_reaction(reaction.emoji, react_user)
            return

        react = str(reaction.emoji)
        user = guild.get_member(intro[2])

        if react == staff_reactions[0]:
            await self.intro_approve(user, react_user)
        elif react == staff_reactions[1]:
            await self.intro_deny(user, react_user)
        elif react == staff_reactions[2]:
            await self.member_remove(user)

        self.bot._prev_events.append("on_raw_reaction_add")


def setup(bot):
    bot.add_cog(Intro(bot))
