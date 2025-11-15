import re, asyncio
from database import db
from config import temp
from .test import CLIENT , start_clone_bot
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import struct
from pyrogram.file_id import FileId
import base64

DUPLICATE_TEXT = """
╔════❰ ᴜɴᴇǫᴜɪғʏ sᴛᴀᴛᴜs ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼ <b>ғᴇᴛᴄʜᴇᴅ ғɪʟᴇs:</b> <code>{}</code>
║┃
║┣⪼ <b>ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴅᴇʟᴇᴛᴇᴅ:</b> <code>{}</code> 
║╰━━━━━━━━━━━━━━━➣
╚════❰ {} ❱══❍⊱❁۪۪
"""

CLIENT = CLIENT()    
COMPLETED_BTN = InlineKeyboardMarkup(    
   [    
      [InlineKeyboardButton('💠ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ💠', url='https://t.me/mallumovieworldmain2')]    
   ]    
)    
    
CANCEL_BTN = InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', callback_data="close_btn")]])    

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")
   

def unpack_new_file_id(new_file_id):
    """Return file_id"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        struct.pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id

@Client.on_message(filters.command("unequify") & filters.private)    
async def unequify(client, message):    
   user_id = message.from_user.id    
   temp.CANCEL[user_id] = False    
   if temp.lock.get(user_id) and str(temp.lock.get(user_id))=="True":    
      return await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇ</b>")    
   _bot = await db.get_bot(user_id)    
   if not _bot or _bot['is_bot']:    
      return await message.reply("<b>Need Userbot To Do This Process. Please Add A Userbot Using /settings</b>")    
   target = await client.ask(user_id, text="<b>Forward The Last Message From Target Chat or Send Last Message Link.</b>\n/cancel - <code>Cancel This Process</code>")    
   if target.text.startswith("/"):    
      return await message.reply("<b>process cancelled !</b>")    
   elif target.text:    
      regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")    
      match = regex.match(target.text.replace("?single", ""))    
      if not match:    
         return await message.reply("<b>Invalid link</b>")    
      chat_id = match.group(4)    
      last_msg_id = int(match.group(5))    
      if chat_id.isnumeric():    
         chat_id  = int(("-100" + chat_id))    
   elif target.forward_from_chat.type in ['channel', 'supergroup']:    
        last_msg_id = target.forward_from_message_id    
        chat_id = target.forward_from_chat.username or target.forward_from_chat.id    
   else:    
        return await message.reply_text("<b>invalid !<b>")    
   confirm = await client.ask(user_id, text="<b>Send /yes To Start The Process & /no To Cancel This Process</b>")    
   if confirm.text.lower() == '/no':    
      return await confirm.reply("<b>Process Cancelled !</b>")    
   sts = await confirm.reply("<code>Processing...</code>")    
   try:    
      bot = await start_clone_bot(CLIENT.client(_bot))    
   except Exception as e:    
      return await sts.edit(e)    
   try:    
       k = await bot.send_message(chat_id, text="testing")    
       await k.delete()    
   except:    
       await sts.edit(f"<b>please make your [userbot](t.me/{_bot['username']}) admin in target chat with full permissions</b>")    
       return await bot.stop()    
   MESSAGES = []    
   DUPLICATE = []    
   total = 0
   deleted = 0
   temp.lock[user_id] = True    
   try:
     await sts.edit(DUPLICATE_TEXT.format(total, deleted, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)
     async for message in bot.search_messages(chat_id=chat_id, filter=enums.MessagesFilter.DOCUMENT):
        if temp.CANCEL.get(user_id) == True:
           await sts.edit(DUPLICATE_TEXT.format(total, deleted, "ᴄᴀɴᴄᴇʟʟᴇᴅ"), reply_markup=COMPLETED_BTN)
           return await bot.stop()
        file = message.document
        file_id = unpack_new_file_id(file.file_id) 
        if file_id in MESSAGES:
           DUPLICATE.append(message.id)
        else:
           MESSAGES.append(file_id)
        total += 1
        if total %1000 == 0:
           await sts.edit(DUPLICATE_TEXT.format(total, deleted, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)
        if len(DUPLICATE) >= 100:
           await bot.delete_messages(chat_id, DUPLICATE)
           deleted += 100
           await sts.edit(DUPLICATE_TEXT.format(total, deleted, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)
           DUPLICATE = []
     if DUPLICATE:
        await bot.delete_messages(chat_id, DUPLICATE)
        deleted += len(DUPLICATE)
   except Exception as e:
       temp.lock[user_id] = False 
       await sts.edit(f"**ERROR**\n`{e}`")
       return await bot.stop()
   temp.lock[user_id] = False
   await sts.edit(DUPLICATE_TEXT.format(total, deleted, "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"), reply_markup=COMPLETED_BTN)
   await bot.stop()
