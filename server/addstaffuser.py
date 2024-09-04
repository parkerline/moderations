import disnake
from disnake.ext import commands
import asyncio
from settings.config import *
from settings.cfg import *
from settings.db import *
from settings.funcdb import *


class AddStaffUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.addstaff())
        self.bot.loop.create_task(self.check_staff_roles())
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Проверка, является ли автор сообщения ботом
        if message.author.bot:
            return
        
        guild = self.bot.get_guild(BOT["GUILD_ID"])
        chatmute_role = guild.get_role(CFG["chatmute_role"])
        if chatmute_role in message.author.roles:
            await message.delete()

    async def addstaff(self):
        await self.bot.wait_until_ready()
        while True:
            guild = self.bot.get_guild(BOT["GUILD_ID"])
            staff_role = guild.get_role(CFG["staff_role"])
            for member in guild.members:
                if staff_role in member.roles:
                    added = await addstaff(guild.id, member.id)
                    if added:
                        print(f"Добавлен новый сотрудник: {member}")
            await asyncio.sleep(5)

    async def check_staff_roles(self):
        await self.bot.wait_until_ready()
        while True:
            guild = self.bot.get_guild(BOT["GUILD_ID"])
            staff_role = guild.get_role(CFG["staff_role"])
            async for staff in staffdb.find({"guild_id": guild.id}):
                member = guild.get_member(staff["user_id"])
                if member and staff_role not in member.roles:
                    if staff["user_id"] not in self.removed_staff:
                        await staffdb.delete_one(
                            {"guild_id": guild.id, "user_id": staff["user_id"]}
                        )
                        print(f"Удален сотрудник: {member}")
                        self.removed_staff.add(staff["user_id"])  # Добавляем в множество
            await asyncio.sleep(5)

def setup(bot):
    bot.add_cog(AddStaffUser(bot))
