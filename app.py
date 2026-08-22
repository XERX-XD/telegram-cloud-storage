from flask import Flask, request, jsonify, redirect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
import secrets
import datetime
from dotenv import load_dotenv
import os
import requests
from datetime import timedelta

from flask_cors import CORS

load_dotenv()
app = Flask(__name__)

CORS(app)
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storage.db"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
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
        try:

            response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",data={"chat_id":CHAT_ID},files={"document":(upload_file.filename,upload_file.stream)})
            result = response.json()
        except requests.exceptions.RequestException as e:

            total.append({"filename": upload_file.filename, "status": "failed", "error": f"network error: {str(e)}"})
            continue
        if not result.get("ok"):
            total.append({"filename": upload_file.filename, "status": "failed", "error": result.get("description", "unknown error")})
            continue
        
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
        if file_id is None:
            total.append({"filename": upload_file.filename, "status": "failed", "error": "unrecognized file type in response"})
            continue
        new_file = File(filename=upload_file.filename,file_id=file_id)
        db.session.add(new_file)
        db.session.commit()
        total.append({"filename": upload_file.filename, "file_id": file_id})

    return jsonify({"status": "uploaded", "files": total})
@app.route("/files",methods=["GET"])
@jwt_required()
def get_files():
    files = File.query.all()
    print(files)
    result=[]
    if files:
        for file in files:
            result.append({"id":file.id,"filename":file.filename,"uploaded_at":file.uploaded_at,"file_id":file.file_id})
        return jsonify({"status":"found","files":result})
    return jsonify({"status":"not found any thing in database"})

@app.route("/files/<int:id>/download")
@jwt_required()
def download(id):
    file_record = db.session.get(File, id)
    if not file_record:
        return jsonify({"status":"file not found to that id"})
        
    file_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",params={"file_id": file_record.file_id})
    print(file_response.json())
    file_info= file_response.json()
    if not file_info.get("ok"):
        return jsonify({"error": "could not retrieve file from Telegram"}), 502
    file_path = file_info["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    
    return redirect(download_url)

@app.route("/files/search",methods=["GET"])
@jwt_required()
def search():
    result=[]
    query = request.args.get("q", "").strip()
    #print(query)
    if not query:
        return jsonify({
            "status": "error",
            "message": "Search query is required"
        }), 400
    files = File.query.filter(File.filename.ilike(f"%{query}%"))
    #print(files)
    for file in files:
        print(file.filename)
        result.append({
            "id": file.id,
            "filename": file.filename,
            "file_id": file.file_id,
            "uploaded_at": file.uploaded_at
        })
    return jsonify({
        "status": "success",
        "count": len(result),
        "files": result
    })
with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(debug=True)