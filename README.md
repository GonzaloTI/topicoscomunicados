webhook para coneccion con twilio

librerias :

Flask
twilio
python-dotenv
psycopg2-binary
requests

se debe condigurar el sandbox, para recibir el callbak en la app de flask ,

ruta : develop / messaging / try it out / send a whatsapp message / sandbox - sandbox settings

r

{
        "facebook": {
            "response": "¿Necesitas orientación sobre el retiro de materias? ¡Estamos aquí para ayudarte! 📚✨"
        },
        "instagram": {
            "response": "¿Necesitas ayuda con el retiro de materias? ¡Contáctanos para más información! 📚✨"
        },
        "linkedin": {
            "response": "¿Buscas información sobre el retiro de materias? ¡Contáctanos para recibir la asesoría que necesitas! 📚✨"
        },
        "tiktok": {
            "response": "¿Problemas con el retiro de materias? ¡Déjanos ayudarte! 📚✨ #RetiroDeMaterias #Estudio #Ayuda"
        },
        "whatsapp": {
            "response": "¿Tienes dudas sobre el retiro de materias? ¡Escríbenos para brindarte la asesoría que necesitas! 📚✨"
        }
    }