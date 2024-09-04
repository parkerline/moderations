import disnake
from disnake.ext import commands
import asyncio
from settings.config import *
from settings.cfg import *
from settings.db import *
from settings.funcdb import *

class OnlineTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.online())

    async def online(self):
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(1)
            await self.update_online_time()

    async def update_online_time(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if any(role.id in STAFF.values() for role in member.roles):
                    staff = await staffdb.find_one({"guild_id": guild.id, "user_id": member.id})
                    if not staff:
                        staff = staffstructure.copy()
                        staff["guild_id"] = guild.id
                        staff["user_id"] = member.id
                        await staffdb.insert_one(staff)

                    voice_state = member.voice
                    if voice_state and voice_state.channel:
                        if any(role.id == STAFF["Support"] for role in member.roles):
                            if voice_state.channel.id in ONLINE["SUPPORT_CHANNELS"]:
                                staff["online"]["online_day"] += 1
                                staff["online"]["online_week"] += 1
                                staff["online"]["online"] += 1
                        else:
                            staff["online"]["online_day"] += 1
                            staff["online"]["online_week"] += 1
                            staff["online"]["online"] += 1

                        await staffdb.update_one(
                            {"guild_id": guild.id, "user_id": member.id},
                            {"$set": staff}
                        )

def setup(bot):
    bot.add_cog(OnlineTasks(bot))