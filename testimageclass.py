from plataforma_service.imagen_generator import ImageGenerator

ig = ImageGenerator()

resultado = ig.generate_image(
    prompt_text="universidad , entrada de una universidad que se llama UAGRM, y debajo un comunicado que dice: se suspenden las clases en la uagrm por bloqueo de la ficct , nadie  ",
)

print("URL Runway:", resultado["runway_url"])
print("URL pública API:", resultado["public_url"])
