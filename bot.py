import discord
from discord.ext import commands
from discord import ui
import urllib.request
import base64
import json
import os
import random
import hashlib
import time

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

webui_server_url = 'http://127.0.0.1:7860'

out_dir = 'api_out'
out_dir_t2i = os.path.join(out_dir, 'txt2img')
os.makedirs(out_dir_t2i, exist_ok=True)

def get_seed(string):
    a = string + str(time.time())
    return int(hashlib.md5(a.encode()).hexdigest(), 16) % 1000000

with open("json\\prompt.json", 'r') as f:
    prompt = json.load(f)
    p_prompt = prompt['positive_prompt']
    n_prompt = prompt['negative_prompt']

def encode_file_to_base64(path):    # i2i api
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')
    
def decode_and_save_base64(base64_str, save_path): 
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))


def call_txt2img_api(user_name, **payload):
    response = call_api('sdapi/v1/txt2img', **payload)
    if response == -1:
        return False
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_t2i, f'txt2img-{user_name}-{index}.png')
        decode_and_save_base64(image, save_path)
    return True

def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    try:
        request = urllib.request.Request(
            f'{webui_server_url}/{api_endpoint}',
            headers={'Content-Type': 'application/json'},
            data=data,
        )
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"fail to call: {e}")
        return -1

@bot.event
async def on_ready():
    with open("json\\token.json", 'r') as f:
        bot_name = json.load(f)['bot_name']
    print(f"{bot_name} is ready")
    await bot.tree.sync()

@bot.command(name='딸깍')
async def t2i(ctx, *arg):
    user_name = ctx.message.author.name # sender's name
    argument = ', '.join(arg)
    random.seed(get_seed(user_name))
    payload = {
        "prompt": p_prompt + argument,  # user prompt
        "negative_prompt": n_prompt,
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
        "sampler_name": "DPM++ 2M",
        "n_iter": 1,
        "batch_size": 1,
        "seed:": random.randint(0, 1000000)
    }
    #print(argument)
    msg = await ctx.reply("생성중...")
    if(not call_txt2img_api(user_name, **payload)):
        await msg.delete()
        await ctx.reply("생성에 실패하였습니다.")
        return
    with open(f'./api_out/txt2img/txt2img-{user_name}-0.png', 'rb') as f:
        picture = discord.File(f)
        await msg.delete()
        await ctx.reply(file=picture)
    os.remove(f'./api_out/txt2img/txt2img-{user_name}-0.png')


class prompt_modal(ui.Modal, title="프롬프트 입력기"):
    user_positive_prompt = ui.TextInput(
        label="positive prompt",
        style=discord.TextStyle.long,
        placeholder="positive prompt",
        default= p_prompt
    )
    user_negative_prompt = ui.TextInput(
        label="negative prompt",
        style=discord.TextStyle.long,
        placeholder="negative prompt",
        default= n_prompt
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_name = interaction.user.name
        random.seed(get_seed(user_name))
        payload = {
            "prompt": self.user_positive_prompt.value,  # user prompt
            "negative_prompt": self.user_negative_prompt.value,
            "steps": 20,
            "width": 512,
            "height": 512,
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M",
            "n_iter": 1,
            "batch_size": 1,
            "seed:": random.randint(0, 1000000)
        }
        print(payload)
        await interaction.response.defer()
        doing = await interaction.followup.send("생성중...")
        if(not call_txt2img_api(user_name, **payload)):
        #if False:
            await interaction.followup.edit_message(message_id=doing.id, content="생성에 실패하였습니다.")
            return
        with open(f'./api_out/txt2img/txt2img-{user_name}-0.png', 'rb') as f:
        #with open(f'./api_out/txt2img/test_kazusa.png', 'rb') as f:
            picture = discord.File(f)
            await doing.delete()
            await interaction.followup.send(file=picture)
        os.remove(f'./api_out/txt2img/txt2img-{user_name}-0.png')

@bot.tree.command(name='고급딸깍')
async def high_t2i(interaction: discord.Interaction):
    await interaction.response.send_modal(prompt_modal())


######### test functionn ###########
@bot.command(name='카즈사테스트딸깍')
async def t2i(ctx, *arg):
    argument = ', '.join(arg)
    payload = {
        "prompt": p_prompt + argument,  # user prompt
        "negative_prompt": n_prompt,
        "seed": 1,
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
        "sampler_name": "DPM++ 2M",
        "n_iter": 1,
        "batch_size": 1,
    }
    #user_name = ctx.message.author.name # sender's name
    print(argument)
    msg = await ctx.reply("생성중...")
    #call_txt2img_api(user_name, **payload)
    with open(f'./api_out/txt2img/test_kazusa.png', 'rb') as f:
        picture = discord.File(f)
        await msg.delete()
        await ctx.reply(file=picture)
    #os.remove(f'./api_out/txt2img/txt2img-{user_name}-0.png')  

with open("json\\token.json", 'r') as f:
    token = json.load(f)['api_token']
bot.run(token)
