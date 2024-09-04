import disnake
import asyncio
import time
from disnake.ext import commands
from settings.config import *
from settings.funcdb import *
from settings.cfg import *

class ModalMute(disnake.ui.Modal):
    def __init__(self, author, member, msg, type):
        self.author = author
        self.member = member
        self.msg = msg
        self.type = type
        components = [
            disnake.ui.TextInput(
                label="Введите причину мута",
                custom_id="reason",
                placeholder="Правило 1.1",
                min_length=1,
                max_length=30,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Введите время в минутах",
                custom_id="time",
                placeholder="60",
                min_length=1,
                max_length=30,
                required=True,
            ),
        ]
        super().__init__(title="Выдача мута", components=components)
        
    async def callback(self, interaction: disnake.MessageInteraction):
        role_map = {
            "chat": CFG["chatmute_role"],
            "voice": CFG["voicemute_role"]
        }
        mute_role = interaction.guild.get_role(role_map.get(self.type))
        
        if not mute_role:
            await interaction.response.send_message("Неверный тип мута", ephemeral=True)
            return
        try:
            reason = interaction.text_values['reason']
            times = int(interaction.text_values['time'])
        except KeyError as e:
            await interaction.response.send_message(f"Введите {e.args[0]}", ephemeral=True)
            return
        except ValueError:
            await interaction.response.send_message("Время должно быть числом", ephemeral=True)
            return
        if times < 1:
            await interaction.response.send_message("Время должно быть больше 0", ephemeral=True)
            return
        await self.member.add_roles(mute_role)
        embed = disnake.Embed(
            title="Выдача мута",
            description=f"Пользователь {self.member.mention} успешно замучен",
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        modlogs = interaction.guild.get_channel(NEW["modlogs"])
        types = {
            "chat": "в чате",
            "voice": "голос"
        }
        typer = types.get(self.type)
        lembed = disnake.Embed(
            title="Выдача мута",
        )
        lembed.add_field(name=f"> Цель:", value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
        lembed.add_field(name=f"> Модератор:", value=f"{self.author.mention}\n`{self.author.id}`", inline=True)
        lembed.add_field(name="Причина и время наказания", value=f"```Причина: {reason}\nВремя: {times} минут```", inline=False)
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        await modlogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await self.member.send(embed=lembed)
        unmute_date = int(time.time() + times * 60)
        await addmute(interaction.guild.id, self.member.id, self.author.id, self.type, reason, unmute_date)
        await interaction.response.send_message("Пользователь успешно замучен", ephemeral=True)
        
class BanModal(disnake.ui.Modal):
    def __init__(self, author, member, msg):
        self.author = author
        self.member = member
        self.msg = msg
        components = [
            disnake.ui.TextInput(
                label="Введите причину бана",
                custom_id="reason",
                placeholder="Правило 1.1",
                min_length=1,
                max_length=30,
                required=True,
            ),
        ]
        super().__init__(title="Выдача бана", components=components)
        
    async def callback(self, interaction: disnake.MessageInteraction):
        banrole = interaction.guild.get_role(CFG["ban_role"])
        try:
            reason = interaction.text_values['reason']
        except KeyError as e:
            await interaction.response.send_message(f"Введите {e.args[0]}", ephemeral=True)
            return

        for role in self.member.roles:
            if role != interaction.guild.default_role:
                try:
                    await self.member.remove_roles(role)
                except disnake.Forbidden:
                    continue
        await asyncio.sleep(5)
        await self.member.add_roles(banrole)
        embed = disnake.Embed(
            title="Выдача бана",
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        modlogs = interaction.guild.get_channel(NEW["modlogs"])
        lembed = disnake.Embed(
            title="Выдача бана",
        )
        lembed.add_field(name=f"> Цель:", value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
        lembed.add_field(name=f"> Модератор:", value=f"{self.author.mention}\n`{self.author.id}`", inline=True)
        lembed.add_field(name="Причина", value=f"```{reason}```")
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        await self.member.send(embed=lembed)
        await modlogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await addban(interaction.guild.id, self.member.id, self.author.id, reason)
        await interaction.followup.send("Пользователь успешно забанен", ephemeral=True)
        
        

class MuteView(disnake.ui.View):
    def __init__(self, author, member, msg):
        super().__init__()
        self.author = author
        self.member = member
        self.msg = msg
    
    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        return True
    
    @disnake.ui.button(label="Чат", style=disnake.ButtonStyle.gray, custom_id="chatmute")
    async def chatmute(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        chatmuterole = interaction.guild.get_role(CFG["chatmute_role"])
        if chatmuterole in self.member.roles:
            await interaction.response.send_message("Пользователь уже замучен в чате", ephemeral=True)
            return
        modal = ModalMute(self.author, self.member, self.msg, "chat")
        await interaction.response.send_modal(modal)
        
    @disnake.ui.button(label="Голос", style=disnake.ButtonStyle.gray, custom_id="voicemute")
    async def voicemute(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        voicemuterole = interaction.guild.get_role(CFG["voicemute_role"])
        if voicemuterole in self.member.roles:
            await interaction.response.send_message("Пользователь уже замучен в голосе", ephemeral=True)
            return
        modal = ModalMute(self.author, self.member, self.msg, "voice")
        await interaction.response.send_modal(modal)

class GenderView(disnake.ui.View):
    def __init__(self, author, member, msg):
        super().__init__()
        self.author = author
        self.member = member
        self.msg = msg

    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Мужской", style=disnake.ButtonStyle.gray, custom_id="boyrole")
    async def boyrole(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        try:
            boyrole = interaction.guild.get_role(CFG["boy_role"])
            unverify_role = interaction.guild.get_role(CFG["unverify_role"])
            nedopusk_role = interaction.guild.get_role(CFG["nedopusk_role"])

            await self.member.add_roles(boyrole)

            if unverify_role in self.member.roles:
                await self.member.remove_roles(unverify_role)
            elif nedopusk_role in self.member.roles:
                await self.member.remove_roles(nedopusk_role)

            embed = disnake.Embed(
                title="Верификация",
                description=f"Пользователь {self.member.mention} успешно верифицирован как мужчина",
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)
            embed.set_author(
                name=self.author.display_name, icon_url=self.author.display_avatar.url
            )

            logsverify = interaction.guild.get_channel(NEW["logsverify"])
            lembed = disnake.Embed(
                title="Верификация",
                description=f"Модератор {self.author.mention} верифицировал пользователя {self.member.mention} как мужчину",
            )
            lembed.set_thumbnail(url=self.member.display_avatar.url)
            lembed.set_author(
                name=self.author.display_name, icon_url=self.author.display_avatar.url
            )
            await logsverify.send(embed=lembed)
            await self.msg.edit(embed=embed, view=None)
            await addverify(interaction.guild.id, self.author.id, self.member.id, "Мужской", "verify")
            await interaction.response.send_message("Пользователь успешно верифицирован как мужчина", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка: {str(e)}", ephemeral=True)

    @disnake.ui.button(label="Женский", style=disnake.ButtonStyle.gray, custom_id="girlrole")
    async def girlrole(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        try:
            girl_role = interaction.guild.get_role(CFG["girl_role"])
            unverify_role = interaction.guild.get_role(CFG["unverify_role"])
            nedopusk_role = interaction.guild.get_role(CFG["nedopusk_role"])
            await self.member.add_roles(girl_role)
            if unverify_role in self.member.roles:
                await self.member.remove_roles(unverify_role)
            elif nedopusk_role in self.member.roles:
                await self.member.remove_roles(nedopusk_role)
            embed = disnake.Embed(
                title="Верификация",
                description=f"Пользователь {self.member.mention} успешно верифицирован как женщина",
            )
            embed.set_thumbnail(url=self.member.display_avatar.url)
            embed.set_author(
                name=self.author.display_name, icon_url=self.author.display_avatar.url
            )

            logsverify = interaction.guild.get_channel(NEW["logsverify"])
            lembed = disnake.Embed(
                title="Верификация",
                description=f"Модератор {self.author.mention} верифицировал пользователя {self.member.mention} как женщину",
            )
            lembed.set_thumbnail(url=self.member.display_avatar.url)
            lembed.set_author(
                name=self.author.display_name, icon_url=self.author.display_avatar.url
            )
            await logsverify.send(embed=lembed)
            await self.msg.edit(embed=embed, view=None)
            await addverify(interaction.guild.id, self.author.id, self.member.id, "Женский", "verify")
            await interaction.response.send_message("Пользователь успешно верифицирован как женщина", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка: {str(e)}", ephemeral=True)
            
class UnMuteView(disnake.ui.View):
    def __init__(self, author, member, msg):
        super().__init__()
        self.author = author
        self.member = member
        self.msg = msg
        
    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False
        return True
    
    @disnake.ui.button(label="Чат", style=disnake.ButtonStyle.gray, custom_id="chatunmute")
    async def chatunmute(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        chatmuterole = interaction.guild.get_role(CFG["chatmute_role"])
        if chatmuterole not in self.member.roles:
            await interaction.response.send_message("Пользователь не замучен в чате", ephemeral=True)
            return
        mutedb = await mute.find_one({"guild_id": interaction.guild.id, "user_id": self.member.id, "type": "chat", "end": False})
        if not mutedb:
            await interaction.response.send_message("Не удалось найти мут пользователя", ephemeral=True)
            return
        await mute.update_one({"_id": mutedb["_id"]}, {"$set": {"unmute": True, "unmoderator_id": self.author.id, "end": True}})
        await self.member.remove_roles(chatmuterole)
        embed = disnake.Embed(
            title="Размут",
            description=f"Пользователь {self.member.mention} успешно размучен в чате",
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        modlogs = interaction.guild.get_channel(NEW["modlogs"])
        lembed = disnake.Embed(
            title="Размут",
        )
        lembed.add_field(name=f"> Цель:", value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
        lembed.add_field(name=f"> Модератор:", value=f"{self.author.mention}\n`{self.author.id}`", inline=True)
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        await self.member.send(embed=lembed)
        await modlogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Пользователь успешно размучен в чате", ephemeral=True)
        
    @disnake.ui.button(label="Голос", style=disnake.ButtonStyle.gray, custom_id="voiceunmute")
    async def voiceunmute(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        voicemuterole = interaction.guild.get_role(CFG["voicemute_role"])
        if voicemuterole not in self.member.roles:
            await interaction.response.send_message("Пользователь не замучен в голосе", ephemeral=True)
            return
        mutedb = await mute.find_one({"guild_id": interaction.guild.id, "user_id": self.member.id, "type": "voice", "unmute": False})
        if not mutedb:
            await interaction.response.send_message("Не удалось найти мут пользователя", ephemeral=True)
            return
        await mute.update_one({"_id": mutedb["_id"]}, {"$set": {"unmute": True, "unmoderator_id": self.author.id, "end": True}})
        await self.member.remove_roles(voicemuterole)
        embed = disnake.Embed(
            title="Размут",
        )
        lembed.add_field(name=f"> Цель:", value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
        lembed.add_field(name=f"> Модератор:", value=f"{self.author.mention}\n`{self.author.id}`", inline=True)
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        modlogs = interaction.guild.get_channel(NEW["modlogs"])
        lembed = disnake.Embed(
            title="Размут",
            description=f"Модератор {self.author.mention} размутил пользователя {self.member.mention} в голосе",
        )
        lembed.set_thumbnail(url=self.member.display_avatar.url)
        lembed.set_author(
            name=self.author.display_name, icon_url=self.author.display_avatar.url
        )
        await self.member.send(embed=lembed)
        await modlogs.send(embed=lembed)
        await self.msg.edit(embed=embed, view=None)
        await interaction.response.send_message("Пользователь успешно размучен в голосе", ephemeral=True)


class ActionsView(disnake.ui.View):
    def __init__(self, author, member, roles, msg):
        super().__init__()
        self.author = author
        self.member = member
        self.roles = roles
        self.msg = msg
        self.role_map = {
            "Moderator": ROLE["Moderator"],
            "Support": ROLE["Support"],
        }
        self.muterole = [
            member.guild.get_role(CFG["chatmute_role"]),
            member.guild.get_role(CFG["voicemute_role"])
        ]
        self.role_staff = member.guild.get_role(CFG["staff_role"])

        if self.role_map["Support"] in self.roles:
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Верификация", custom_id="verify"))
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Недопустить", custom_id="unverify"))
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Сменить гендер", custom_id="change_gender"))
        if self.role_map["Moderator"] in self.roles:
            if any(role in self.member.roles for role in self.muterole):
                self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Размутить", custom_id="unmute"))
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Выдать мут", custom_id="mute"))
            if self.member.guild.get_role(CFG["ban_role"]) not in self.member.roles:
                self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Выдать бан", custom_id="ban"))
            if self.member.guild.get_role(CFG["ban_role"]) in self.member.roles:
                self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, label="Разбанить", custom_id="unban"))
        

    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете взаимодействовать с этой кнопкой", ephemeral=True)
            return False

        try:
            if interaction.component.custom_id == "verify":
                userdb = await staffdb.find_one({"guild_id": interaction.guild.id, "user_id": self.author.id})
                unverify_role = interaction.guild.get_role(CFG["unverify_role"])
                nedopusk_role = interaction.guild.get_role(CFG["nedopusk_role"])
                if unverify_role not in self.member.roles and nedopusk_role not in self.member.roles:
                    await interaction.response.send_message("Он уже прошел верификацию", ephemeral=True)
                    return False
                if self.author.voice is None:
                    await interaction.response.send_message("Вы должны находиться в голосовом канале", ephemeral=True)
                    return False
                embed = disnake.Embed(
                    title="Верификация",
                    description=f"Выбирите пол пользователя {self.member.mention}",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                await interaction.response.defer()  # Отложенный ответ
                await self.msg.edit(embed=embed, view=GenderView(self.author, self.member, self.msg))

            if interaction.component.custom_id == "unverify":
                userdb = await staffdb.find_one({"guild_id": interaction.guild.id, "user_id": self.author.id})
                unverify_role = interaction.guild.get_role(CFG["unverify_role"])
                nedopusk_role = interaction.guild.get_role(CFG["nedopusk_role"])
                if unverify_role not in self.member.roles:
                    await interaction.response.send_message("Он уже прошел верификацию", ephemeral=True)
                    return False
                if nedopusk_role in self.member.roles:
                    await interaction.response.send_message("Он уже недопущен", ephemeral=True)
                    return False
                if self.author.voice is None:
                    await interaction.response.send_message("Вы должны находиться в голосовом канале", ephemeral=True)
                    return False
                await self.member.add_roles(nedopusk_role)
                await self.member.remove_roles(unverify_role)
                embed = disnake.Embed(
                    title="Недопуск",
                    description=f"Пользователь {self.member.mention} успешно недопущен",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                logsverify = interaction.guild.get_channel(NEW["logsverify"])
                lembed = disnake.Embed(
                    title="Недопуск",
                    description=f"Модератор {self.author.mention} недопустил пользователя {self.member.mention}",
                )
                lembed.set_thumbnail(url=self.member.display_avatar.url)
                lembed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                await logsverify.send(embed=lembed)
                await self.msg.edit(embed=embed, view=None)
                await addunverify(interaction.guild.id, self.author.id, self.member.id, "unverify")
                await interaction.response.send_message("Пользователь успешно недопущен", ephemeral=True)

            if interaction.component.custom_id == "change_gender":
                userdb = await staffdb.find_one({"guild_id": interaction.guild.id, "user_id": self.author.id})
                boy_role = interaction.guild.get_role(CFG["boy_role"])
                girl_role = interaction.guild.get_role(CFG["girl_role"])
                staff_role = interaction.guild.get_role(CFG["staff_role"])
                if staff_role in self.member.roles:
                    await interaction.response.send_message("Вы не можете сменить пол сотрудника", ephemeral=True)
                    return
                if boy_role in self.member.roles:
                    await self.member.remove_roles(boy_role)
                    await self.member.add_roles(girl_role)
                    gender_changed_to = "женский"
                elif girl_role in self.member.roles:
                    await self.member.remove_roles(girl_role)
                    await self.member.add_roles(boy_role)
                    gender_changed_to = "мужской"
                else:
                    await interaction.response.send_message("У пользователя нет роли для смены пола.", ephemeral=True)
                    return

                embed = disnake.Embed(
                    title="Смена пола",
                    description=f"Пользователю {self.member.mention} успешно сменен пол на {gender_changed_to}.",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )

                logsverify = interaction.guild.get_channel(NEW["logsverify"])
                lembed = disnake.Embed(
                    title="Смена пола",
                    description=f"Модератор {self.author.mention} сменил пол пользователя {self.member.mention} на {gender_changed_to}.",
                )
                lembed.set_thumbnail(url=self.member.display_avatar.url)
                lembed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                await logsverify.send(embed=lembed)
                await self.msg.edit(embed=embed, view=None)
                await interaction.response.send_message("Вы успешно сменили пол пользователя", ephemeral=True)
                
            if interaction.component.custom_id == "mute":
                chatmuterole = interaction.guild.get_role(CFG["chatmute_role"])
                voicemuterole = interaction.guild.get_role(CFG["voicemute_role"])

                if chatmuterole in self.member.roles and voicemuterole in self.member.roles:
                    await interaction.response.send_message("Пользователь уже замучен в чате и голосовом канале", ephemeral=True)
                    return
                embed = disnake.Embed(
                    title="Выдача мута",
                    description=f"Выберите режим мута для пользователя {self.member.mention}",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                await interaction.response.defer()  # Отложенный ответ
                await self.msg.edit(embed=embed, view=MuteView(self.author, self.member, self.msg))
                
            if interaction.component.custom_id == "ban":
                banrole = interaction.guild.get_role(CFG["ban_role"])
                if banrole in self.member.roles:
                    await interaction.response.send_message("Пользователь уже забанен", ephemeral=True)
                    return
                modal = BanModal(self.author, self.member, self.msg)
                await interaction.response.send_modal(modal)
                
            if interaction.component.custom_id == "unban":
                banrole = interaction.guild.get_role(CFG["ban_role"])
                if banrole not in self.member.roles:
                    await interaction.response.send_message("Пользователь не забанен", ephemeral=True)
                    return
                bandb = await bans.find_one({"guild_id": interaction.guild.id, "user_id": self.member.id, "unban": False})
                if not bandb:
                    await interaction.response.send_message("Не удалось найти бан пользователя", ephemeral=True)
                    return
                bans.update_one({"_id": bandb["_id"]}, {"$set": {"unban": True, "unmoderator_id": self.author.id}})
                await self.member.remove_roles(banrole)
                embed = disnake.Embed(
                    title="Разбан",
                    description=f"Пользователь {self.member.mention} успешно разбанен",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                modlogs = interaction.guild.get_channel(NEW["modlogs"])
                lembed = disnake.Embed(
                    title="Разбан",
                )
                lembed.add_field(name=f"> Цель:", value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
                lembed.add_field(name=f"> Модератор:", value=f"{self.author.mention}\n`{self.author.id}`", inline=True)
                lembed.set_thumbnail(url=self.member.display_avatar.url)
                lembed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                await modlogs.send(embed=lembed)
                await self.msg.edit(embed=embed, view=None)
                await interaction.response.send_message("Пользователь успешно разбанен", ephemeral=True)
                
            if interaction.component.custom_id == "unmute":
                chatmuterole = interaction.guild.get_role(CFG["chatmute_role"])
                voicemuterole = interaction.guild.get_role(CFG["voicemute_role"])
                if chatmuterole not in self.member.roles and voicemuterole not in self.member.roles:
                    await interaction.response.send_message("Пользователь не замучен", ephemeral=True)
                    return
                embed = disnake.Embed(
                    title="Размут",
                    description=f"Выберите режим размута для пользователя {self.member.mention}",
                )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                embed.set_author(
                    name=self.author.display_name, icon_url=self.author.display_avatar.url
                )
                await interaction.response.defer()
                await self.msg.edit(embed=embed, view=UnMuteView(self.author, self.member, self.msg))

        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка: {str(e)}", ephemeral=True)

        return True



class Action(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="action", description="Выполнить действие над пользователем"
    )
    async def action(
        self, inter: disnake.ApplicationCommandInteraction, пользователь: disnake.Member
    ):
        user = inter.author
        member = inter.guild.get_member(пользователь.id)
        userdb = await staffdb.find_one(
            {"guild_id": inter.guild.id, "user_id": user.id}
        )

        if userdb is None:
            await inter.response.send_message(
                "Вы не являетесь сотрудником", ephemeral=True
            )
            return

        dostuprole_ids = ROLE["Actions"]
        dostuprole = [inter.guild.get_role(role_id) for role_id in dostuprole_ids]

        user_roles = [role.id for role in user.roles]
        relevant_roles = [role for role in dostuprole if role.id in user_roles]

        if relevant_roles:
            embed = disnake.Embed(
                title="Выберите действие",
                description=f"Выберите действие, которое вы хотите выполнить над пользователем {member.mention}",
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_author(
                name=inter.author.display_name, icon_url=inter.author.display_avatar.url
            )
            await inter.response.send_message(embed=embed)
            msg = await inter.original_message()
            view = ActionsView(inter.author, member, user_roles, msg)
            await msg.edit(view=view)
            
        else:
            await inter.response.send_message(
                "У вас нет доступных ролей для выполнения этого действия",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(Action(bot))