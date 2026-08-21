# ☁️ Telegram Cloud Storage

A Flask-based cloud storage application that uses the **Telegram Bot API as the file storage backend** and **SQLite with SQLAlchemy** to store file metadata.

This project is being developed as a practical learning project for Flask, SQLAlchemy, JWT authentication, REST APIs, external API integration, and frontend development.

---

## 🚧 Project Status

**Currently in development**

The backend currently includes authentication, Telegram file upload, file listing, file downloading, and filename search.



### 🔐 Authentication

- JWT-based authentication
- Login endpoint
- Protected file endpoints
- JWT access token expiration of 1 day


### 📤 File Upload

- Upload one or multiple files
- Send files directly to Telegram
- Store Telegram `file_id` in SQLite
- Handle individual upload/network failures

### 📋 File Management

- List uploaded files
- Search files by filename
- Download files through Telegram

### 🔎 File Search

Search files using a URL query parameter:

```text
GET /files/search?q=photo
```

The search is case-insensitive and matches the search text anywhere in the filename.

For example, searching for:

```text
photo
```

can match:

```text
photo.jpg
holiday_photo.png
MyPhoto.jpeg
```


---

# 📁 Project Structure

```text
telegram-cloud-storage/
│
├── app.py
├── .env
├── .env.example
└── instance/
    └── storage.db
```

The frontend structure is still being developed.

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd telegram-cloud-storage
```

Replace `YOUR_REPOSITORY_URL` with your GitHub repository URL.

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your_strong_secret_key

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

You can use `.env.example` as a starting point.

### ⚠️ Security

Never upload your real `.env` file to GitHub.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.db
instance/
```

---

# 🤖 Telegram Setup

This project uses a Telegram bot to store uploaded files.

You need:

1. A Telegram bot
2. The bot token
3. A Telegram chat where the bot can send files
4. The chat ID

Put the values in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

The application sends uploaded files to Telegram using the Bot API.

---

# ▶️ Running the Application

Start the Flask development server:

```bash
python app.py
```

The application normally runs at:

```text
http://127.0.0.1:5000
```

---

# 🔑 API Documentation

All file-related endpoints are protected with JWT authentication.

After logging in, send the returned token using:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 🔐 Login

### Endpoint

```http
POST /login
```

### Request

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

### Successful response

```json
{
    "access_token": "YOUR_JWT_TOKEN"
}
```

The username and password are checked against the configured environment variables.

---

# 📤 Upload Files

### Endpoint

```http
POST /upload
```

### Authentication

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Request type

```text
multipart/form-data
```

### File field

```text
file
```

Multiple files can be uploaded using the same `file` field.

### Example response

```json
{
    "status": "uploaded",
    "files": [
        {
            "filename": "photo.jpg",
            "file_id": "TELEGRAM_FILE_ID"
        }
    ]
}
```

The application sends each uploaded file to Telegram and stores the resulting Telegram `file_id` in SQLite.

---

# 📋 Get All Files

### Endpoint

```http
GET /files
```

### Authentication

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Example response

```json
{
    "status": "found",
    "files": [
        {
            "id": 1,
            "filename": "photo.jpg",
            "uploaded_at": "...",
            "file_id": "TELEGRAM_FILE_ID"
        }
    ]
}
```

---

# 🔎 Search Files

### Endpoint

```http
GET /files/search?q=photo
```

### Authentication

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Example

```text
/files/search?q=photo
```

### Example response

```json
{
    "status": "success",
    "count": 2,
    "files": [
        {
            "id": 1,
            "filename": "photo.jpg",
            "file_id": "TELEGRAM_FILE_ID",
            "uploaded_at": "..."
        },
        {
            "id": 5,
            "filename": "holiday_photo.png",
            "file_id": "TELEGRAM_FILE_ID",
            "uploaded_at": "..."
        }
    ]
}
```

### How search works

The backend gets the query from the URL:

```python
query = request.args.get("q", "").strip()
```

Then SQLAlchemy searches the filename:

```python
File.filename.ilike(f"%{query}%")
```

The `%` wildcard allows the query to match anywhere in the filename.

---

# 📥 Download File

### Endpoint

```http
GET /files/<id>/download
```

### Example

```text
GET /files/1/download
```

### Authentication

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

The application:

1. Finds the file record in SQLite.
2. Gets the Telegram `file_id`.
3. Calls Telegram's `getFile` API.
4. Gets the Telegram `file_path`.
5. Builds the Telegram download URL.
6. Redirects the client to the file.

Flow:

```text
File ID
   ↓
SQLite
   ↓
Telegram file_id
   ↓
Telegram getFile API
   ↓
file_path
   ↓
Telegram download URL
   ↓
Redirect
```

---

# 🗄️ Database

The project currently uses SQLite with Flask-SQLAlchemy.

The current `File` model contains:

```python
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_id = db.Column(db.String(300), nullable=False, unique=True)
    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )
```

The database stores file metadata and the Telegram `file_id`.

The actual uploaded file is handled by Telegram.

---

# ☁️ Storage Architecture

The application does not need to store uploaded files directly on the Flask server.

Instead:

```text
                 User
                   │
                   │ Upload
                   ▼
             Flask Server
                   │
                   │ Telegram Bot API
                   ▼
            ┌──────────────┐
            │   Telegram   │
            │              │
            │  Actual File │
            └──────────────┘
                   │
                   │ file_id
                   ▼
                SQLite
                   │
                   │
             File Metadata
```

This allows Telegram to act as the storage backend while SQLite stores the information needed by the application.

---

# 🔎 Search Architecture

The current search flow:

```text
Browser / Postman
        │
        │ GET /files/search?q=photo
        ▼
      Flask
        │
        ▼
 request.args
        │
        ▼
    SQLAlchemy
        │
        ▼
      SQLite
        │
        ▼
Matching files
        │
        ▼
    JSON response
```

---

# 🧪 Testing

The API can be tested using:

- Postman
- Browser
- curl
- JavaScript Fetch API

Example search:

```bash
curl "http://127.0.0.1:5000/files/search?q=photo"
```

Protected endpoints require a valid JWT token.

---

## Backend

- Flask
- REST APIs
- HTTP methods
- JWT authentication
- SQLAlchemy
- SQLite
- Database queries
- File uploads
- External APIs
- Telegram Bot API
- Error handling

---

# 👨‍💻 Author

**Aryan Chaudhary**

This project is being developed as a learning project while learning Flask, backend development, and frontend development.

---

The project is currently under active development.

---

## ⭐ If you find this project useful

Feel free to star the repository and follow the development as new Flask and frontend features are added.
