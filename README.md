# CarePath

CarePath is a robust Django-based API designed to modernize hospital queue management. It streamlines patient flow, reduces waiting times, and integrates advanced AI capabilities for drug verification.

## 🚀 Features

### 🏥 Hospital & Patient Management
*   **Hospital Registry**: Manage hospital details including location (latitude/longitude) and contact info.
*   **Patient Profiles**: Track patient status (New vs. Returning) and history.

### ⏳ Smart Queue System
*   **Dynamic Queueing**: Patients can join queues with automatic position calculation.
*   **Real-time Updates**: Status tracking (Waiting → Called → Completed).
*   **Auto-Reordering**: Intelligent queue shifting using `django-lifecycle` hooks when a patient is called or leaves.
*   **Concurrency Safety**: Uses database locking (`select_for_update`) to prevent race conditions during queue joining.

### 🤖 AI-Powered Drug Verification
Powered by **Google Gemini 2.5 Flash**:
*   **Drug Validity Check**: Upload an image of a drug to analyze its expiration and physical condition.
*   **Drug Authentication**: Verify the authenticity of a drug packaging via image analysis.

### 📚 Documentation
*   **Interactive API Docs**: Fully documented with Swagger UI and Redoc (via `drf-spectacular`).

## 🛠️ Tech Stack

*   **Framework**: Django 6.0, Django REST Framework 3.16
*   **Database**: SQLite (Default)
*   **AI Engine**: Google GenAI SDK (`google-genai`)
*   **Image Processing**: Pillow
*   **Utilities**: `django-lifecycle`, `python-decouple`

## 📋 Prerequisites

*   Python 3.10+
*   A Google Cloud Project with the **Gemini API** enabled.

## ⚡ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/carepath.git
    cd carepath
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory:
    ```ini
    SECRET_KEY=your_django_secret_key
    DEBUG=True
    GEMINI_API_KEY=your_google_gemini_api_key
    ```

5.  **Run Migrations**
    ```bash
    python manage.py migrate
    ```

6.  **Start the Server**
    ```bash
    python manage.py runserver
    ```

## 📖 API Documentation

Once the server is running, access the interactive documentation:

*   **Swagger UI**: [http://127.0.0.1:8000/api/schema/swagger-ui/](http://127.0.0.1:8000/api/schema/swagger-ui/)
*   **Redoc**: [http://127.0.0.1:8000/api/schema/redoc/](http://127.0.0.1:8000/api/schema/redoc/)

## 🔑 Key Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/queue/join/` | Join a hospital queue |
| `GET` | `/api/queue/list/` | List current queues |
| `POST` | `/api/drug/check/` | AI Drug Validity Check (Multipart/Form-data) |
| `POST` | `/api/drug/authenticate/` | AI Drug Authentication (Multipart/Form-data) |
| `GET` | `/api/hospitals/list/` | List all hospitals |

## 🧪 Testing

Run the test suite to ensure everything is working correctly. The tests use `unittest.mock` to simulate AI responses, saving your API quota.

```bash
python manage.py test
```

## 🤝 Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
