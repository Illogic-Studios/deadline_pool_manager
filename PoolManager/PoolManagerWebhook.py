import json
import os
from discord import Webhook, Embed
import aiohttp
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
CONFIG_PATH = os.getenv('POOL_CONFIG_PATH', os.path.join(os.path.dirname(__file__), 'PoolManager', 'pool_distribution_config.json'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def get_embed_color(avg):
    if avg >= 50:
        return 0x2ecc40  # vert
    elif avg >= 10:
        return 0xffe135  # jaune
    else:
        return 0xff4136  # rouge

async def get_rates_embed():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    embed = Embed(title='Deadline Pool Manager', description='% de la farm attribué à chaque production :', color=0x3498db)
    for k, v in sorted(data.items(), key=lambda x: -x[1]):
        if v >= 50:
            emoji = '🟩'
        elif v >= 10:
            emoji = '🟨'
        else:
            emoji = '🟥'
        bar = '▓' * (v // 10) + '░' * (10 - (v // 10))
        embed.add_field(name=k, value=f"{emoji} {v}%\n{bar}", inline=True)
    return embed

async def send_or_edit_rates():
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        embed = await get_rates_embed()

        msg_id_path = os.path.join(os.path.dirname(__file__), 'webhook_msg_id.txt')
        msg_id = None
        if os.path.exists(msg_id_path):
            with open(msg_id_path, 'r') as f:
                msg_id = f.read().strip()

        if msg_id:
            try:
                await webhook.edit_message(int(msg_id), content=None, embed=embed)
            except Exception:
                sent = await webhook.send(embed=embed, username='PoolManager', wait=True)
                with open(msg_id_path, 'w') as f:
                    f.write(str(sent.id))
        else:
            sent = await webhook.send(embed=embed, username='PoolManager', wait=True)
            with open(msg_id_path, 'w') as f:
                f.write(str(sent.id))

if __name__ == '__main__':
    import asyncio
    asyncio.run(send_or_edit_rates())
