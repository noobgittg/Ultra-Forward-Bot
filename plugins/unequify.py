import re, asyncio
from database import db
from config import temp
from .test import CLIENT , start_clone_bot
from translation import Translation
from pyrogram import Client, filters 
#from pyropatch.utils import unpack_new_file_id
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

DUPLICATE_TEXT = """
╔════❰ ᴜɴᴇǫᴜɪғʏ sᴛᴀᴛᴜs ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼ ғᴇᴛᴄʜᴇᴅ ᴍᴇᴅɪᴀs: {}
║┃
║┣⪼ ʀᴇᴍᴀɪɴɪɴɢ ᴍᴇᴅɪᴀs: {}
║┃
║┣⪼ ᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀs: {}
║┃
║┣⪼ ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴅᴇʟᴇᴛᴇᴅ: {} 
║╰━━━━━━━━━━━━━━━➣
╚════❰ {} ❱══❍⊱❁۪۪
"""

CLIENT = CLIENT()    
COMPLETED_BTN = InlineKeyboardMarkup(    
   [    
      [InlineKeyboardButton('💠ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ💠', url='https://t.me/mallumovieworldmain2')]    
   ]    
)    
    
CANCEL_BTN = InlineKeyboardMarkup([[InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')]])    
@Client.on_message(filters.command("unequify") & filters.private)    
async def unequify(client, message):    
   user_id = message.from_user.id    
   temp.CANCEL[user_id] = False    
   if temp.lock.get(user_id) and str(temp.lock.get(user_id))=="True":    
      return await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴜɴᴛɪʟʟ ᴘʀᴇᴠɪᴏᴜs ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇ</b>")    
   _bot = await db.get_bot(user_id)    
   if not _bot or _bot['is_bot']:    
      return await message.reply("<b>Need userbot to do this process. Please add a userbot using /settings</b>")    
   target = await client.ask(user_id, text="<b>Forward the last message from target chat or send last message link.<b>\n/cancel - `cancel this process`")    
   if target.text.startswith("/"):    
      return await message.reply("<b>process cancelled !**")    
   elif target.text:    
      regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")    
      match = regex.match(target.text.replace("?single", ""))    
      if not match:    
         return await message.reply('<b>Invalid link<b>')    
      chat_id = match.group(4)    
      last_msg_id = int(match.group(5))    
      if chat_id.isnumeric():    
         chat_id  = int(("-100" + chat_id))    
   elif target.forward_from_chat.type in ['channel', 'supergroup']:    
        last_msg_id = target.forward_from_message_id    
        chat_id = target.forward_from_chat.username or target.forward_from_chat.id    
   else:    
        return await message.reply_text("<b>invalid !<b>")    
   confirm = await client.ask(user_id, text="<b>send /yes to start the process and /no to cancel this process<b>")    
   if confirm.text.lower() == '/no':    
      return await confirm.reply("<b>process cancelled !<b>")    
   sts = await confirm.reply("<code>Processing...</code>")    
   try:    
      bot = await start_clone_bot(CLIENT.client(_bot))    
   except Exception as e:    
      return await sts.edit(e)    
   try:    
       k = await bot.send_message(chat_id, text="testing")    
       await k.delete()    
   except:    
       await sts.edit(f"<b>please make your [userbot](t.me/{_bot['username']}) admin in target chat with full permissions<b>")    
       return await bot.stop()    
   MESSAGES = []    
   DUPLICATE = []    
   total=checked=unsupported=deleted=0    
   temp.lock[user_id] = True    
   try:    
     await sts.edit(DUPLICATE_TEXT.format(0, 0, 0, 0, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)    
     async for message in bot.search_messages(chat_id=chat_id):    
        if temp.CANCEL.get(user_id) == True:    
           remaining = checked - deleted    
           await sts.edit(DUPLICATE_TEXT.format(checked, remaining, unsupported, deleted, "ᴄᴀɴᴄᴇʟʟᴇᴅ"), reply_markup=COMPLETED_BTN)    
           return await bot.stop()    
        total += 1    
        if message.document or message.video:    
           checked += 1    
           file = message.document or message.video    
           file_id = unpack_new_file_id(file.file_id)     
           if file_id in MESSAGES:    
              DUPLICATE.append(message.id)    
           else:    
              MESSAGES.append(file_id)    
           if len(DUPLICATE) >= 80:    
              await bot.delete_messages(chat_id, DUPLICATE)    
              deleted += 80    
              DUPLICATE = []    
        else:    
           unsupported += 1    
        if total % 80 == 0:    
           remaining = checked - deleted    
           await sts.edit(DUPLICATE_TEXT.format(checked, remaining, unsupported, deleted, "ᴘʀᴏɢʀᴇssɪɴɢ"), reply_markup=CANCEL_BTN)    
     if DUPLICATE:    
        await bot.delete_messages(chat_id, DUPLICATE)    
        deleted += len(DUPLICATE)    
   except Exception as e:    
       temp.lock[user_id] = False     
       await sts.edit(f"**ERROR**\n`{e}`")    
       return await bot.stop()    
   temp.lock[user_id] = False    
   remaining = checked - deleted    
   await sts.edit(DUPLICATE_TEXT.format(checked, remaining, unsupported, deleted, "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"), reply_markup=COMPLETED_BTN)    
   await bot.stop()    
