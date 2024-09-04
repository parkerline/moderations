import disnake
from disnake.ext import commands
from settings.config import *
import time
import pymongo
import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(BOT["MONGO_URI"])
db = client.ecotest
staffdb = db.staff
verifydb = db.verify
mute = db.mute
bans = db.bans
ticketes = db.tickets
reporters = db.reports

reportsstructure = {
    "guild_id": None,
    "user_id": None,
    "member_id": None,
    "moderator_id": None,
    "date": None,
    "reason": None,
    "status": None, # wait, open, close
}

ticketstructure = {
    "guild_id": None,
    "user_id": None,
    "moderator_id": None,
    "date": None,
    "date_close": None,
    "status": None, # wait, open, close
}


bansstructure = {
    "guild_id": None,
    "user_id": None,
    "moderator_id": None,
    "date": None,
    "reason": None,
    "unban": None,
    "unmoderator_id": None,
}

mutestcrutre = {
    "guild_id": None,
    "user_id": None,
    "moderator_id": None,
    "date": None,
    "unmute_date": None,
    "type": None, # chat, voice
    "reason": None,
    "unmute": None,
    "unmoderator_id": None,
    "end": None,
}

verifystucture = {
    "guild_id": None,
    "moderator_id": None,
    "user_id": None,
    "gender": None,
    "date": None,
    "type": None, # verify, nedopusk
}

staffstructure = {
    "guild_id": None,
    "user_id": None,
    "profiles": {
        "warns": 0,
        "mutes": 0,
        "bans": 0,
        "reports": 0,
        "tickets": 0,
        "verify": 0,
        "unverify": 0,
        "points": 0,
    },
    "online": {
        "online_day": 0,
        "online_week": 0,
        "online": 0,
    },
}


async def stafferr():
    return staffstructure
