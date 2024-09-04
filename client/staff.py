import disnake
import asyncio
import time
from disnake.ext import commands
from settings.config import *
from settings.funcdb import *
from settings.cfg import *

class WarnModal(disnake.ui.Modal):
    def __init__(self, author, member, bot, msg):
        self.author = author
        self.member = member
        self.bot = bot
        self.msg = msg
        components = [
            disnake.ui.TextInput(
                label="Введите причину выговора",
                custom_id="reason",
                placeholder="Правило 1.1",
                min_length=1,
                max_length=30,
                required=True,
            ),
        ]
        super().__init__(title="Выдача выговора", components=components)
        
    async def callback(self, interaction: disnake.MessageInteraction):
        try:
            reason = interaction.text_values['reason']
        except KeyError:
            await interaction.response.send_message("Причина не была указана", ephemeral=True)
            return
        memberdb = await staffdb.find_one({"user_id": self.member.id})
        if not memberdb:
            await interaction.response.send_message("Пользователь не найден в базе данных", ephemeral=True)
            return
        await staffdb.update_one({"user_id": self.member.id}, {"$inc": {"profiles.warns": 1}})
        embed = disnake.Embed(
            title="Выговор",
            description=f"Пользователю {self.member.mention} был выдан выговор по причине {reason}",
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
        givelogs = interaction.guild.get_channel(NEW["givelogs"])
        lembed = disnake.Embed(
            title=embed.title,
            description=embed.description,
        )
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
        await givelogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message(embed.title, ephemeral=True)


class CuratorPanel(disnake.ui.View):
    def __init__(self, author, member, bot, msg):
        super().__init__(timeout=None)
        self.author = author
        self.member = member
        self.bot = bot
        self.msg = msg
        self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Выдать выговор", custom_id="warn"))
        
        # Проверка на наличие выговоров у self.member
        self.bot.loop.create_task(self.check_warns())

    async def check_warns(self):
        member_data = await staffdb.find_one({"guild_id": self.member.guild.id, "user_id": self.member.id})
        if member_data and member_data.get("profiles", {}).get("warns", 0) > 0:
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.red, label="Снять выговор", custom_id="unwarn"))
            await self.msg.edit(view=self)

    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        
        if interaction.component.custom_id == "warn":
            modal = WarnModal(self.author, self.member, self.bot, self.msg)
            await interaction.response.send_modal(modal)
        if interaction.component.custom_id == "unwarn":
            member_data = await staffdb.find_one({"guild_id": self.member.guild.id, "user_id": self.member.id})
            if member_data and member_data.get("profiles", {}).get("warns", 0) > 0:
                await staffdb.update_one({"guild_id": self.member.guild.id, "user_id": self.member.id}, {"$inc": {"profiles.warns": -1}})
                embed = disnake.Embed(
                    title="Снятие выговора",
                    description=f"У пользователя {self.member.mention} был снят выговор",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
                givelogs = interaction.guild.get_channel(NEW["givelogs"])
                lembed = disnake.Embed(
                    title=embed.title,
                    description=embed.description,
                )
                lembed.set_thumbnail(url=self.member.display_avatar.url)
                lembed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
                await givelogs.send(embed=lembed)
                await self.msg.edit(embed=embed, view=None)
                await interaction.response.send_message(embed.title, ephemeral=True)
            
        return True

class SelectRole(disnake.ui.Select):
    def __init__(self, author, member, msg, bot, action):
        self.author = author
        self.member = member
        self.msg = msg
        self.bot = bot
        self.action = action
        options = []

        for role_name, role_id in OTVETS.items():
            if role_id in [role.id for role in self.author.roles]:
                options.append(disnake.SelectOption(label=f"STAFF {role_name.capitalize()}", value=STAFF[role_name]))

        if not (1 <= len(options) <= 25):
            raise ValueError("Количество опций в селекте должно быть от 1 до 25")

        super().__init__(placeholder="Выберите роль", options=options)
    
    async def callback(self, interaction: disnake.MessageInteraction):
        role = interaction.guild.get_role(int(self.values[0]))
        staffrole = interaction.guild.get_role(CFG["staff_role"])
        
        if self.action == "add":
            if role in self.member.roles:
                await interaction.response.send_message("Пользователь уже имеет эту роль", ephemeral=True)
                return
            if interaction.user.id != self.author.id:
                await interaction.response.send_message("Вы не можете взаимодействовать с этим меню", ephemeral=True)
                return
            await self.member.add_roles(role)
            staff_roles = [r for r in self.member.roles if r.id in STAFF.values()]
            if len(staff_roles) == 1:
                await self.member.add_roles(staffrole)
            await addstaff(interaction.guild.id, self.member.id)
            embed = disnake.Embed(
                title="Поставить на ветку",
                description=f"Пользователь {self.member.mention} поставлен на роль {role.mention}",
            )
        elif self.action == "remove":
            if role not in self.member.roles:
                await interaction.response.send_message("Пользователь не имеет эту роль", ephemeral=True)
                return
            if interaction.user.id != self.author.id:
                await interaction.response.send_message("Вы не можете взаимодействовать с этим меню", ephemeral=True)
                return
            await self.member.remove_roles(role)
            staff_roles = [r for r in self.member.roles if r.id in STAFF.values()]
            if len(staff_roles) == 0:
                await self.member.remove_roles(staffrole)
            embed = disnake.Embed(
                title="Убрать с ветки",
                description=f"Пользователь {self.member.mention} убран с роли {role.mention}",
            )
        
        
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
        givelogs = interaction.guild.get_channel(NEW["givelogs"])
        lembed = disnake.Embed(
            title=embed.title,
            description=embed.description,
        )
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
        await givelogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message(embed.title, ephemeral=True)

class StaffView(disnake.ui.View):
    def __init__(self, author, member, bot, msg):
        super().__init__(timeout=None)
        self.author = author
        self.member = member
        self.bot = bot
        self.msg = msg
        self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Поставить на ветку", custom_id="addstaff"))
        self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.red, label="Убрать с ветки", custom_id="removestaff"))
        
        if ROLE["Curator"] in [role.id for role in self.author.roles]:
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.grey, label="Панель куратора", custom_id="curatorpanel"))
        
    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        
        if interaction.component.custom_id == "addstaff":
            embed = disnake.Embed(
                title="Поставить на ветку",
                description=f"Выберите роль, на которую хотите поставить пользователя {self.member.mention}",
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)
            embed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
            view = disnake.ui.View()
            select = SelectRole(self.author, self.member, self.msg, self.bot, action="add")
            view.add_item(select)
            await interaction.response.defer()
            await self.msg.edit(embed=embed, view=view)
            
        if interaction.component.custom_id == "removestaff":
            embed = disnake.Embed(
                title="Убрать с ветки",
                description=f"Выберите роль, с которой хотите убрать пользователя {self.member.mention}",
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)
            embed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
            view = disnake.ui.View()
            select = SelectRole(self.author, self.member, self.msg, self.bot, action="remove")
            view.add_item(select)
            await interaction.response.defer()
            await self.msg.edit(embed=embed, view=view)
            
        if interaction.component.custom_id == "curatorpanel":
            curator_role = interaction.guild.get_role(ROLE["Curator"])
            admin_role = interaction.guild.get_role(ROLE["Admin"])
            
            if curator_role in self.member.roles or admin_role in self.member.roles:
                await interaction.response.send_message("Вы не можете взаимодействовать с ним", ephemeral=True)
                return
            author_roles = [role.id for role in self.author.roles]
            member_roles = [role.id for role in self.member.roles]
            
            can_interact = False
            for role_name, otvet_role_id in OTVETS.items():
                staff_role_id = STAFF.get(role_name)
                if otvet_role_id in author_roles and staff_role_id in member_roles:
                    can_interact = True
                    break
            
            if not can_interact:
                await interaction.response.send_message("Вы не можете взаимодействовать с ним", ephemeral=True)
                return
            embed = disnake.Embed(
                title="Панель",
                description=f"Выбирите действие, которое хотите выполнить с пользователем {self.member.mention}",
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)
            embed.set_author(name=self.member, icon_url=self.member.display_avatar.url)
            view = CuratorPanel(self.author, self.member, self.bot, self.msg)
            await interaction.response.defer()
            await self.msg.edit(embed=embed, view=view)
            
            
        return True

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.slash_command(name="staff", description="Выбирите действие")
    async def staff(self, inter: disnake.ApplicationCommandInteraction, пользователь: disnake.User):
        staff_role = inter.guild.get_role(CFG["staff_role"])
        member = inter.guild.get_member(пользователь.id)
        if inter.author.id == пользователь.id:
            await inter.response.send_message("Вы не можете использовать эту команду на себе", ephemeral=True)
            return
        staffcommand_roles = [inter.guild.get_role(role_id) for role_id in ROLE["Staffcommand"]]
        if not any(role in inter.author.roles for role in staffcommand_roles):
            await inter.response.send_message("У вас нет прав на использование этой команды", ephemeral=True)
            return
        embed = disnake.Embed(title="Выбирите действие", description=f"Выбирите действие, которое хотите выполнить с пользователем {пользователь.mention}")
        embed.set_thumbnail(url=пользователь.display_avatar.url)
        embed.set_author(name=пользователь, icon_url=пользователь.display_avatar.url)
        await inter.response.send_message(embed=embed)
        msg = await inter.original_message()
        view = StaffView(inter.author, member, self.bot, msg)
        await msg.edit(view=view)
        
        
        
def setup(bot):
    bot.add_cog(Staff(bot))