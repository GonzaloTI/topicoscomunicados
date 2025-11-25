import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RUNWAYML_API_SECRET")

# -------------------------------
# 1. CREAR LA TAREA DE VIDEO
# -------------------------------
url = "https://api.dev.runwayml.com/v1/text_to_video"

payload = {
    "promptText": "un video de un comunicado de universidad, titulo 'UAGRM inicio de inscripción', estilo moderno profesional",
    "duration": 4,            # ✔️ Debe ser 4, 6 o 8 (2 NO ES VÁLIDO)
    "audio": False,
    "ratio": "1280:720",
    "model": "veo3.1_fast"
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-Runway-Version": "2024-11-06"
}

response = requests.post(url, json=payload, headers=headers)

print("STATUS POST:", response.status_code)
print("BODY POST:", response.text)

data = response.json()
task_id = data.get("id")
print("Task creada:", task_id)

# Si no hay id, no sigas
if not task_id:
    print("❌ La API no devolvió 'id'. Revisa el BODY POST de arriba (modelo, créditos, etc.).")
    raise SystemExit()

# -------------------------------
# 2. ESPERAR A QUE EL VIDEO TERMINE
# -------------------------------
task_url = f"https://api.dev.runwayml.com/v1/tasks/{task_id}"

while True:
    task_response = requests.get(task_url, headers=headers).json()
    status = task_response.get("status")

    print("Estado:", status)

    if status == "SUCCEEDED":
        print("¡Video listo!")
        print(task_response)
        break

    if status == "FAILED":
        print("Error:", task_response)
        raise SystemExit()

    time.sleep(2)  # consultar cada 2 segundos

# -------------------------------
# 3. OBTENER URL DEL VIDEO
# -------------------------------
video_url = task_response["output"][0]
print("URL del video:", video_url)

# -------------------------------
# 4. DESCARGAR EL VIDEO
# -------------------------------
video_bytes = requests.get(video_url).content

with open("resultado_video.mp4", "wb") as f:
    f.write(video_bytes)

print("Video guardado como resultado_video.mp4")
