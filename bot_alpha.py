# TODO list
# Check valid lang code, only accept iso 639-2 (ma not working?)
# Create method that sends temp message to ctx channel, permanent msg to log 
## Allow to set the log channel from within
# Cleanup categories or channels that no longer exists
# Add signature for easy deleting/Delete rita msg
# Delete author's original message after some time
# Allow linking by name, multiple names.
# Allow setting category or adding channels by name.
# Add completion message for linking.

# Bugs:
# Database locked while linking.
# ma language code not recognized
# Category show with emoji not working

import os
import discord
from discord.ext import commands
import sqlite3

DB_PATH = "language_groups.db"
TOKEN = "Enter token here"
GUILD = 0 # Guild ID goes here (integer)
BOT_CHANNEL = 0 # Bot channel ID goes here (integer)

MSG_EXPIRY = 60

# client = discord.Client()
bot = commands.Bot(command_prefix="$")

@bot.event
async def on_ready():
    """ Prints information on connection. """
    
    # Ensure only connected to one guild
    if len(bot.guilds) > 1:
        raise Exception("Not handled to run on more than one guild!")
    guild = bot.guilds[0]
    if guild.id != GUILD:
        raise Exception("Guild is not same as target guild.")

    # Initialize database
    initialize_db()

    # Say hello
    print(f"{bot.user} is connected to the following guild:\n"
          f"{guild.name} (id: {guild.id})")

    await bot.get_channel(BOT_CHANNEL).send("A wild bot has appeared!")

def initialize_db():
    """ Checks if database and tables exists, otherwise create it. """
    
    # Connect to database (will create if doesn't exist)
    conn = sqlite3.connect(DB_PATH)

    # Create tables if they don't exist
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS Category (
                        CategoryId  INTEGER PRIMARY KEY,
                        Lang        TEXT NOT NULL
                   )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS LangGroup (
                        Name        TEXT PRIMARY KEY
                   )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS Channel (
                        LangGroup   TEXT,
                        ChannelId   INTEGER PRIMARY KEY,
                        FOREIGN KEY (LangGroup) REFERENCES LangGroup (Name)
                    )""")
    conn.commit()
    conn.close()


@bot.command()
@commands.has_permissions(administrator=True)
async def mb(ctx, *args):
    """ Detects a command. """

    await command_handler(ctx, args)

async def command_handler(ctx, args):
    """ Sends command to correct command handler based on first argument. """

    if len(args) < 1:
        await ctx.send("Need at least 1 argument.", delete_after=MSG_EXPIRY)
        return

    if args[0] == "group":
        await group_command_handler(ctx, args[1:])
    elif args[0] == "category":
        await category_command_handler(ctx, args[1:])
    elif args[0] == "channel":
        await channel_command_handler(ctx, args[1:])
    elif args[0] == "link":
        await link_command_handler(ctx, args[1:])
    elif args[0] == "unlink":
        await unlink_command_handler(ctx, args[1:])
    elif args[0] == "ping":
        await ping_command_handler(ctx)
    else:
        await ctx.send(f"Unknown command: `{args[0]}`",
                        delete_after=MSG_EXPIRY)


async def group_command_handler(ctx, args):
    """ Creates, deletes or lists groups, which hold group of channels
    representing a single channel, but in multiple languages.
    """

    if len(args) < 1:
        await ctx.send("Incorrect number of arguments for `group`.",
                       delete_after=MSG_EXPIRY)
        return

    # No arguments required for list
    if args[0] == "get":
        await get_groups(ctx)
        return
    elif args[0] == "list":
        await list_groups(ctx)
        return
    elif len(args) < 2:
        await ctx.send("Incorrect number of arguments for `group`.",
                       delete_after=MSG_EXPIRY)
        return

    # Make group all lowercase
    group = args[1].lower()
    
    if args[0] == "create":
        await create_group(ctx, group)
    elif args[0] == "delete":
        await delete_group(ctx, group)
    elif args[0] == "show":
        await show_group(ctx, group)
    else:
        await ctx.send(f"Unknown option: `{args[0]}`", delete_after=MSG_EXPIRY)

async def category_command_handler(ctx, args):
    """ Sets or unsets the language of a category, which holds channels of
    similar languages.
    """

    if args[0] == "list":
        await list_categories(ctx)
        return

    # Get category ID
    categoryID = ctx.channel.category_id
    if categoryID == None:
        await ctx.send("This channel is not under a category.",
                       delete_after=MSG_EXPIRY)
        return

    if args[0] == "set":
        if len(args) < 2:
            await ctx.send("Incorrect number of arguments for `category set`.",
                           delete_after=MSG_EXPIRY)
            return
        await set_category_lang(ctx, args[1])
    elif args[0] == "unset":
        await unset_category_lang(ctx)
    elif args[0] == "get":
        await get_category_lang(ctx)
    elif args[0] == "show":
        if len(args) < 2:
            await ctx.send("Incorrect number of arguments for"
                           "`category show`.",
                           delete_after=MSG_EXPIRY)
        await show_category(ctx, args[1])
    else:
        await ctx.send(f"Unknown option: `{args[0]}`", delete_after=MSG_EXPIRY)

async def channel_command_handler(ctx, args):
    """ Adds or removes a channel from a group. """

    if len(args) < 2:
        await ctx.send("Incorrect number of arguments for `channel`.",
                       delete_after=MSG_EXPIRY)
        return

    # Make sure group is all lowercase
    group = args[1].lower()

    if args[0] == "add":
        await add_channel(ctx, group)
    elif args[0] == "remove":
        await remove_channel(ctx, group)
    else:
        await ctx.send(f"Unknown option: `{args[0]}`", delete_after=MSG_EXPIRY)

async def link_command_handler(ctx, args):
    """ Links channels together via RITA's auto-translation feature. """

    if len(args) < 1:
        await ctx.send("Incorrect number of arguments for `link`.",
                       delete_after=MSG_EXPIRY)
        return

    if args[0] == "channel":
        await link_channels(ctx, args[1:])
    elif args[0] == "group":
        await link_groups(ctx, args[1:])
    elif args[0] == "category":
        await link_categories(ctx, args[1:])
    elif args[0] == "all":
        await link_all(ctx)
    else:
        await ctx.send(f"Unknown option: `{args[0]}`", delete_after=MSG_EXPIRY)

async def unlink_command_handler(ctx, args):
    """ Unlinks RITA's auto-translation features between channels. """

    if len(args) < 1:
        await ctx.send("Incorrect number of arguments for `unlink`.",
                       delete_after=MSG_EXPIRY)
        return

    if args[0] == "channel":
        await unlink_channels(ctx, args[1:])
    elif args[0] == "group":
        await link_groups(ctx, args[1:])
    elif args[0] == "category":
        await unlink_categories(ctx, args[1:])
    elif args[0] == "all":
        await unlink_all(ctx)
    else:
        await ctx.send(f"Unknown option: `{args[0]}`", delete_after=MSG_EXPIRY)

async def ping_command_handler(ctx):
    """ Pings bot. Bot replies Pong! """
    await ctx.send("Pong!", delete_after=MSG_EXPIRY)

async def create_group(ctx, group):
    """ Create a group by creating and recording it in the database. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # First, check that group does not already exist
    cur.execute("SELECT Name FROM LangGroup WHERE Name = ?", (group,))
    if cur.fetchone() != None:
        await ctx.send("Group already exists!", delete_after=MSG_EXPIRY)
        return

    # Add to groups table
    cur.execute("INSERT INTO LangGroup (Name) VALUES (?)", (group,))
    conn.commit()
    conn.close()

    await ctx.send(f"Created group: `{group}`", delete_after=MSG_EXPIRY)

async def delete_group(ctx, group):
    """ Create a group by creating and recording it in the database. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # First, check if group exists
    cur.execute("SELECT Name FROM LangGroup WHERE Name = ?", (group,))
    if cur.fetchone() == None:
        await ctx.send("Group doesn't exist.", delete_after=MSG_EXPIRY)
        return

    # Delete channels in the group from the channels' table
    cur.execute("DELETE FROM Channel WHERE LangGroup = ?", (group,))

    # Remove from groups' table
    cur.execute("DELETE FROM LangGroup WHERE Name = ?", (group,))
    conn.commit()
    conn.close()
    await ctx.send("Deleted group: " + group, delete_after=MSG_EXPIRY)

async def get_groups(ctx):
    """ Gets the groups the channel is in. """

    # Get the channel's groups
    channel = ctx.channel
    groups = get_channel_groups(channel)
    if len(groups) == 0:
        await ctx.send("This channel is not in any groups.",
                       delete_after=MSG_EXPIRY)
        return
    
    group_list = ", ".join([f"`{group}`"
                            for group in get_channel_groups(channel)])
    await ctx.send(f"<#{channel.id}> is in the following groups: " 
                   + group_list, delete_after=MSG_EXPIRY)

async def list_groups(ctx):
    """ Lists all groups, with the number of channels in them. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get all groups, aggregate number of channels in them
    cur.execute("""SELECT LangGroup, COUNT(ChannelId) 
                    FROM Channel
                   GROUP BY LangGroup""")
    output = ["All groups:"]
    for group, num_channels in cur:
        output.append(f"\t`{group}` — {num_channels} channels")
    conn.close()

    await ctx.send("\n".join(output), delete_after=MSG_EXPIRY)


async def show_group(ctx, group):
    """ Show all channels in group, with their languages. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get all channels in the group, and get their languages
    cur.execute("SELECT ChannelId FROM Channel WHERE LangGroup = ?", (group,))
    output = [f"Channels in `{group}` group:"]
    for row in cur:
        channel = bot.get_channel(row[0])
        lang = await get_channel_lang(ctx, channel, require_valid=False)

        output.append(f"\t<#{channel.id}> — **{lang}**")
    conn.close()

    await ctx.send("\n".join(output), delete_after=MSG_EXPIRY)

async def list_channels(ctx, group):
    """ Lists all the channels in any group. """

    await ctx.send("To be modified.", delete_after=MSG_EXPIRY)
    return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # First, check if group exists
    cur.execute("SELECT Name FROM LangGroup WHERE Name = ?", (group,))
    if cur.fetchone() == None:
        await ctx.send("Group doesn't exist.", delete_after=MSG_EXPIRY)
        return

    cur.execute(f"SELECT ChannelId FROM {group}_Channel")
    output = [f"Channels in `{group}`:"]
    for i, row in enumerate(cur):
        channel_id = row[0]
        # category = bot.get_channel(channel_id).category
        # TODO: Get lang, category

        output.append(f"\t{i + 1}. <#{channel_id}>")
    conn.close()

    await ctx.send("\n".join(output), delete_after=MSG_EXPIRY)

async def set_category_lang(ctx, lang):
    """ Assigns a language to a category. """
    
    # Get category's ID
    category = ctx.channel.category

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Set new language or override existing
    cur.execute("""INSERT OR REPLACE INTO Category (CategoryId, Lang)
                   VALUES(?, ?)""", (category.id, lang))
    conn.commit()
    conn.close()

    await ctx.send(f"Set language for `{category}` to **{lang}**.",
                    delete_after=MSG_EXPIRY)

async def unset_category_lang(ctx):
    """ Removes assigned language from category. """

    # Get category's ID
    category = ctx.channel.category

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if category exists
    cur.execute("SELECT CategoryId FROM Category WHERE CategoryId = ?",
                (category.id,))
    if cur.fetchone() == None:
        await ctx.send("Language is already unset for `{category}`.", 
                        delete_after=MSG_EXPIRY)
        return

        # Unset category
    cur.execute("DELETE FROM Category WHERE CategoryId = ?", (category.id,))
    conn.commit()
    conn.close()

    await ctx.send(f"Unset language for `{category}`.",
                    delete_after=MSG_EXPIRY)

def return_category_lang(category):
    """ Returns the category's language as a string, assuming category exists.
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Set new language or override existing
    cur.execute("SELECT lang FROM Category WHERE CategoryId = ?",
                (category.id,))
    result = cur.fetchone()
    conn.commit()
    conn.close()

    if result == None:
        return None
    else:
        return result[0]

async def get_category_lang(ctx):
    """ Gets the category's language. """

    category = ctx.channel.category
    lang = return_category_lang(category)

    if lang == None:
        await ctx.send(f"`{category}` does not have a language set.",
                        delete_after=MSG_EXPIRY)
        return

    await ctx.send(f"`{category}` language is set to **{lang}**.",
                    delete_after=MSG_EXPIRY)

async def list_categories(ctx):
    """ Lists all the categories, with their language.
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get all categories, with their language
    cur.execute("SELECT CategoryId, Lang FROM Category")
    output = ["All categories:"]
    for category_id, lang in cur:
        category = discord.utils.get(ctx.guild.categories, id=category_id)
        output.append(f"\t`{category}` — **{lang}**")
    conn.close()

    await ctx.send("\n".join(output), delete_after=MSG_EXPIRY)


async def show_category(ctx, categoryName):
    """ Lists all the channels in a category, with their groups. """

    # Get all channels, then find their groups
    category = discord.utils.get(ctx.guild.categories, name=categoryName)
    if category == None:
        await ctx.send("Category does not exist.", delete_after=MSG_EXPIRY)
        return

    output = ["Channels in `{category}` category:"]
    for channel in category.channels:
        groups = [f"`{group}`" for group in get_channel_groups(channel)]
        output.append("\t<#{}> — Groups: {}".format(channel.id, 
                      ", ".join(groups)))

    await ctx.send("\n".join(output), delete_after=MSG_EXPIRY)

async def add_channel(ctx, group):
    """ Adds a channel to a group. """

    # Check if channel belongs to a category
    channel = ctx.channel
    category = channel.category
    if category == None:
        ctx.send("Channel must be under a category.", delete_after=MSG_EXPIRY)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if group exists
    cur.execute("SELECT Name FROM LangGroup WHERE Name = ?", (group,))
    if cur.fetchone() == None:
        await ctx.send("Group doesn't exist.", delete_after=MSG_EXPIRY)
        return

    # Check if already in group
    cur.execute("SELECT ChannelId FROM Channel WHERE ChannelId = ?",
                (channel.id,))
    if cur.fetchone() != None:
        await ctx.send("Channel has already been added.",
                        delete_after=MSG_EXPIRY)
        return

    # Add to group
    cur.execute("INSERT INTO Channel (LangGroup, ChannelId) VALUES (?, ?)",
                (group, channel.id))

    conn.commit()
    conn.close()

    await ctx.send(f"Added <#{channel.id}> to group `{group}`.",
                    delete_after=MSG_EXPIRY)

async def remove_channel(ctx, group):
    """ Removes a channel from a group. """

    channel = ctx.channel

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if group exists
    cur.execute("SELECT Name FROM LangGroup WHERE Name = ?", (group,))
    if cur.fetchone() == None:
        await ctx.send("Group doesn't exist.", delete_after=MSG_EXPIRY)
        return

    # Check if already removed from group
    cur.execute("SELECT ChannelId FROM Channel WHERE ChannelId = ?",
                (channel.id,))
    if cur.fetchone() == None:
        await ctx.send("Channel is already not in the group.",
                        delete_after=MSG_EXPIRY)
        return

    # Remove channel from group
    cur.execute("DELETE FROM Channel WHERE (ChannelId = ? AND LangGroup = ?)",
                (channel.id, group))

    conn.commit()
    conn.close()

    await ctx.send(f"Removed channel <#{channel.id}> to group `{group}`.",
                    delete_after=MSG_EXPIRY)

async def link_channels(ctx, args):
    """ Either links the current channel or multiple channels. """
    
    # No arguments: Link current channel
    if len(args) == 0:
        await link_channel(ctx, ctx.channel, require_valid=True)
    else:
        await ctx.send("Linking multiple channels has not been implemented "
                        "yet.", delete_after=MSG_EXPIRY)

async def link_groups(ctx, args):
    """ Either links the current channel's group or multiple groups. """
    
    # No arguments: Link current channel's groups
    if len(args) == 0:
        # Get the channel's groups
        groups = get_channel_groups(ctx.channel)
        if len(groups) == 0:
            await ctx.send("This channel is not in a group.",
                           delete_after=MSG_EXPIRY)
            return

        # Link each group
        for group in groups:
            await link_group(ctx, group)
    else:
        await ctx.send("Linking multiple groups has not been implemented "
                        "yet.", delete_after=MSG_EXPIRY)

async def link_categories(ctx, args):
    """ Either links the current category or multiple categories. """

    # No arguments: Link current category
    if len(args) == 0:
        await link_category(ctx, ctx.channel.category)
    else:
        await ctx.send("Linking multiple categories has not been implemented "
                       "yet", delete_after=MSG_EXPIRY)

async def unlink_channels(ctx, args):
    """ Either links the current channel or multiple channels. """
    
    # No arguments: Link current channel
    if len(args) == 0:
        await unlink_channel(ctx, ctx.channel)
        return
    else:
        await ctx.send("Unlinking multiple channels has not been implemented "
                        "yet.", delete_after=MSG_EXPIRY)

async def unlink_groups(ctx, args):
    """ Either links the current channel's group or multiple groups. """
    
    # No arguments: Unink current channel's groups
    if len(args) == 0:
        # Get the channel's groups
        groups = get_channel_groups(ctx.channel)
        if len(groups) == 0:
            await ctx.send("This channel is not in a group.",
                           delete_after=MSG_EXPIRY)
            return

        # Unlink each group
        for group in groups:
            await unlink_group(ctx, group)
    else:
        await ctx.send("Unlinking multiple groups has not been implemented "
                        "yet.", delete_after=MSG_EXPIRY)

async def unlink_categories(ctx, args):
    """ Either links the current category or multiple categories. """

    # No arguments: Link current category
    if len(args) == 0:
        await unlink_category(ctx, ctx.channel.category)
        return
    else:
        await ctx.send("Unlinking multiple categories has not been "
                       "implemented yet", delete_after=MSG_EXPIRY)

async def get_channel_lang(ctx, channel, require_valid=False):
    """ Returns the channel's language, given by its category.  """

    # Check that channel has a category
    category = channel.category
    if category == None:
        if require_valid:
            await ctx.send(f"Channel `{channel}` must be in a category.",
                           delete_after=MSG_EXPIRY)
        return None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check that category has a language set
    cur.execute("SELECT Lang from Category WHERE CategoryId = ?",
                (category.id,))
    row = cur.fetchone()
    conn.close()

    if row == None:
        if require_valid:
            await ctx.send(f"Category `{category}` for `{channel}` needs to "
                            "be assigned a language.", delete_after=MSG_EXPIRY)
        return None

    return row[0]


def get_channel_groups(channel):
    """ Returns the names of the groups a channel is in in a tuple. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT LangGroup FROM Channel WHERE ChannelId = ?",
                (channel.id,))
    rows = cur.fetchall()

    conn.close()

    return [row[0] for row in rows]

async def link_channel(ctx, channel, require_valid=False):
    """ Activates outgoing translations to all other channels in a channel's
    group.
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get the channel's language
    lang = await get_channel_lang(ctx, channel, require_valid)
    if lang == None:
        return

    # Find the channel's groups
    groups = get_channel_groups(channel)
    if len(groups) == 0:
        if require_valid:
            await ctx.send(f"Channel `{channel}` is not in any groups.",
                            delete_after=MSG_EXPIRY)
            return

    # For each group, get the other channels and translate to them
    for group in groups:
        cur.execute("""SELECT ChannelId FROM Channel 
                       WHERE (LangGroup = ? AND ChannelId != ?)""",
                    (group, channel.id))
        for target_channel_rows in cur:
            target_channel_id = target_channel_rows[0]

            # Get target channel's language
            target_lang = await get_channel_lang(
                                    ctx,
                                    bot.get_channel(target_channel_id),
                                    require_valid=True)
            if target_lang == None:
                await ctx.send("Stopping...", delete_after=MSG_EXPIRY)
                return

            await channel.send("!tr channel from {} to {} for <#{}>".format(
                                lang, target_lang, target_channel_id),
                                delete_after=MSG_EXPIRY)

    conn.commit()
    conn.close()

async def link_group(ctx, group):
    """ Links all channels in the group. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Links all channels in the group
    cur.execute("SELECT ChannelId FROM Channel WHERE LangGroup = ?", (group,))
    for row in cur:
        channel = bot.get_channel(row[0])
        await link_channel(ctx, channel, require_valid=True)

    conn.close()

async def link_category(ctx, category):
    """ Links all channels in the category. """

    # Link all channels in the category
    for channel in category.text_channels:
        await link_channel(ctx, channel, require_valid=True)
    
async def link_all(ctx):
    """ Links all linkable channels. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Link all channels in the channels table
    cur.execute("SELECT ChannelId FROM Channel")
    for row in cur:
        await link_channel(ctx, bot.get_channel(row[0]), require_valid=True)

    conn.close()

async def unlink_channel(ctx, channel):
    """ Unlinks the specified channel. """

    await channel.send("!tr stop for all", delete_after=MSG_EXPIRY)

async def unlink_group(ctx, group):
    """ Unlinks all channels in the group. """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Links all channels in the group
    cur.execute("SELECT ChannelId FROM Channel WHERE LangGroup = ?", (group,))
    for row in cur:
        channel = bot.get_channel(row[0])
        await unlink_channel(ctx, channel)

    conn.close()

async def unlink_category(ctx, category):
    """ Unlinks all channels in the category. """

    for channel in category.text_channels:
        await unlink_channel(ctx, channel)
    
async def unlink_all(ctx):
    """ Unlinks all channels in the server. """

    for channel in bot.get_all_channels():
        await unlink_channel(ctx, channel)

bot.run(TOKEN)
