import discord
from discord.ext import commands, tasks
import datetime
import json

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

voice_log = {}
message_count = {}


@bot.event
async def on_ready():
    print(f"{bot.user} 봇이 로그인했습니다!")
    check_inactive_members.start()


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        voice_log[member.id] = datetime.datetime.utcnow()


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    now = datetime.datetime.utcnow()
    two_weeks_ago = now - datetime.timedelta(days=14)
    if message.author.id not in message_count:
        message_count[message.author.id] = []
    message_count[message.author.id].append(now)
    message_count[message.author.id] = [
        t for t in message_count[message.author.id] if t > two_weeks_ago
    ]
    await bot.process_commands(message)


def format_names_block(name_list):
    if not name_list:
        return "`(없음)`"
    names_str = ", ".join(name_list)
    return f"```\n{names_str}\n```"


@tasks.loop(hours=24 * 14)
async def check_inactive_members():
    await bot.wait_until_ready()
    now = datetime.datetime.utcnow()
    two_weeks_ago = now - datetime.timedelta(days=14)
    guild = bot.guilds[0]
    channel = discord.utils.get(guild.text_channels, name="💾┊bot_백업")
    if channel is None:
        print("관리자 채널을 찾을 수 없습니다.")
        return

    chat_0_10 = []
    chat_11_50 = []
    chat_50_up = []
    all_inactive = []

    for member in guild.members:
        if member.bot:
            continue
        last_voice = voice_log.get(member.id)
        if last_voice is None or last_voice < two_weeks_ago:
            all_inactive.append(member.display_name)
            msgs = message_count.get(member.id, [])
            count = len(msgs)
            if count == 0 or (1 <= count <= 10):
                chat_0_10.append(member.display_name)
            elif 11 <= count <= 50:
                chat_11_50.append(member.display_name)
            else:
                chat_50_up.append(member.display_name)

    start_date = two_weeks_ago.strftime("%m월 %d일")
    end_date = now.strftime("%m월 %d일")

    total_inactive = len(all_inactive)

    if total_inactive == 0:
        msg = "**2주간 음성 채팅 미참여 멤버가 없습니다.**"
    else:
        msg = f"""## 📢 **[ {start_date} ~ {end_date} ]** 음성 채팅 미참여 멤버 목록
\u200b
**❌ 미참여 멤버 ({total_inactive}명)**  
{format_names_block(all_inactive)}

**💬 채팅 횟수별 분류**
\u200b
**[ 채팅 50회 이상 ({len(chat_50_up)}명) ]**  
{format_names_block(chat_50_up)}

**[ 채팅 11회 - 50회 ({len(chat_11_50)}명) ]**  
{format_names_block(chat_11_50)}

**[ 채팅 0회 - 10회 ({len(chat_0_10)}명) ]**  
{format_names_block(chat_0_10)}
"""

    await channel.send(msg)


@bot.command()
async def 잠수(ctx):
    if ctx.channel.name == "💾┊bot_백업":
        await ctx.send("봇 정상 작동 중입니다")


with open('./config.json') as f :
    config = json.load(f)

bot.run(config['token'])