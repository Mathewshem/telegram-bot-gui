import streamlit as st
import asyncio
import json
import random
from telethon import TelegramClient

# Store sent users to avoid duplicate messages
DB_FILE = "sent_users.json"


# Load previously sent users
def load_sent_users():
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {user: True for user in data}
    except FileNotFoundError:
        return {}


def save_sent_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)


sent_users = load_sent_users()

# Streamlit UI
st.markdown("""
    <h1 style='text-align: center; color: #0088cc;'>📢 TELEGRAM CHANNEL BOOST BOT BY SHEMTECH</h1>
""", unsafe_allow_html=True)

st.write("### Enter API Details")
api_id = st.text_input("API ID:")
api_hash = st.text_input("API Hash:")
phone_number = st.text_input("Phone Number:")
message = st.text_area("Message to Send:")
bot_name = st.text_input("Bot Username:")
password = st.text_input("Bot Owner Code:", type="password")
group_names = st.text_input("Group/Channel Names (comma-separated):")
media_path = st.file_uploader("Upload Media File (Optional)")
media_caption = st.text_input("Media Caption (Optional)")

PASSWORD = "Shem67"


def start_bot():
    if password != PASSWORD:
        st.error("Invalid Code! Access Denied.")
        return

    for group_name in group_names.split(","):
        group_name = group_name.strip()
        if group_name:
            asyncio.run(
                run_bot(api_id, api_hash, phone_number, message, media_path, media_caption, bot_name, group_name))

    st.success("Messages sent successfully!")


if st.button("Start Bot"):
    start_bot()


async def run_bot(api_id, api_hash, phone_number, message, media_path, media_caption, bot_name, group_name):
    client = TelegramClient('session_name', int(api_id), api_hash)
    await client.start(phone_number)

    dialogs = await client.get_dialogs()
    target_group = next((dialog for dialog in dialogs if dialog.is_group and (
                group_name.lower() in dialog.name.lower() or group_name == str(dialog.id))), None)

    if not target_group:
        st.error(f"Group '{group_name}' not found!")
        return

    participants = await client.get_participants(target_group)
    batch_size = min(200, max(30, len(participants) // 10))
    tagged_message = f"[{bot_name}] {message}\n"
    batch_users = []

    for count, user in enumerate(participants, 1):
        username = getattr(user, 'username', None)
        if username and username not in sent_users:
            batch_users.append(f"@{username}")
            sent_users[username] = True

            if count % batch_size == 0:
                await send_message(client, target_group, media_path, media_caption, tagged_message, batch_users)
                batch_users = []
                await asyncio.sleep(random.randint(90, 120))

    if batch_users:
        await send_message(client, target_group, media_path, media_caption, tagged_message, batch_users)
        await asyncio.sleep(random.randint(90, 120))

    save_sent_users(sent_users)
    await client.disconnect()


async def send_message(client, target_group, media_path, media_caption, tagged_message, batch_users):
    full_caption = f"{media_caption}\n{tagged_message} {' '.join(batch_users)}" if media_caption else f"{tagged_message} {' '.join(batch_users)}"
    full_caption = full_caption[:1020] + "..." if len(full_caption) > 1024 else full_caption

    if media_path:
        await client.send_file(target_group.id, media_path, caption=full_caption)
    else:
        await client.send_message(target_group.id, full_caption)
