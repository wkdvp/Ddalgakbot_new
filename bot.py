import discord
from discord.ext import commands
import urllib.request
import base64
import json
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

webui_server_url = 'http://127.0.0.1:7860'

out_dir = 'api_out'
out_dir_t2i = os.path.join(out_dir, 'txt2img')
os.makedirs(out_dir_t2i, exist_ok=True)

def encode_file_to_base64(path):    # i2i api
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')
    
def decode_and_save_base64(base64_str, save_path): 
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))


def call_txt2img_api(user_name, **payload):
    response = call_api('sdapi/v1/txt2img', **payload)
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_t2i, f'txt2img-{user_name}-{index}.png')
        decode_and_save_base64(image, save_path)

def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{webui_server_url}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data,
    )
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))

@bot.event
async def on_ready():
    print("Bot is ready")

@bot.command(name='딸깍')
async def t2i(ctx, *arg):
    argument = ', '.join(arg)
    payload = {
        "prompt": "masterpiece, (best quality:1.1)" + argument,  # user prompt
        "negative_prompt": "one hand with more than 5 fingers, one hand with less than 5 fingers,(worst quality, normal quality, low quality:1.4), lowres, blurry",
        "seed": 1,
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
        "sampler_name": "DPM++ 2M",
        "n_iter": 1,
        "batch_size": 1,
    }
    user_name = ctx.message.author.name # sender's name
    print(argument)
    call_txt2img_api(user_name, **payload)
    with open(f'./api_out/txt2img/txt2img-{user_name}-0.png', 'rb') as f:
        picture = discord.File(f)
        await ctx.reply(file=picture)
    os.remove(f'./api_out/txt2img/txt2img-{user_name}-0.png')

with open("json\\token.json", 'r') as f:
    token = json.load(f)['api_token']
bot.run(token)