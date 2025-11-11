import os
import sys
import math
import time
import asyncio
import logging
from .utils import STS
from database import db
from .test import CLIENT, start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message

logging.basicConfig(
    level=logging.INFO,
    format="⚡ %(asctime)s — %(levelname)s — %(message)s"
)

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
TEXT = Translation.TEXT

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    if temp.lock.get(user) and str(temp.lock.get(user)) == "True":
        return await message.answer("Please wait until previous task completed.", show_alert=True)
    sts = STS(frwd_id)
    if not sts.verify():
        await message.answer("Old session expired.", show_alert=True)
        return await message.message.delete()
    i = sts.get(full=True)
    if i.TO in temp.IS_FRWD_CHAT:
        return await message.answer("Target chat already processing.", show_alert=True)
    m = await msg_edit(message.message, "<b>Verifying...</b>")
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    if not _bot:
        return await msg_edit(m, "<code>Add a bot using /settings</code>", wait=True)
    try:
        client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:
        return await m.edit(str(e))
    await msg_edit(m, "<b>Processing...</b>")
    try:
        await client.get_messages(sts.get("FROM"), sts.get("limit"))
    except:
        await msg_edit(m, f"Source chat is private or not accessible.", retry_btn(frwd_id), True)
        return await stop(client, user)
    try:
        k = await client.send_message(i.TO, "Testing")
        await k.delete()
    except:
        await msg_edit(m, f"Bot must be admin in target chat.", retry_btn(frwd_id), True)
        return await stop(client, user)
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "<b>🚀 Forwarding Started</b>")
    sts.add(time=True)
    await msg_edit(m, "<b>Starting...</b>")
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    if locked:
        try:
            MSG = []
            pling = 0
            async for msg in client.iter_messages(
                client,
                chat_id=sts.get('FROM'),
                limit=int(sts.get('limit')),
                offset=int(sts.get('skip')) if sts.get('skip') else 0
            ):
                if await is_cancelled(client, user, m, sts):
                    return
                if pling % 20 == 0:
                    await edit(m, 'Forwarding', 10, sts)
                pling += 1
                sts.add('fetched')
                if msg.empty or msg.service:
                    sts.add('deleted')
                    continue
                if forward_tag:
                    MSG.append(msg.id)
                    notcompleted = len(MSG)
                    completed = sts.get('total') - sts.get('fetched')
                    if notcompleted >= 100 or completed <= 100:
                        await forward(client, MSG, m, sts, protect)
                        sts.add('total_files', notcompleted)
                        await asyncio.sleep(0.3)
                        MSG = []
                else:
                    new_caption = custom_caption(msg, caption)
                    details = {"msg_id": msg.id, "media": media(msg), "caption": new_caption, 'button': button, "protect": protect}
                    await copy(client, details, m, sts)
                    sts.add('total_files')
                    await asyncio.sleep(0.25)
        except Exception as e:
            await msg_edit(m, f'<b>Error:</b>\n<code>{e}</code>', wait=True)
            temp.IS_FRWD_CHAT.remove(sts.TO)
            return await stop(client, user)
        temp.IS_FRWD_CHAT.remove(sts.TO)
        await send(client, user, "<b>✅ Forwarding Completed</b>")
        await edit(m, 'Completed', "Completed", sts)
        await stop(client, user)

async def copy(bot, msg, m, sts):
    try:
        if msg.get("media") and msg.get("caption"):
            await bot.send_cached_media(
                chat_id=sts.get('TO'),
                file_id=msg.get("media"),
                caption=msg.get("caption"),
                reply_markup=msg.get('button'),
                protect_content=msg.get("protect"))
        else:
            await bot.copy_message(
                chat_id=sts.get('TO'),
                from_chat_id=sts.get('FROM'),
                caption=msg.get("caption"),
                message_id=msg.get("msg_id"),
                reply_markup=msg.get('button'),
                protect_content=msg.get("protect"))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await copy(bot, msg, m, sts)
    except Exception:
        sts.add('deleted')

async def forward(bot, msg, m, sts, protect):
    try:
        await bot.forward_messages(
            chat_id=sts.get('TO'),
            from_chat_id=sts.get('FROM'),
            protect_content=protect,
            message_ids=msg)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await forward(bot, msg, m, sts, protect)

PROGRESS = """
📊 Percentage : {0} %
📥 Fetched : {1}
📤 Forwarded : {2}
🗂 Remaining : {3}
🔧 Status : {4}
⏳ ETA : {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass

async def edit(msg, title, status, sts):
    i = sts.get(full=True)
    status = 'Forwarding' if status == 10 else status
    percentage = "{:.0f}".format(float(i.fetched) * 100 / float(i.total))
    button = [[InlineKeyboardButton(percentage + "%", f'fwrdstatus#{status}#0#{percentage}#{i.id}')]]
    await msg_edit(msg, TEXT.format(i.total, i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, i.filtered, status, percentage, title), InlineKeyboardMarkup(button))

async def is_cancelled(client, user, msg, sts):
    if temp.CANCEL.get(user) == True:
        temp.IS_FRWD_CHAT.remove(sts.TO)
        await edit(msg, "Cancelled", "Completed", sts)
        await send(client, user, "<b>❌ Forwarding Cancelled</b>")
        await stop(client, user)
        return True
    return False

async def stop(client, user):
    try:
        await client.stop()
    except:
        pass
    await db.rmve_frwd(user)
    temp.forwardings -= 1
    temp.lock[user] = False

async def send(bot, user, text):
    try:
        await bot.send_message(user, text=text)
    except:
        pass

def custom_caption(msg, caption):
    if msg.media:
        media = getattr(msg, msg.media.value, None)
        if media:
            file_name = getattr(media, 'file_name', '')
            file_size = getattr(media, 'file_size', '')
            fcaption = msg.caption.html if msg.caption else ''
            if caption:
                return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
            return fcaption
    return None

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def media(msg):
    if msg.media:
        media = getattr(msg, msg.media.value, None)
        if media:
            return getattr(media, 'file_id', None)
    return None

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('Retry', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True
    await m.answer("Cancelled", show_alert=True)

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if sts.verify():
        total = sts.get('total')
        skipped = sts.get('skip')
        fetched, forwarded = sts.get('fetched'), sts.get('total_files')
        remaining = total - forwarded - skipped
    else:
        fetched, forwarded, remaining, skipped = 0, 0, 0, 0
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, "Calculating"), show_alert=True)

@Client.on_message(filters.command("stop"))
async def stop_forwarding(bot, message):
    user_id = message.from_user.id
    if temp.lock.get(user_id):
        temp.lock[user_id] = False
        temp.CANCEL[user_id] = True
        await message.reply("Forwarding Stopped", quote=True)
    else:
        await message.reply("No Active Task", quote=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()

