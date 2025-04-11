import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
from flask import Flask
from threading import Thread

# --- keep_alive 定義 ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ---- 設定（あなた用に変更済） ----
YOUTUBE_API_KEY = "AIzaSyBekUF9RVE6QcIr3pdAT5NbD1pBFdU3TJo"
YOUTUBE_CHANNEL_ID = "UC74BUTz4cecF7QK3_SMF0Tw"
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # ReplitのSecretsに保存
DISCORD_CHANNEL_ID = 1355162915614887936  # 通知チャンネルのID
TARGET_SUBS = [600, 700, 800, 900, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
CHECK_INTERVAL = 60  # 秒
NOTIFIED_FILE = "notified.json"
# -----------------------------------

# 通知済み登録者数を読み込む
def load_notified_targets():
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE, "r") as f:
            return set(json.load(f))
    return set()

# 通知済みを保存
def save_notified_targets(notified):
    with open(NOTIFIED_FILE, "w") as f:
        json.dump(list(notified), f)

notified_targets = load_notified_targets()

# YouTubeの登録者数を取得
async def get_subscriber_count():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YOUTUBE_CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            stats = data["items"][0]["statistics"]
            return int(stats["subscriberCount"])

# 定期的に登録者数をチェック
async def check_subscriber_goal(client):
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    global notified_targets

    while not client.is_closed():
        try:
            sub_count = await get_subscriber_count()
            print(f"現在の登録者数: {sub_count}")
            for target in TARGET_SUBS:
                if sub_count >= target and str(target) not in notified_targets:
                    await channel.send(f"🎉 チャンネル登録者数が **{target}人** を突破しました！おめでとうございます！")
                    notified_targets.add(str(target))
                    save_notified_targets(notified_targets)
        except Exception as e:
            print(f"エラー: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

# Discord Botの設定
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ログイン完了: {bot.user}")
    bot.loop.create_task(check_subscriber_goal(bot))

@bot.command()
async def subs(ctx):
    """現在の登録者数を表示するコマンド"""
    try:
        sub_count = await get_subscriber_count()
        await ctx.send(f"現在の登録者数は **{sub_count}人** です。")
    except Exception as e:
        await ctx.send("登録者数の取得に失敗しました。エラー: " + str(e))

# Flaskサーバーを起動してBotを実行
keep_alive()
bot.run(DISCORD_BOT_TOKEN)
