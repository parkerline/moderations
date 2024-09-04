import disnake
import asyncio
import time
from disnake.ext import commands
from settings.config import *
from settings.funcdb import *
from settings.cfg import *

class NewView(disnake.ui.View):
    def __init__(self, member, author, bot):
        super().__init__()
        self.member = member
        self.author = author
        self.bot = bot
        
    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        return True
    
    @disnake.ui.button(label="Посмотреть онлайн", style=disnake.ButtonStyle.green)
    async def online(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        bk = await staffdb.find_one({"guild_id": interaction.guild.id, "user_id": self.member.id})
        online_day = bk["online"]["online_day"]
        online_week = bk["online"]["online_week"]
        online = bk["online"]["online"]
        
        # Форматирование времени для "Сегодня"
        hours_day = online_day // 3600
        minutes_day = (online_day % 3600) // 60
        
        # Форматирование времени для "Неделя"
        hours_week = online_week // 3600
        minutes_week = (online_week % 3600) // 60
        
        # Форматирование времени для "Всего"
        hours = online // 3600
        minutes = (online % 3600) // 60
        
        embed = disnake.Embed(
            title="Онлайн",
            description=f"**Сотрудник:** {self.member.mention}",
        )
        embed.add_field(name="Сегодня", value=f"```{hours_day}ч. {minutes_day}м.```", inline=False)
        embed.add_field(name="Неделя", value=f"```{hours_week}ч. {minutes_week}м.```", inline=False)
        embed.add_field(name="Всего", value=f"```{hours}ч. {minutes}м.```", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        

class Sprofile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.slash_command(name="sprofile", description="Посмотреть профиль сотрудника")
    async def sprofile(self, inter, пользователь: disnake.Member = None):
        member = пользователь or inter.author
        staff = await staffdb.find_one({"guild_id": inter.guild.id, "user_id": member.id})
        if not staff:
            await inter.response.send_message("Этот пользователь не является сотрудником", ephemeral=True)
            return
        
        embed = disnake.Embed(
            title="Профиль сотрудника",
            description=f"**Сотрудник:** {member.mention}\n",
        )
        staff_roles = [inter.guild.get_role(role_id).mention for role_name, role_id in STAFF.items() if inter.guild.get_role(role_id) in member.roles]
        if staff_roles:
            embed.description += f"\n**СТАФФ РОЛИ:** {', '.join(staff_roles)}"
        embed.add_field(name="Выговоры", value=f"```{staff['profiles']['warns']}```", inline=True)
        embed.add_field(name="Поинты", value=f"```{staff['profiles']['points']}```", inline=True)
        
        if any(role.id == STAFF["Moderator"] for role in member.roles):
            embed.add_field(name="Выдано мутов", value=f"```{staff['profiles']['mutes']}```", inline=False)
            embed.add_field(name="Выдано банов", value=f"```{staff['profiles']['bans']}```", inline=True)
            embed.add_field(name="Репорты", value=f"```{staff['profiles']['reports']}```", inline=True)
        
        if any(role.id == STAFF["Support"] for role in member.roles):
            embed.add_field(name="Верификации", value=f"```{staff['profiles']['verify']}```", inline=True)
            embed.add_field(name="Недопусков", value=f"```{staff['profiles']['unverify']}```", inline=True)
            embed.add_field(name="Тикеты", value=f"```{staff['profiles']['tickets']}```", inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=inter.author, icon_url=inter.author.display_avatar.url)
        
        view = NewView(member, inter.author, self.bot)
        await inter.response.send_message(embed=embed, view=view)
        
        
def setup(bot):
    bot.add_cog(Sprofile(bot))