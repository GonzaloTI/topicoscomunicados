from plataforma_service.video_generator import VideoGenerator

vg = VideoGenerator()

resultado = vg.generate_video(
    prompt_text="un video de un comunicado de universidad, titulo 'UAGRM inicio de inscripción', estilo moderno profesional"
)

print("URL Runway:", resultado["runway_url"])
print("URL pública API:", resultado["public_url"])