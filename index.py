from pathlib import Path
import sqlite3
import sys
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import has_role
import discord.ext.commands.errors as discord_errors
import typing

from simple_logging import Logger
from db_setup import setup_db
from config import *

log = Logger('ug_bot', log_folder=Path(LOG_FOLDER).resolve(),
             log_level='debug', output_level='debug')

log.debug("Loaded all modules.")
log.info("Starting the bot...")

if not setup_db(log):
    log.error("Unable to setup the database.")
    sys.exit(1)

db = sqlite3.connect(DB_PATH)
log.debug("Connected to database.")

bot = commands.Bot(command_prefix=COMMAND_PREFIX)
log.info("Bot created with prefix {}.".format(COMMAND_PREFIX))


def get_users(db, name, *, is_full_name=False):
    c = db.cursor()
    # I doubt this is the 'sensible' way to do it
    if is_full_name:
        raw_rows = c.execute("SELECT name FROM names WHERE name=?;", [name])
    else:
        raw_rows = c.execute("SELECT name FROM names WHERE name LIKE ?;", [
            "%" + name + "%"])
    rows = [row[0] for row in raw_rows]
    c.close()
    return rows


def get_members(db, name, *, is_full_name=False):
    c = db.cursor()
    if is_full_name:
        raw_rows = c.execute("SELECT name FROM members WHERE name=?;", [name])
    else:
        raw_rows = c.execute("SELECT name FROM members WHERE name LIKE ?;", [
            "%" + name + "%"])
    rows = [row[0] for row in raw_rows]
    c.close()
    return rows


def get_unregistered(db, name, *, is_full_name=False):
    all = get_users(db, name, is_full_name=False)
    reg = get_members(db, name, is_full_name=False)
    new = [p for p in all if p not in reg]
    return new

# TODO: Implement this, after making the nescessary tables in the database
# Implement *what*?


def register_new(db, name, id):
    c = db.cursor()
    log.debug("Registering: {} as {}".format(id, name))
    c.execute("INSERT INTO members VALUES(?, ?);", [id, name])
    c.close()
    db.commit()
    return True


def style_name(name):
    return name.title()  # maybe change this later


async def register_actual(ctx, user, *, name, is_full_name=False):
    member_role = ctx.guild.get_role(member_role_id)
    log.debug("Registration requested for {} by {} with name {}.".format(
        user, ctx.author, name))
    if member_role in user.roles:
        log.debug("They were already registered.")
        await ctx.send("{} is already registered!".format(user))
        return
    name = name.upper()
    ok_names = get_unregistered(db, name, is_full_name=False)
    log.debug("Users with name {}: {}".format(name, ok_names))
    if len(ok_names) == 0:
        log.debug("No results found for name: {}".format(name))
        await ctx.send("No users found with name {}. Please try again.".format(name))
    elif len(ok_names) == 1:
        name = ok_names[0]
        log.debug("Only one result found: {}. Registering.".format(name))
        id = user.id
        if register_new(db, name, id):
            full_name = style_name(name)
            await user.add_roles(member_role, reason='New member')
            try:
                await user.edit(reason='Use full name', nick=full_name)
            except discord.errors.Forbidden as e:
                log.warn(
                    "Could not change nickname for {}, they are probably admin".format(user))
            await ctx.send("{}, registered {} sucessfully as `{}`!".format(ctx.author.mention, user.mention, name))
        else:
            await ctx.send("There was an error. Please contact the admins.")
    else:
        ok_names_list = ""
        for i, okn in enumerate(ok_names):
            ok_names_list += "\n{}. {}".format(i, okn)
        log.debug("Multiple results found for {}. They were:{}".format(
            name, ok_names_list))
        await ctx.send("Multiple results were found for the name {}. Please register again with the full name.".format(name))


# def is_mod():
#    async def predicate(ctx):
#        return ctx.guild and ctx.guild.get_role(mod_role_id) in ctx.author.roles
#    return commands.check(predicate)

def in_welcome():
    def predicate(ctx):
        return ctx.message.channel.id == welcome_id
    return commands.check(predicate)

# Unused code. WHY is this here?
@bot.check
def only_this_guild(ctx):
    return ctx.guild and ctx.guild.id == guild_id


@bot.event
async def on_ready():
    log.success("Bot running!")


@bot.command()
@has_role(mod_role_id)
async def shutdown(ctx):
    """[Mods only] Shuts down the bot."""
    log.warn("Bot shutdown requested by: {}".format(ctx.author))
    await bot.logout()


@bot.command()
# @has_role(mod_role_id)
async def hello(ctx):
    """[Mods only] Replies with hello. For testing purposes."""
    log.debug("Saying hello to {}".format(ctx.author.name))
    await ctx.send("Hello, {}".format(ctx.author.mention))


@bot.command()
@in_welcome()
async def reg(ctx, *, name):
    """Register yourself. Gives you the proper roles."""
    await register_actual(ctx, ctx.author, name=name)


@bot.command()
@in_welcome()
async def reg_full(ctx, *, name):
    """Register yourself with full name explicitly. Gives you the proper roles."""
    await register_actual(ctx, ctx.author, name=name, is_full_name=True)


@bot.command()
@in_welcome()
@has_role(mod_role_id)
async def reg_m(ctx, user: discord.Member, *, name):
    """[Mods only] Registers someone else."""
    await register_actual(ctx, user, name=name)


@bot.command()
@in_welcome()
@has_role(mod_role_id)
async def reg_full_m(ctx, user: discord.Member, *, name):
    """[Mods only] Registers someone else with full name explicitly."""
    await register_actual(ctx, user, name=name, is_full_name=True)


@bot.command()
@in_welcome()
@has_role(mod_role_id)
async def reg_s(ctx, user: discord.Member, *, name):
    """[Mods only] Registers a senior."""
    log.debug("Registration of senior requested for {} by {} with name {}.".format(
        user, ctx.author, name))
    full_name = style_name(name)
    await user.add_roles(ctx.guild.get_role(senior_role_id), reason='New senior')
    try:
        await user.edit(reason='Use full name', nick=full_name)
    except discord.errors.Forbidden as e:
        log.warn(
            "Could not change nickname for {}, they are probably admin".format(user))
    await ctx.send("{}, registered {} sucessfully as `{}`!".format(ctx.author.mention, user.mention, name))


@bot.command()
@has_role(mod_role_id)
async def mute(ctx, user: discord.Member):
    """[Mods only] Mutes a member. They cannot speak in any public channels."""
    log.debug("Mute requested by {} for {}.".format(ctx.author, user))
    await user.add_roles(ctx.guild.get_role(muted_id))
    await ctx.send("{} muted successfully!".format(user.mention))


@bot.command()
@has_role(mod_role_id)
async def unmute(ctx, user: discord.Member):
    """[Mods only] Unmutes a member."""
    log.debug("Unmute requested by {} for {}.".format(ctx.author, user))
    await user.remove_roles(ctx.guild.get_role(muted_id))
    await ctx.send("{} unmuted successfully!".format(user.mention))

@bot.command()
async def kawaii(ctx, user: typing.Optional[discord.Member] = 'lmao'):
    """ calls user kawaii """
    # WANT to call the guy who called the function kawaii if user is empty, pls do something
    if user == "lmao":
        await ctx.send("{} is so kawaii".format(ctx.author.mention))
    else:
        await ctx.send("{} is so kawaii".format(user.mention))


@bot.event
async def on_member_join(member):
    log.debug("New member?", member)
    if member.guild.id == guild_id:
        log.info("New member joined: {}".format(member))
        await member.guild.get_channel(welcome_id).send(("Welcome, {}! Please register using `!reg <your name>` to access the full server.\n"
                                                         "If you are a seior, please as a Moderator to register you."))

@bot.event
async def on_command_error(ctx, error):
    log.debug("Command error: {}".format(error))
    if isinstance(error, discord_errors.CheckFailure):
        log.debug("Check Failure.")
    else:
        log.warn("".join(traceback.format_exception(type(error), error, error.__traceback__)))


log.debug("Loaded all.")
bot.run(token)
log.debug("Closing database.")
db.close()
log.warn("Bot shut down.")
