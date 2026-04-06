import discord
import os
from datetime import datetime, timezone, timedelta
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
ACCOUNT_AGE_DAYS = 30
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))
WHITELISTED_BOTS = os.environ.get("WHITELISTED_BOTS", "").split(",")

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")

@client.event
async def on_member_join(member):
    # Never ban whitelisted bots
    if member.bot and str(member.id) in WHITELISTED_BOTS:
        return

    account_age = datetime.now(timezone.utc) - member.created_at
    
    if account_age < timedelta(days=ACCOUNT_AGE_DAYS):
        days_old = account_age.days
        
        # Try to DM the user before banning
        try:
            await member.send(
                f"Your Discord account is only {days_old} days old. "
                f"This server requires accounts to be at least {ACCOUNT_AGE_DAYS} days old. "
                f"Please try again later."
            )
        except:
            pass  # DMs might be disabled
        
        # Ban the user
        await member.ban(reason=f"Account too new: {days_old} days old (minimum: {ACCOUNT_AGE_DAYS})")
        
        # Log to channel
        if LOG_CHANNEL_ID:
            channel = client.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"🚫 **Banned:** {member.name} ({member.id})\n"
                    f"**Reason:** Account age {days_old} days (minimum: {ACCOUNT_AGE_DAYS})\n"
                    f"**Created:** {member.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
                )
client.run(os.environ["DISCORD_TOKEN"])
