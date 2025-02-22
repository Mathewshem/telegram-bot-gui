import streamlit as st
from telethon import TelegramClient
import asyncio
import json
import random

DB_FILE = "sent_users.json"
GROUP_HISTORY_FILE = "sent_groups.json"
PASSWORD = "Shem67"

# Load sent users and groups
def load_json(filename, default):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

sent_users = load_json(DB_FILE, {})
sent_groups = load_json(GROUP_HISTORY_FILE, [])

async def run_bot(api_id, api_hash, phone_number, message, media_caption, media_path, bot_name, group_name):
    client = TelegramClient('session_name', int(api_id), api_hash)
    await client.start(phone_number)

    dialogs = await client.get_dialogs()
    target_group = next((dialog for dialog in dialogs if dialog.is_group and (group_name.lower() in dialog.name.lower() or group_name == str(dialog.id))), None)

    if not target_group:
        st.error("Group not found!")
        return

    if group_name in sent_groups:
        st.warning(f"Already messaged {group_name}. Skipping.")
        return

    participants = await client.get_participants(target_group)
    batch_size = min(50, max(20, len(participants) // 15))
    tagged_message = f"[{bot_name}] {message}\n"
    count = 0
    batch_users = []

    for user in participants:
        username = getattr(user, 'username', None)
        if username and username not in sent_users:
            batch_users.append(f"@{username}")
            sent_users[username] = True
            count += 1

            if count % batch_size == 0:
                caption = media_caption if media_caption else " ".join(batch_users)
                if len(caption) > 1024:
                    caption = caption[:1020] + "..."

                if media_path:
                    await client.send_file(target_group.id, media_path, caption=caption)
                else:
                    await client.send_message(target_group.id, tagged_message + caption)

                st.success(f'Message sent to {target_group.name}')
                batch_users = []
                await asyncio.sleep(random.randint(90, 120))

    if batch_users:
        caption = media_caption if media_caption else " ".join(batch_users)
        if len(caption) > 1024:
            caption = caption[:1020] + "..."

        if media_path:
            await client.send_file(target_group.id, media_path, caption=caption)
        else:
            await client.send_message(target_group.id, tagged_message + caption)

        st.success(f'Message sent to {target_group.name}')
        await asyncio.sleep(random.randint(90, 120))

    sent_groups.append(group_name)
    save_json(DB_FILE, sent_users)
    save_json(GROUP_HISTORY_FILE, sent_groups)

    st.success("All messages sent successfully!")
    await client.disconnect()

# Streamlit UI
st.title("🚀 Telegram Channel Boost Bot by ShemTech")

api_id = st.text_input("API ID")
api_hash = st.text_input("API Hash")
phone_number = st.text_input("Phone Number")
message = st.text_area("Message to Send")
media_caption = st.text_area("Media Caption (Optional)")
media_path = st.file_uploader("Upload Media File (Optional)", type=["png", "jpg", "mp4", "pdf"])
bot_name = st.text_input("Bot Username")
group_name = st.text_input("Group/Channel Name or ID")
password = st.text_input("Bot Owner Code", type="password")

if st.button("Start Bot"):
    if password != PASSWORD:
        st.error("Invalid Code! Access Denied.")
    else:
        st.info("Starting bot...")
        asyncio.run(run_bot(api_id, api_hash, phone_number, message, media_caption, media_path, bot_name, group_name))
