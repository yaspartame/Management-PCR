from app import app

if __name__ == '__main__':
<<<<<<< Updated upstream
    app.run(debug=True, port=5000)
=======
    # Trigger reload final final final
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
>>>>>>> Stashed changes
