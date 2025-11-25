import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RUNWAYML_API_SECRET")

# -------------------------------
# 1. CREAR TAREA
# -------------------------------
url = "https://api.dev.runwayml.com/v1/text_to_image"

payload = {
    "promptText": "universidad , entrada de una universidad que se llama, UAGRM , y un modulo detras de la entada",
    "seed": 4294967295,
    "ratio": "1024:1024",
    "contentModeration": {
        "publicFigureThreshold": "auto"
    },
    "model": "gemini_2.5_flash"
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Runway-Version": "2024-11-06"
}

response = requests.post(url, json=payload, headers=headers)
task_id = response.json().get("id")

print("Task creada:", task_id)

# -------------------------------
# 2. ESPERAR A QUE TERMINE
# -------------------------------
task_url = f"https://api.dev.runwayml.com/v1/tasks/{task_id}"

while True:
    task_response = requests.get(task_url, headers=headers).json()
    status = task_response.get("status")
    print("Estado:", status)

    if status == "SUCCEEDED":
        print("¡Imagen lista!")
        print(task_response)
        break

    if status == "FAILED":
        print("Error:", task_response)
        exit()

    time.sleep(1)  # Espera 1 segundo y vuelve a consultar

# -------------------------------
# 3. OBTENER LA IMAGEN
# -------------------------------
image_url = task_response["output"][0]
print("URL de la imagen:", image_url)

# -------------------------------
# 4. DESCARGAR OPCIONALMENTE
# -------------------------------
image_bytes = requests.get(image_url).content
with open("resultado.jpg", "wb") as f:
    f.write(image_bytes)

print("Imagen guardada como resultado.png")
