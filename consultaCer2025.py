import requests
import json
import pandas as pd
import re
import asyncio
import notion_client
import streamlit as st
import os
from io import BytesIO
from PIL import Image

imagen1 = Image.open('minecLogo.jpeg')
imagen2 = Image.open('minecLogoTitle.jpeg')

st.image(imagen1)
st.image(imagen2)

# --- Configuración de la API (asegúrate de tener secrets.toml configurado) ---
try:
    api_key = st.secrets["wasender"]["API_KEY"]
    # st.success("API Key de Wasender cargada exitosamente.")
except KeyError:
    st.error("Error: WASENDER_API_KEY no encontrada en .streamlit/secrets.toml. Por favor, configúrala.")
    st.stop() # Detiene la ejecución si no hay API Key
  
# Importa la lógica de envío de WhatsApp
from whatsapp_sender import (send_multiple_messages_parallel, send_whatsapp_message_async)
url = "https://www.wasenderapi.com/api/send-message" 

# Configuración del cliente y del ID de la base de datos
database_id = st.secrets["notion"]["Pronda2025_databaseID"]
notion = notion_client.Client(auth = st.secrets["notion"]["authkey"])

def dropbox_to_raw(url: str) -> str:
    """
    Transforma una URL de Dropbox en una URL de descarga directa (raw).
    """
    if "dl=0" in url or "dl=1" in url:
        # Cambiamos el parámetro a raw=1
        return url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
    # Si no tiene dl, simplemente añadimos raw=1
    return url + "?raw=1"

# Función para convertir el enlace de Google Drive a imagen directa
def drive_to_image(url: str) -> str:
    if "drive.google.com/uc" in url:
        return url.replace("export=download", "export=image")
    return url  # Si no es una URL de Drive, la dejamos como está

@st.cache_data()
def fdata():
    all_results = []                                 # Lista para almacenar todos los resultados
    has_more = True
    start_cursor = None
    while has_more:
        response = notion.databases.query(            # 1. Hacer la consulta con o sin el start_cursor
            database_id=database_id,
            start_cursor=start_cursor)
        all_results.extend(response['results'])       # 2. Agregar los resultados actuales a la lista principal
        has_more = response['has_more']               # 3. Actualizar has_more y next_cursor para la siguiente iteración
        start_cursor = response['next_cursor']
    with open('dbpronda2025.json', 'w', encoding='utf8') as f:
            json.dump(response, f, ensure_ascii=False, indent=4)
    flattened_data = []                               # 4. Aplanar los datos y crear el DataFrame
    for result in all_results:
        properties = result['properties']
        nombreu = properties['NOMBRES2025']['title'][0]['text']['content']
        apellidou = properties['APELLIDOS2025']['rich_text'][0]['text']['content']
        certificado2025 = properties['certificado2025']['url']
        certificado2022 = properties['certificado2022']['url']
        certificado2023 = properties['certificado2023']['url']
        certificado2024 = properties['certificado2024']['url']
        cedula = properties['CEDULA']['number']

        flattened_data.append({'Cedula' : cedula, 'Nombre' : nombreu, 'apellidou': apellidou,  'certificado2022url' : certificado2022, 'certificado2023url' : certificado2023, 'certificado2024url' : certificado2024, 'certificado2025url' : certificado2025 })

    df = pd.DataFrame(flattened_data)
    return df

@st.cache_data
def get_image_bytes(image_url: str) -> bytes:
    """Descarga la imagen y devuelve los bytes."""
    resp = requests.get(image_url, timeout=10)
    resp.raise_for_status()          # lanza excepción si algo falla
    return resp.content


df = fdata()
#df
st.subheader("Módulo de Consulta de Certificados Prondamin")

idced = st.text_input("Cédula : ")
try:
    registrosol = df[df["Cedula"] == int(idced)]
    #registrosol
    registrosol1 = registrosol.to_dict()
    #registrosol1

    def muestracer(cualcer):
        imacer25 = registrosol1[cualcer]
        #f"imacer25 = {imacer25}"
        url2025 = list(imacer25.values())[0]
        #url2025
        try:
            if url2025.find('dropbox')>0:
                imacer25_directa = dropbox_to_raw(url2025)
                f"Certificado Prondamin {cualcer[-7:-3]}"
                st.image(imacer25_directa)
            if url2025.find('drive')>0:
                image_bytes = get_image_bytes(url2025)
                f"Certificado Prondamin {cualcer[-7:-3]}"
                st.image(BytesIO(image_bytes))
        except: f"NO hay certificado para el año {cualcer[-7:-3]}"

    nombreu = list(registrosol1['Nombre'].values())[0]
    apellidou = list(registrosol1['apellidou'].values())[0]
    st.success(f"Bienvenid@ {nombreu} {apellidou}")
    for certs in ["certificado2022url", "certificado2023url", "certificado2024url", "certificado2025url"]:
        muestracer(certs)
        '---'
    st.success('Para :red[**guardar**] la 👆imagen👆 de tu certificado👆 en tu :orange[**computadora**]💻, _puedes hacer clic con el **botón derecho** sobre la 👆imagen👆, y elegir en el **menú contextual** la opción de :blue[**imprimir**]🖨️ o :blue[**guardar imagen como**]_.📂 $\\newline$ En caso de que lo hagas desde una :orange[**tablet o un celular**]📱, manten la imagen _presionada_ y te aparecerá un **_menú contextual_** con las opciones de :blue[**agregar a fotos**]🖼️ (_que descargará el certificado en la carpeta :red[**Fotos**] de tu dispositivo_), :blue[**compartir**]✉️ (_que te permitirá enviarlo a un correo electrónico, Whatsapp, Telegram, Drive, etc_) y la de :blue[**copiar**] (_lo copia en memoria para pegarlo en otra aplicación tal como Powerpoint, Notas, etc_)')
except:
    st.error("Ingrese una Cédula válida")
