import discord
import os
import re
from datetime import datetime, timezone, timedelta
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
ACCOUNT_AGE_DAYS = 30
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))

# Comma-separated Discord user IDs to skip all checks
WHITELIST_IDS = os.environ.get("WHITELIST_IDS", "")
WHITELIST = set(int(uid.strip()) for uid in WHITELIST_IDS.split(",") if uid.strip())

# Pattern: username ending in exactly 4 digits
SPAM_NAME_PATTERN = re.compile(r".*\d{4}$")

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    if WHITELIST:
        print(f"Whitelist loaded: {len(WHITELIST)} user(s)")

@client.event
async def on_member_join(member):
    # Never ban bots - they are added by admins
    if member.bot:
        return

    # Skip all checks for whitelisted users
    if member.id in WHITELIST:
        if LOG_CHANNEL_ID:
            channel = client.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"✅ **Whitelisted:** {member.name} ({member.id}) - skipped all checks"
                )
        return

    account_age = datetime.now(timezone.utc) - member.created_at
    is_new_account = account_age < timedelta(days=ACCOUNT_AGE_DAYS)
    has_spam_name = bool(SPAM_NAME_PATTERN.match(member.name))
    days_old = account_age.days

    # Ban if account is too new OR has spam name pattern
    if is_new_account or has_spam_name:
        if is_new_account and has_spam_name:
            reason = f"Account too new ({days_old} days) + spam name pattern"
        elif has_spam_name:
            reason = f"Spam name pattern detected (account {days_old} days old)"
        else:
            reason = f"Account too new: {days_old} days old (minimum: {ACCOUNT_AGE_DAYS})"

        try:
            await member.send(
                f"Your account has been flagged by our anti-spam system. "
                f"If you believe this is an error, please contact a server admin."
            )
        except:
            pass

        await member.ban(reason=reason)

        if LOG_CHANNEL_ID:
            channel = client.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"🚫 **Banned:** {member.name} ({member.id})\n"
                    f"**Reason:** {reason}\n"
                    f"**Created:** {member.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                )

client.run(os.environ["DISCORD_TOKEN"])
