import disnake
from disnake.ext import commands
import asyncio
from settings.config import *
from settings.cfg import *
from settings.db import *
from settings.funcdb import *
import time

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.unmute())
        self.bot.loop.create_task(self.check_mute_roles())
        self.bot.loop.create_task(self.checkbanroles())

    async def unmute(self):
        await self.bot.wait_until_ready()
        while True:
            guild = self.bot.get_guild(BOT["GUILD_ID"])
            chatmuterole = guild.get_role(CFG["chatmute_role"])
            voicemuterole = guild.get_role(CFG["voicemute_role"])
            current_time = time.time()

            async for mute_record in mute.find({"guild_id": guild.id, "end": False}):
                if mute_record["unmute_date"] <= current_time:
                    member = guild.get_member(mute_record["user_id"])
                    if member:
                        if mute_record["type"] == "chat" and chatmuterole in member.roles:
                            await member.remove_roles(chatmuterole)
                        elif mute_record["type"] == "voice" and voicemuterole in member.roles:
                            await member.remove_roles(voicemuterole)
                    
                    await mute.update_one(
                        {"_id": mute_record["_id"]},
                        {"$set": {"end": True}}
                    )

            await asyncio.sleep(5)

    async def check_mute_roles(self):
        await self.bot.wait_until_ready()
        while True:
            guild = self.bot.get_guild(BOT["GUILD_ID"])
            chatmuterole = guild.get_role(CFG["chatmute_role"])
            voicemuterole = guild.get_role(CFG["voicemute_role"])

            async for mute_record in mute.find({"guild_id": guild.id, "end": False}):
                member = guild.get_member(mute_record["user_id"])
                if member:
                    if mute_record["type"] == "chat" and chatmuterole not in member.roles:
                        await member.add_roles(chatmuterole)
                    elif mute_record["type"] == "voice" and voicemuterole not in member.roles:
                        await member.add_roles(voicemuterole)

            await asyncio.sleep(5)
            
    async def checkbanroles(self):
        await self.bot.wait_until_ready()
        print("Задача checkbanroles запущена")
        while True:
            guild = self.bot.get_guild(BOT["GUILD_ID"])
            if not guild:
                print("Гильдия не найдена в checkbanroles")
                await asyncio.sleep(15)
                continue

            banrole = guild.get_role(CFG["ban_role"])
            if not banrole:
                print("Роль бана не найдена")
                await asyncio.sleep(15)
                continue

            async for ban_record in bans.find({"guild_id": guild.id, "unban": False}):
                member = guild.get_member(ban_record["user_id"])
                if member:
                    print(f"Проверка пользователя {member.display_name}")
                    if banrole not in member.roles:
                        try:
                            await member.add_roles(banrole)
                            print(f"Роль бана добавлена пользователю {member.display_name}")
                        except disnake.Forbidden:
                            print(f"Не удалось добавить роль бана пользователю {member.display_name} из-за недостатка прав")
                        except Exception as e:
                            print(f"Произошла ошибка при добавлении роли бана пользователю {member.display_name}: {e}")
                else:
                    print(f"Пользователь с ID {ban_record['user_id']} не найден")

            await asyncio.sleep(1)

def setup(bot):
    bot.add_cog(Unmute(bot))