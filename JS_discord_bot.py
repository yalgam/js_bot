import discord
from discord.ext import commands, tasks
import datetime
import json

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

voice_log = {}
message_count = {}
is_check_week = False


@bot.event
async def on_ready():
    print(f"{bot.user} 봇이 로그인했습니다!")
    check_inactive_members.start()


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        voice_log[member.id] = datetime.datetime.now()


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.author.id not in message_count:
        message_count[message.author.id] = 0
    message_count[message.author.id] += 1
    await bot.process_commands(message)


def format_names_block(name_list):
    if not name_list:
        return "`(없음)`"
    names_str = ", ".join(name_list)
    return f"```\n{names_str}\n```"


@tasks.loop(time=datetime.time(hour=0, minute=0))
async def check_inactive_members():
    global voice_log,message_count,is_check_week
    now = datetime.datetime.now()
    if now.weekday() != 0:
        return
    if not is_check_week :
        is_check_week = True
        return
    
    await bot.wait_until_ready()
    for guild in bot.guilds:
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
            if member.id not in voice_log:
                all_inactive.append(member.display_name)
                if member.id not in message_count:
                    chat_0_10.append(member.display_name)
                else:
                    count = message_count[member.id]
                    if 1 <= count <= 10:
                        chat_0_10.append(member.display_name)
                    elif 11 <= count <= 50:
                        chat_11_50.append(member.display_name)
                    else:
                        chat_50_up.append(member.display_name)

        now = datetime.datetime.now()
        two_weeks_ago = now - datetime.timedelta(days=14)
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
        voice_log.clear()
        message_count.clear()
        is_check_week = False
    

@bot.command()
async def 잠수(ctx):
    if ctx.channel.name == "💾┊bot_백업":
        await ctx.send("봇 정상 작동 중입니다")
    

with open("./config.json") as f:
    config = json.load(f)

bot.run(config["token"])
