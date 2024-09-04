import disnake
import asyncio
import time
from disnake.ext import commands
from settings.config import *
from settings.funcdb import *
from settings.cfg import *

class CloseView(disnake.ui.View):
    def __init__(self, member, author, moderator, bot, msg):
        super().__init__()
        self.member = member
        self.author = author
        self.moderator = moderator
        self.bot = bot
        self.msg = msg
        
    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.moderator.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        return True
        
    @disnake.ui.button(label="Закрыть", style=disnake.ButtonStyle.red)
    async def close(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        moderatorole = interaction.guild.get_role(STAFF["Moderator"])
        if moderatorole not in interaction.author.roles:
            await interaction.response.send_message("У вас нет прав", ephemeral=True)
            return
        await reporters.update_one(
            {"guild_id": interaction.guild.id, "user_id": self.author.id, "member_id": self.member.id, "status": "open"},
            {"$set": {"status": "close", "moderator_id": interaction.author.id}},
        )
        await staffdb.update_one(
            {"guild_id": interaction.guild.id, "user_id": self.moderator.id},
            {"$inc": {"profiles.reports": 1, "profiles.points": 1}},
        )
        embed = self.msg.embeds[0]
        embed.add_field(name="Закрыл", value=interaction.author.mention)
        membed = disnake.Embed(
            title="Жалоба",
            description=f"Ваша жалоба на {self.member.mention} была закрыта модератором {interaction.author.mention}",
        )
        membed.set_thumbnail(url=self.member.display_avatar.url)
        membed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        logchannel = interaction.guild.get_channel(NEW["reportlogs"])
        lembed = disnake.Embed(
            title="Жалоба",
            description=f"Жалоба от {self.author.mention} на {self.member.mention} была закрыта модератором {interaction.author.mention}",
        )
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        await logchannel.send(embed=lembed)
        await self.author.send(embed=membed)
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Жалоба успешно закрыта", ephemeral=True)
        

class ReportView(disnake.ui.View):
    def __init__(self, author, member, bot, msg):
        super().__init__()
        self.author = author
        self.member = member
        self.bot = bot
        self.msg = msg
        
    @disnake.ui.button(label="Принять", style=disnake.ButtonStyle.green)
    async def accept(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        moderatorole = interaction.guild.get_role(STAFF["Moderator"])
        if moderatorole not in interaction.author.roles:
            await interaction.response.send_message("У вас нет прав", ephemeral=True)
            return
        await reporters.update_one(
            {"guild_id": interaction.guild.id, "user_id": self.author.id, "member_id": self.member.id, "status": "wait"},
            {"$set": {"status": "open", "moderator_id": interaction.author.id}},
        )
        embed = self.msg.embeds[0]
        embed.add_field(name="Принял", value=interaction.author.mention)
        membed = disnake.Embed(
            title="Жалоба",
            description=f"Ваша жалоба на {self.member.mention} была принята модератором {interaction.author.mention}",
        )
        membed.set_thumbnail(url=self.member.display_avatar.url)
        membed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        logchannel = interaction.guild.get_channel(NEW["reportlogs"])
        lembed = disnake.Embed(
            title="Жалоба",
            description=f"Жалоба от {self.author.mention} на {self.member.mention} была принята модератором {interaction.author.mention}",
        )
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        await logchannel.send(embed=lembed)
        await self.author.send(embed=membed)
        await self.msg.edit(embed=embed, view=CloseView(self.member, self.author, interaction.author, self.bot, self.msg))
        await interaction.response.send_message("Жалоба успешно принята", ephemeral=True)
        
    @disnake.ui.button(label="Отклонить", style=disnake.ButtonStyle.red)
    async def decline(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        moderatorole = interaction.guild.get_role(STAFF["Moderator"])
        if moderatorole not in interaction.author.roles:
            await interaction.response.send_message("У вас нет прав", ephemeral=True)
            return
        await reporters.update_one(
            {"guild_id": interaction.guild.id, "user_id": self.author.id, "member_id": self.member.id, "status": "wait"},
            {"$set": {"status": "close", "moderator_id": interaction.author.id}},
        )
        embed = self.msg.embeds[0]
        embed.add_field(name="Отклонил", value=interaction.author.mention)
        membed = disnake.Embed(
            title="Жалоба",
            description=f"Ваша жалоба на {self.member.mention} была отклонена модератором {interaction.author.mention}",
        )
        membed.set_thumbnail(url=self.member.display_avatar.url)
        membed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        logchannel = interaction.guild.get_channel(NEW["reportlogs"])
        lembed = disnake.Embed(
            title="Жалоба",
            description=f"Жалоба от {self.author.mention} на {self.member.mention} была отклонена модератором {interaction.author.mention}",
        )
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(name=interaction.author, icon_url=interaction.author.display_avatar.url)
        await logchannel.send(embed=lembed)
        await self.author.send(embed=membed)
        await self.msg.edit(embed=embed)
        await interaction.response.send_message("Жалоба успешно отклонена", ephemeral=True)
        

class Report(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.slash_command(name="report", description="Пожаловаться на пользователя")
    async def report(self, inter, member: disnake.Member, *, reason: str):
        if member == inter.author:
            await inter.response.send_message("Вы не можете пожаловаться на себя", ephemeral=True)
            return
        if member.bot:
            await inter.response.send_message("Вы не можете пожаловаться на бота", ephemeral=True)
            return
        report = await reporters.find_one({"guild_id": inter.guild.id, "user_id": member.id, "status": "wait"})
        if report:
            await inter.response.send_message("На этого пользователя уже есть жалоба", ephemeral=True)
            return
        await reporters.insert_one(
            {
                "guild_id": inter.guild.id,
                "user_id": inter.author.id,
                "member_id": member.id,
                "moderator_id": inter.author.id,
                "date": time.time(),
                "reason": reason,
                "status": "wait",
            }
        )
        embed = disnake.Embed(
            title="Жалоба",
            description=f"От: {inter.author.mention}\nНа: {member.mention}",
        )
        polstovatelvoice = (
            inter.guild.get_channel(member.voice.channel.id)
            if member.voice
            else None
        )
        embed.add_field(
            name="Голосовой канал",
            value=f"{polstovatelvoice.mention if polstovatelvoice else 'Не в голосовом канале'}",
            inline=False,
        )
        embed.add_field(name="Причина", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=inter.author, icon_url=inter.author.display_avatar.url)
        reportchannel = inter.guild.get_channel(NEW["reportchannel"])
        msg = await reportchannel.send(embed=embed)
        view = ReportView(inter.author, member, self.bot, msg)
        await msg.edit(view=view)
        await inter.response.send_message("Жалоба успешно отправлена", ephemeral=True)
        
def setup(bot):
    bot.add_cog(Report(bot))