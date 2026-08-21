from flask import Flask, request, jsonify, redirect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
import secrets
import datetime
from dotenv import load_dotenv
import os
import requests
load_dotenv()
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storage.db"
db = SQLAlchemy(app)
jwt = JWTManager(app)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_id = db.Column(db.String(300), nullable=False, unique=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route("/login",methods=["POST"])
def login():
    data = request.get_json()
    if data["username"]==os.getenv("ADMIN_USERNAME") and data["password"]==os.getenv("ADMIN_PASSWORD"):
        token = create_access_token(identity=str(data["username"]))
        print(token)
        return jsonify({"access_token":token})
    return jsonify({"status":"error invalid username password"}),401

@app.route("/upload",methods=["POST"])
@jwt_required()
def upload():
    x = request.files.getlist("file")
    print(x)
    total=[]
    for upload_file in x:

        response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",data={"chat_id":CHAT_ID},files={"document":(upload_file.filename,upload_file.stream)})
        result = response.json()
        print(result)
        file_data=result["result"]
        if "document" in file_data:
            file_id = file_data["document"]["file_id"]
        elif "video" in file_data:
            file_id = file_data["video"]["file_id"]
        elif "photo" in file_data:
            file_id = file_data["photo"][-1]["file_id"]
        elif "audio" in file_data:
            file_id = file_data["audio"]["file_id"]
        else:
            file_id = None  
        
        new_file = File(filename=upload_file.filename,file_id=file_id)
        db.session.add(new_file)
        db.session.commit()
        total.append({"filename": upload_file.filename, "file_id": file_id})

    return jsonify({"status": "uploaded", "files": total})

with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(debug=True)