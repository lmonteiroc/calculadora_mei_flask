from app import create_app

# esta variável PRECISA se chamar "app" (é o que o gunicorn usa)
app = create_app()

if __name__ == "__main__":
    # debug=False em produção
    app.run(host="0.0.0.0", port=5000, debug=False)
