import gradio as gr
import base64
from PIL import Image
from io import BytesIO
import nextcord
from nextcord.ext import commands
from keep_alive import keep_alive
import os
import requests
import asyncio
import uuid  # Necesitas importar la librería uuid
import json  # Asegúrate de que esta línea esté presente

bot = commands.Bot(command_prefix='/')

# Step 2
API_URL = "https://zzzzzzzbbbbbbb-texttoimage-jmpstrt.hf.space/run/predict"

# Step 3
# Step 3.1
def encode(img):
    with open(img, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string

# Step 3.2
def get_image_without_background(encode_image):
    response = requests.post(
        API_URL, json={"data": ["data:image/jpg;base64," + encode_image]}).json()
    return response['data']

# Step 4
def decode(imgs):
    base64_data = imgs[0][22:]
    image_data = base64.b64decode(base64_data)
    image = Image.open(BytesIO(image_data))
    return image

async def get_result(prompt, max_retries=4, max_concurrent_requests=4):
  for _ in range(max_retries):
      tasks = [process_request(prompt, attempt) for attempt in range(1, max_concurrent_requests + 1)]
      results = await asyncio.gather(*tasks, return_exceptions=True)

      for result in results:
          if not isinstance(result, Exception):
              return result

      await asyncio.sleep(1)  # Esperar un breve período antes de volver a intentar

  return {"error": "Se alcanzó el número máximo de intentos"}

async def process_request(prompt, attempt):
  try:
      response = await asyncio.to_thread(requests.post, API_URL, json={"data": [f"{prompt}_id_{uuid.uuid4()}"]})
      response.raise_for_status()
      return response.json()
  except Exception as e:
      print(f"Error en la solicitud ({attempt}/{max_concurrent_requests}): {e}")
      raise  # Propagar la excepción para que sea capturada por asyncio.gather

# Cargar la lista de usuarios autorizados desde el archivo users.json
def load_authorized_users():
    with open('users.json') as f:
        users = json.load(f)
    return set(users)

# Verificar si el usuario está autorizado para usar /img
def is_user_authorized(author_id):
    authorized_users = load_authorized_users()
    return str(author_id) in authorized_users

# Comando para generar imágenes sin fondo
@bot.slash_command(name='img')
async def generate_image(ctx, prompt: str):
    # Verificar la autorización del usuario
    if not is_user_authorized(ctx.user.id):
        await ctx.send("**Para tener acceso a este comando, deberás tener rol premium**\n"
                     "- Puedes comprarlo en nuestro Servidor: [Aquí](https://discord.gg/5zsfagW4Zm)\n"
                     "- Y accede al canal: https://discord.com/channels/1185752992998236200/1189187391139876904")
        return

    msg = await ctx.send('Pensando, por favor espera...')

    response = await get_result(prompt)

    if "data" in response and response["data"]:
        data = response["data"]
        if data[0]:
            image = Image.open(BytesIO(base64.b64decode(data[0].replace('data:image/jpeg;base64,', ''))))

            # Crear un nuevo objeto Embed de Discord (usando nextcord.Embed)
            embed = nextcord.Embed()
            embed.set_image(url='attachment://result.png')  # Establecer la imagen en el embed

            # Agregar pie de imagen personalizado
            embed.set_footer(text="Create with ©️ Quantum AI v2")

            with BytesIO() as buffer:
                image.save(buffer, 'PNG')
                buffer.seek(0)

                # Enviar el embed con la imagen como archivo adjunto
                await ctx.send(embed=embed, file=nextcord.File(fp=buffer, filename='result.png'))
                await msg.delete()
        else:
            await ctx.send("Error: Se produjo una saturacion de solicitudes.")
            await msg.delete()
    else:
        await ctx.send("Error: Espere unos segundos e intente de nuevo.")
        await msg.delete()

# Keep the bot alive on replit
keep_alive()

# Run the bot in a loop
while True:
    try:
        bot.run(os.environ['DISCORD_TOKEN'])
    except Exception as e:
        print(f"Error al ejecutar el bot: {e}")
    finally:
        print("Reiniciando el bot...")
        asyncio.sleep(5)  # Espera 5 segundos antes de reiniciar