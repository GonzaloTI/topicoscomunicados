# videogenerator.py
import os
import time
import uuid
import requests
from dotenv import load_dotenv


class VideoGenerator:
    def __init__(
        self,
        api_key: str | None = None,
        output_folder: str = "videos",
        public_base_url: str = "https://pagina-de-presentacion3.onrender.com/videos"
    ):
        """
        api_key:        API key de Runway. Si no se pasa, toma RUNWAYML_API_SECRET del .env
        output_folder:  Carpeta local donde se guardarán los .mp4
        public_base_url:Base URL pública de tu API para servir los videos.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("RUNWAYML_API_SECRET")
        if not self.api_key:
            raise ValueError("No se encontró RUNWAYML_API_SECRET en el entorno ni se pasó api_key.")

        self.base_url = "https://api.dev.runwayml.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

        self.output_folder = output_folder
        self.public_base_url = public_base_url.rstrip("/")

        os.makedirs(self.output_folder, exist_ok=True)

    # ------------------ API PÚBLICA ------------------ #
    def generate_video(
        self,
        prompt_text: str,
        duration: int = 4,
        ratio: str = "1280:720",
        model: str = "veo3.1_fast",
        audio: bool = False,
        filename: str | None = None,
    ) -> dict:
        """
        Genera un video en Runway y lo guarda localmente.

        Retorna un dict con:
        {
            "runway_url": "<url directa en Runway>",
            "public_url": "<url pública servida por tu API>"
        }
        """
        if not prompt_text:
            raise ValueError("prompt_text no puede estar vacío.")

        # 1) Crear tarea en Runway
        task_id = self._crear_tarea_video(
            prompt_text=prompt_text,
            duration=duration,
            ratio=ratio,
            model=model,
            audio=audio,
        )

        # 2) Esperar a que termine
        runway_url = self._esperar_y_obtener_url(task_id)

        # 3) Guardar video en tu servidor
        saved_filename = self._guardar_video_en_servidor(runway_url, filename=filename)

        # 4) Construir URL pública
        public_url = self._obtener_url_publica(saved_filename)
        
        # 5) Construir ruta local absoluta
        local_path = os.path.join(self.output_folder, saved_filename)

        return {
            "runway_url": runway_url,
            "public_url": public_url,
            "local_path": local_path,
        }
        

    # ------------------ HELPERS PRIVADOS ------------------ #
    def _crear_tarea_video(
        self,
        prompt_text: str,
        duration: int,
        ratio: str,
        model: str,
        audio: bool,
    ) -> str:
        """
        Lanza la tarea text_to_video en Runway y devuelve el task_id.
        """
        url = f"{self.base_url}/text_to_video"

        prompt_textcontext = f"creame un video de noticia con este contenido, {prompt_text} que el video tenga de fondo la universidad UAGRM y una presentadora hermosa coreana"
        

        payload = {
            "promptText": prompt_textcontext,
            "ratio": ratio,
            "model": model,
        }

        # Solo agregamos duration y audio si el modelo los soporta;
        # si dan problemas, puedes comentar/ajustar según doc.
        if duration:
            payload["duration"] = duration
        if audio is not None:
            payload["audio"] = audio

        resp = requests.post(url, json=payload, headers=self.headers)
        print("STATUS POST:", resp.status_code)
        print("BODY POST:", resp.text)

        if resp.status_code != 200:
            raise RuntimeError(f"Error al crear tarea de video: {resp.text}")

        data = resp.json()
        task_id = data.get("id")
        if not task_id:
            raise RuntimeError(f"No se recibió 'id' de tarea en la respuesta: {data}")

        return task_id

    def _esperar_y_obtener_url(self, task_id: str, sleep_seconds: int = 2, max_tries: int = 300) -> str:
        """
        Consulta /tasks/{id} hasta que el status sea SUCCEEDED o FAILED.
        Devuelve la primera URL del output.
        """
        task_url = f"{self.base_url}/tasks/{task_id}"

        for _ in range(max_tries):
            resp = requests.get(task_url, headers=self.headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Error al consultar tarea {task_id}: {resp.text}")

            data = resp.json()
            status = data.get("status")
            print("Estado:", status)

            if status == "SUCCEEDED":
                output = data.get("output") or []
                if not output:
                    raise RuntimeError(f"Tarea {task_id} terminada pero sin output: {data}")
                return output[0]

            if status == "FAILED":
                raise RuntimeError(f"Tarea {task_id} falló: {data}")

            time.sleep(sleep_seconds)

        raise TimeoutError(f"La tarea {task_id} no terminó dentro del tiempo esperado.")

    def _guardar_video_en_servidor(self, url_video: str, filename: str | None = None) -> str:
        """
        Descarga el video desde la URL de Runway y lo guarda en /videos (o la carpeta configurada).
        Devuelve el nombre del archivo guardado.
        """
        resp = requests.get(url_video)
        if resp.status_code != 200:
            raise Exception(f"No se pudo descargar el video desde la URL: {url_video}")

        extension = ".mp4"
        filename = filename or f"{uuid.uuid4()}{extension}"
        filepath = os.path.join(self.output_folder, filename)

        with open(filepath, "wb") as f:
            f.write(resp.content)

        return filename

    def _obtener_url_publica(self, filename: str) -> str:
        """
        Genera la URL pública con tu dominio verificado.
        Por defecto usa: https://pagina-de-presentacion3.onrender.com/videos/<filename>
        Cambia 'videos' si tu endpoint es otro.
        """
        return f"{self.public_base_url}/{filename}"
