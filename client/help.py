import disnake
import asyncio
import time
from disnake.ext import commands
from settings.config import *
from settings.funcdb import *
from settings.cfg import *

class CloseView(disnake.ui.View):
    def __init__(self, authorticket, helper, bot, msg):
        super().__init__(timeout=None)
        self.authorticket = authorticket
        self.helper = helper
        self.bot = bot
        self.msg = msg
        
    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.helper.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        return True
        
    @disnake.ui.button(label="Закрыть", style=disnake.ButtonStyle.red)
    async def close(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        guild = self.bot.get_guild(BOT["GUILD_ID"])
        ticketdb = await ticketes.find_one({"user_id": self.authorticket.id, "status": "open"})
        if ticketdb is None:
            return await interaction.response.send_message("Тикет не найден", ephemeral=True)
        await ticketes.update_one(
            {"user_id": self.authorticket.id, "status": "open"},
            {"$set": {"status": "close", "date_close": int(time.time())}},
        )
        await staffdb.update_one(
            {"guild_id": guild.id, "user_id": interaction.author.id},
            {"$inc": {"profiles.tickets": 1, "profiles.points": 1}},
        )
        membed = disnake.Embed(
            title="Тикет закрыт",
            description=f"Тикет закрыт модератором {interaction.author.mention}",
        )
        membed.set_thumbnail(url=interaction.author.avatar.url)
        membed.set_author(name=interaction.author, icon_url=interaction.author.avatar.url)
        await self.authorticket.send(embed=membed)
        embed = self.msg.embeds[0]
        embed.add_field(name="Закрыл", value=interaction.author.mention, inline=False)  # Исправлено на add_field
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Тикет закрыт", ephemeral=True)
    

class HelpView(disnake.ui.View):
    def __init__(self, authorticket, bot, msg):
        super().__init__(timeout=None)
        self.authorticket = authorticket
        self.bot = bot
        self.msg = msg
        
    @disnake.ui.button(label="Принять", style=disnake.ButtonStyle.green)
    async def accept(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        guild = self.bot.get_guild(BOT["GUILD_ID"])
        supportrole = guild.get_role(STAFF["Support"])
        if supportrole not in interaction.author.roles:
            return await interaction.response.send_message("Вы не являетесь саппортом", ephemeral=True)
        
        ticketdb = await ticketes.find_one({"user_id": self.authorticket.id, "status": "wait"})
        if ticketdb is None:
            return await interaction.response.send_message("Тикет не найден", ephemeral=True)
        
        channel = self.msg.channel
        thread = await channel.create_thread(name=f"Тикет {self.authorticket.name}", message=self.msg, auto_archive_duration=1440)
        
        await ticketes.update_one(
            {"user_id": self.authorticket.id, "status": "wait"},
            {"$set": {
                "status": "open",
                "moderator_id": interaction.author.id,
                "thread_id": thread.id,
            }},
        )
        
        membed = disnake.Embed(
            title="Тикет принят",
            description=f"Тикет принят модератором {interaction.author.mention}",
        )
        membed.set_thumbnail(url=interaction.author.avatar.url)
        membed.set_author(name=interaction.author, icon_url=interaction.author.avatar.url)
        ticketlogs = self.bot.get_channel(NEW["ticketlogs"])
        lembed = disnake.Embed(
            title="Тикет принят",
            description=f"Саппорт {interaction.author.mention} принял тикет от {self.authorticket.mention}",
        )
        lembed.set_thumbnail(url=self.authorticket.display_avatar.url)
        lembed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        await self.authorticket.send(embed=membed)
        
        embed = self.msg.embeds[0]
        embed.add_field(name="Принял", value=interaction.author.mention, inline=False)
        view = CloseView(self.authorticket, interaction.author, self.bot, self.msg)
        await ticketlogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=view)
        
        await interaction.response.send_message("Тикет принят", ephemeral=True)
        
    @disnake.ui.button(label="Отклонить", style=disnake.ButtonStyle.red)
    async def decline(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        guild = self.bot.get_guild(BOT["GUILD_ID"])
        supportrole = guild.get_role(STAFF["Support"])
        if supportrole not in interaction.author.roles:
            return await interaction.response.send_message("Вы не являетесь саппортом", ephemeral=True)
        ticketdb = await ticketes.find_one({"user_id": self.authorticket.id, "status": "wait"})
        if ticketdb is None:
            return await interaction.response.send_message("Тикет не найден", ephemeral=True)
        await ticketes.update_one(
            {"user_id": self.authorticket.id, "status": "wait"},
            {"$set": {"status": "close", "date_close": int(time.time())}},
        )
        membed = disnake.Embed(
            title="Тикет отклонен",
            description=f"Тикет отклонен модератором {interaction.author.mention}",
        )
        membed.set_thumbnail(url=interaction.author.avatar.url)
        membed.set_author(name=interaction.author, icon_url=interaction.author.avatar.url)
        ticketlgos = self.bot.get_channel(NEW["ticketlogs"])
        lembed = disnake.Embed(
            title="Тикет отклонен",
            description=f"Саппорт {interaction.author.mention} отклонил тикет от {self.authorticket.mention}",
        )
        lembed.set_thumbnail(url=self.authorticket.display_avatar.url)
        lembed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        await self.authorticket.send(embed=membed)
        embed = self.msg.embeds[0]
        embed.add_field(name="Отклонил", value=interaction.author.mention, inline=False)
        await ticketlgos.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Тикет отклонен", ephemeral=True)
        


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.slash_command(name="help", description="Помощь по командам")
    async def help(self, inter, проблема: str):
        if await checkticket(inter.guild.id, inter.author.id):
            return await inter.response.send_message("У вас есть открытый тикет, пожалуйста закройте его", ephemeral=True)
        if lasthelp := await checktimeticket(inter.guild.id, inter.author.id):
            if lasthelp['date'] + 300 > int(time.time()):
                date = lasthelp['date'] + 300
                await inter.response.send_message(f"Подождите и попробуйте <t:{int(date)}:R>", ephemeral=True)
                return
        if len(проблема) < 10:
            return await inter.response.send_message("Проблема должна быть больше 10 символов", ephemeral=True)
        await createticket(inter.guild.id, inter.author.id)
        embed = disnake.Embed(
            title="Новый тикет",
            description=f"Пользователь {inter.author.mention} создал тикет, проблема: {проблема}",
        )
        embed.set_thumbnail(url=inter.author.display_avatar.url)
        embed.set_author(name=inter.author, icon_url=inter.author.display_avatar.url)
        ticketchannel = self.bot.get_channel(NEW["ticketchannel"])
        msg = await ticketchannel.send(embed=embed)
        view = HelpView(inter.author, self.bot, msg)
        await msg.edit(view=view)
        await inter.response.send_message("Тикет создан, ожидайте ответа", ephemeral=True)
        
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        
        if isinstance(message.channel, disnake.Thread):
            help = await ticketes.find_one(
                {"thread_id": message.channel.id, "status": "open"}
            )
            if help and message.author.id == help["moderator_id"]:
                user = self.bot.get_user(help["user_id"])
                if user:
                    embed = disnake.Embed(
                        title="Ответ на вашу заявку на помощь",
                        description=message.content,
                    )
                    embed.set_author(
                        name=message.author, icon_url=message.author.avatar.url
                    )
                    embed.set_thumbnail(url=message.author.avatar.url)
                    embedo = disnake.Embed(
                        title="Вы отправили ответ", description=message.content
                    )
                    embedo.set_author(
                        name=message.author, icon_url=message.author.avatar.url
                    )
                    await message.channel.send(embed=embedo)
                    await user.send(embed=embed)
                    
        elif isinstance(message.channel, disnake.DMChannel):
            help = await ticketes.find_one(
                {"user_id": message.author.id, "status": "open"}
            )
            user = self.bot.get_user(help["user_id"])
            if help:
                thread = self.bot.get_channel(help["thread_id"])
                if thread:
                    embed = disnake.Embed(
                        title="Ответ на вашу заявку на помощь",
                        description=message.content,
                    )
                    embed.set_author(
                        name=message.author, icon_url=message.author.avatar.url
                    )
                    embed.set_thumbnail(url=message.author.avatar.url)
                    embedo = disnake.Embed(
                        title="Вы отправили ответ", description=message.content
                    )
                    embedo.set_author(
                        name=message.author, icon_url=message.author.avatar.url
                    )
                    await user.send(embed=embedo)
                    await thread.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Help(bot))
        