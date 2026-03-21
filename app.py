from flask import Flask
from dotenv import load_dotenv
import os

# import blueprints
from routes.auth import bp as auth_bp
from routes.dashboard import bp as dashboard_bp
from routes.glucose import bp as glucose_bp
from routes.reminders import bp as reminders_bp
from routes.settings import bp as settings_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY is not set. Check your .env file.")

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(glucose_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(settings_bp)

@app.route("/healthz")
def health_check():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(debug=True)

