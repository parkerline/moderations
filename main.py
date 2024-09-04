import disnake
from disnake.ext import commands
from settings.config import *
import time
import pymongo
import asyncio
import os
import glob

bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all(), test_guilds=[BOT["GUILD_ID"]])
base_dir = os.path.dirname(os.path.abspath(__file__))


async def load_cogs(bot):
    for filename in glob.glob("client/**/*.py", recursive=True):
        if os.path.basename(filename).startswith("_"):
            continue
        extension = filename.replace("/", ".").replace("\\", ".").replace(".py", "")
        try:
            bot.load_extension(extension)
            print(f"Загружено расширение: {extension}")
        except commands.ExtensionFailed as e:
            print(f"Ошибка при загрузке расширения {extension}: {e.original}")
        except commands.ExtensionNotFound as e:
            print(f"Расширение не найдено: {extension}")
        except commands.NoEntryPointError as e:
            print(f"Не найдена точка входа в расширении: {extension}")
        except commands.ExtensionAlreadyLoaded as e:
            print(f"Расширение уже загружено: {extension}")
        except commands.ExtensionNotLoaded as e:
            print(f"Расширение не загружено: {extension}")
        except commands.ExtensionError as e:
            print(f"Ошибка в расширении: {extension}")


async def load_cogs1(bot):
    for filename in glob.glob("server/**/*.py", recursive=True):
        if os.path.basename(filename).startswith("_"):
            continue
        extension = filename.replace("/", ".").replace("\\", ".").replace(".py", "")
        try:
            bot.load_extension(extension)
            print(f"Загружено расширение: {extension}")
        except commands.ExtensionFailed as e:
            print(f"Ошибка при загрузке расширения {extension}: {e.original}")
        except commands.ExtensionNotFound as e:
            print(f"Расширение не найдено: {extension}")
        except commands.NoEntryPointError as e:
            print(f"Не найдена точка входа в расширении: {extension}")
        except commands.ExtensionAlreadyLoaded as e:
            print(f"Расширение уже загружено: {extension}")
        except commands.ExtensionNotLoaded as e:
            print(f"Расширение не загружено: {extension}")
        except commands.ExtensionError as e:
            print(f"Ошибка в расширении: {extension}")


@bot.event
async def on_ready():
    print(f"Бот {bot.user.name} успешно запущен и готов к работе!")
    guild = bot.get_guild(BOT["GUILD_ID"])
    await load_cogs1(bot)
    await load_cogs(bot)
    await assign_role_to_all(guild)  # Вызов новой функции при запуске бота
    
@bot.event
async def on_member_join(member):
    guild = bot.get_guild(BOT["GUILD_ID"])
    role = guild.get_role(1276296412249718814)
    await member.add_roles(role)
    
async def assign_role_to_all(guild):
    role = guild.get_role(1276296412249718814)
    for member in guild.members:
        if len(member.roles) == 1:  # Проверяем, есть ли у участника только роль @everyone
            await member.add_roles(role)
            print(f"Роль {role.name} успешно добавлена пользователю {member.name}")

bot.run(BOT["TOKEN"])
