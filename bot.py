import discord
import os
from datetime import datetime, timezone, timedelta

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

ACCOUNT_AGE_DAYS = 30
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))

# Comma-separated Discord user IDs to skip account age check
# Add in Railway Variables tab, e.g. "123456789,987654321"
WHITELIST_IDS = os.environ.get("WHITELIST_IDS", "")
WHITELIST = set(int(uid.strip()) for uid in WHITELIST_IDS.split(",") if uid.strip())

# Banned keywords in usernames (comma-separated in env, case-insensitive)
# Add more in Railway Variables tab, e.g. "$dropee,free nitro,crypto airdrop"
BANNED_KEYWORDS = os.environ.get("BANNED_KEYWORDS", "$dropee")
BANNED_LIST = [kw.strip().lower() for kw in BANNED_KEYWORDS.split(",") if kw.strip()]


@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    if WHITELIST:
        print(f"Whitelist loaded: {len(WHITELIST)} user(s)")
    print(f"Banned keywords: {BANNED_LIST}")


@client.event
async def on_member_join(member):
    # Never ban bots - they are added by admins
    if member.bot:
        return

    # --- CHECK 1: Banned keywords in username/display name ---
    name_lower = member.name.lower()
    display_lower = (member.display_name or "").lower()
    for keyword in BANNED_LIST:
        if keyword in name_lower or keyword in display_lower:
            await member.ban(reason=f"Auto-ban: banned keyword '{keyword}' in name")
            if LOG_CHANNEL_ID:
                channel = client.get_channel(LOG_CHANNEL_ID)
                if channel:
                    await channel.send(
                        f"🚫 **Auto-Banned (keyword):** {member.name} ({member.id})\n"
                        f"**Matched:** `{keyword}`\n"
                        f"**Created:** {member.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                    )
            return

    # --- CHECK 2: Whitelisted users skip account age check ---
    if member.id in WHITELIST:
        if LOG_CHANNEL_ID:
            channel = client.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"✅ **Whitelisted:** {member.name} ({member.id}) - skipped account age check"
                )
        return

    # --- CHECK 3: Account age ---
    account_age = datetime.now(timezone.utc) - member.created_at

    if account_age < timedelta(days=ACCOUNT_AGE_DAYS):
        days_old = account_age.days

        try:
            await member.send(
                f"Your Discord account is only {days_old} days old. "
                f"This server requires accounts to be at least {ACCOUNT_AGE_DAYS} days old. "
                f"Please try again later."
            )
        except:
            pass

        await member.ban(reason=f"Account too new: {days_old} days old (minimum: {ACCOUNT_AGE_DAYS})")

        if LOG_CHANNEL_ID:
            channel = client.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"🚫 **Banned:** {member.name} ({member.id})\n"
                    f"**Reason:** Account age {days_old} days (minimum: {ACCOUNT_AGE_DAYS})\n"
                    f"**Created:** {member.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                )

client.run(os.environ["DISCORD_TOKEN"])
