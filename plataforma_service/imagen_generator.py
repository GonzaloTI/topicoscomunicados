# imagegenerator.py
import os
import time
import uuid
import requests
from dotenv import load_dotenv


class ImageGenerator:
    def __init__(
        self,
        api_key: str | None = None,
        output_folder: str = "images",
        public_base_url: str = "https://pagina-de-presentacion3.onrender.com/images"
        #public_base_url: str = "http://127.0.0.1:5000/images"
    ):
        
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
    def generate_image(
        self,
        prompt_text: str,
        ratio: str = "1024:1024",
        model: str = "gemini_2.5_flash",
        seed: int | None = None,
        filename: str | None = None,
        reference_images: list[dict] | None = None,
        use_content_moderation: bool = True,
    ) -> dict:
        """
        Genera una imagen en Runway y la guarda localmente.

        Retorna un dict con:
        {
            "runway_url": "<url directa en Runway>",
            "public_url": "<url pública servida por tu API>"
        }
        """
        if not prompt_text:
            raise ValueError("prompt_text no puede estar vacío.")

        # 1) Crear tarea en Runway
        task_id = self._crear_tarea_imagen(
            prompt_text=prompt_text,
            ratio=ratio,
            model=model,
            seed=seed,
            reference_images=reference_images,
            use_content_moderation=use_content_moderation,
        )

        # 2) Esperar a que termine
        runway_url = self._esperar_y_obtener_url(task_id)

        # 3) Guardar imagen en tu servidor
        saved_filename = self._guardar_imagen_en_servidor(runway_url, filename=filename)

        # 4) Construir URL pública
        public_url = self._obtener_url_publica(saved_filename)

        return {
            "runway_url": runway_url,
            "public_url": public_url,
        }

    # ------------------ HELPERS PRIVADOS ------------------ #
    def _crear_tarea_imagen(
        self,
        prompt_text: str,
        ratio: str,
        model: str,
        seed: int | None,
        reference_images: list[dict] | None,
        use_content_moderation: bool,
    ) -> str:
        """
        Lanza la tarea text_to_image en Runway y devuelve el task_id.
        """
        url = f"{self.base_url}/text_to_image"


       
        prompt_textcontext = f"creame una noticia con este contenido, {prompt_text} que tenga de fondo la universidad UAGRM"
        
        payload: dict = {
            "promptText": prompt_textcontext,
            "ratio": ratio,
            "model": "gemini_2.5_flash",
        }

        if seed is not None:
            payload["seed"] = seed

        if reference_images:
            # Deben tener formato: {"uri": "...", "tag": "opcional"}
            payload["referenceImages"] = reference_images

        if use_content_moderation:
            payload["contentModeration"] = {
                "publicFigureThreshold": "auto"
            }

        resp = requests.post(url, json=payload, headers=self.headers)
        print("STATUS POST:", resp.status_code)
        print("BODY POST:", resp.text)

        if resp.status_code != 200:
            raise RuntimeError(f"Error al crear tarea de imagen: {resp.text}")

        data = resp.json()
        task_id = data.get("id")
        if not task_id:
            raise RuntimeError(f"No se recibió 'id' de tarea en la respuesta: {data}")

        return task_id

    def _esperar_y_obtener_url(self, task_id: str, sleep_seconds: int = 1, max_tries: int = 300) -> str:
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

    def _guardar_imagen_en_servidor(self, url_imagen: str, filename: str | None = None) -> str:
        """
        Descarga una imagen desde URL y la guarda en /images (o la carpeta configurada).
        Devuelve el nombre del archivo guardado.
        """
        resp = requests.get(url_imagen)

        if resp.status_code != 200:
            raise Exception(f"No se pudo descargar la imagen desde la URL: {url_imagen}")

        # Puedes cambiar a .png si prefieres
        extension = ".jpg"
        filename = filename or f"{uuid.uuid4()}{extension}"
        filepath = os.path.join(self.output_folder, filename)

        with open(filepath, "wb") as f:
            f.write(resp.content)

        return filename

    def _obtener_url_publica(self, filename: str) -> str:
        """
        Genera la URL pública con tu dominio verificado.
        Por defecto usa: https://pagina-de-presentacion3.onrender.com/images/<filename>
        Cambia 'images' o el dominio si tu endpoint es otro.
        """
        return f"{self.public_base_url}/{filename}"
