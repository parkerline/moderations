import disnake
from disnake.ext import commands
from settings.config import *
import time
import pymongo
import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient

from settings.db import *


async def addstaff(guild_id: int, user_id: int):
    staff = await staffdb.find_one({"guild_id": guild_id, "user_id": user_id})
    if staff is None:
        await staffdb.insert_one(
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "profiles": staffstructure["profiles"],
                "online": staffstructure["online"],
            }
        )
        return True
    return False

async def addverify(guild_id: int, moderator_id: int, user_id: int, gender: str, type: str):
    verify = await verifydb.find_one({"guild_id": guild_id, "user_id": user_id})
    moderator = await staffdb.find_one({"guild_id": guild_id, "user_id": moderator_id})
    if moderator:
        await verifydb.insert_one(
            {
                "guild_id": guild_id,
                "moderator_id": moderator_id,
                "user_id": user_id,
                "gender": gender,
                "date": time.time(),
                "type": type,
            }
        )
        await staffdb.update_one(
            {"guild_id": guild_id, "user_id": moderator_id},
            {"$inc": {"profiles.verify": 1, "profiles.points": 1}},
        )
        return True
    return False

async def addunverify(guild_id: int, moderator_id: int, user_id: int, type: str):
    verify = await verifydb.find_one({"guild_id": guild_id, "user_id": user_id})
    moderator = await staffdb.find_one({"guild_id": guild_id, "user_id": moderator_id})
    if moderator:
        await verifydb.insert_one(
            {
                "guild_id": guild_id,
                "moderator_id": moderator_id,
                "user_id": user_id,
                "gender": None,
                "date": time.time(),
                "type": type,
            }
        )
        await staffdb.update_one(
            {"guild_id": guild_id, "user_id": moderator_id},
            {"$inc": {"profiles.unverify": 1, "profiles.points": 1}},
        )
        return True
    return False

async def addmute(guild_id: int, user_id: int, moderator_id: int, type: str, reason: str, unmute_date: int):
    moderator = await staffdb.find_one({"guild_id": guild_id, "user_id": moderator_id})
    if moderator:
        await mute.insert_one(
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "moderator_id": moderator_id,
                "date": time.time(),
                "unmute_date": unmute_date,
                "type": type,
                "reason": reason,
                "unmute": False,
                "unmoderator_id": None,
                "end": False,
            }
        )
        await staffdb.update_one(
            {"guild_id": guild_id, "user_id": moderator_id},
            {"$inc": {"profiles.mutes": 1, "profiles.points": 1}},
        )
        return True
    
    return False

async def addban(guild_id: int, user_id: int, moderator_id: int, reason: str):
    moderator = await staffdb.find_one({"guild_id": guild_id, "user_id": moderator_id})
    if moderator:
        await bans.insert_one(
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "moderator_id": moderator_id,
                "date": time.time(),
                "reason": reason,
                "unban": False,
                "unmoderator_id": None,
            }
        )
        await staffdb.update_one(
            {"guild_id": guild_id, "user_id": moderator_id},
            {"$inc": {"profiles.bans": 1, "profiles.points": 1}},
        )
        return True
    
    return False

async def createticket(guild_id: int, user_id: int):
    await ticketes.insert_one(
        {
            "guild_id": guild_id,
            "user_id": user_id,
            "moderator_id": None,
            "date": time.time(),
            "date_close": None,
            "status": "wait",
            "thread_id": None,
        }
    )
    return True

async def createreport(guild_id: int, user_id: int, member_id: int, reason: str):
    await reporters.insert_one(
        {
            "guild_id": guild_id,
            "user_id": user_id,
            "member_id": member_id,
            "moderator_id": None,
            "date": time.time(),
            "date_close": None,
            "reason": reason,
            "status": "wait",
        }
    )
    return True

async def checkreport(guild_id: int, user_id: int):
    report = await reporters.find_one({"guild_id": guild_id, "user_id": user_id, "status": {"$in": ["wait", "open"]}})
    if report:
        return True
    return False

async def checktimereport(guild_id: int, user_id: int):
    report = await reporters.find_one({"guild_id": guild_id, "user_id": user_id, "status": "close"})
    return report

async def checkticket(guild_id: int, user_id: int):
    ticket = await ticketes.find_one({"guild_id": guild_id, "user_id": user_id, "status": {"$in": ["wait", "open"]}})
    if ticket:
        return True
    return False

async def checktimeticket(guild_id: int, user_id: int):
    ticket = await ticketes.find_one({"guild_id": guild_id, "user_id": user_id, "status": "close"})
    return ticket
                
                