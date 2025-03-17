# Speech-to-Text Tool 🎤 → 📝

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green)](https://flask.palletsprojects.com/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Speech--to--Text-orange)](https://cloud.google.com/speech-to-text)

[English](#english) | [Русский](#русский)

</div>

---

<a name="english"></a>
## 🇺🇸 English

### 📋 Overview
A powerful Flask-based server that converts speech to text using Google Cloud Speech-to-Text API. Perfect for integration with chat systems and applications requiring voice transcription capabilities.

### ✨ Features
- 🎯 High-accuracy speech recognition
- 🌍 Multi-language support (default: Russian)
- 🔄 Automatic audio format conversion
- 📊 Confidence scores for transcriptions
- 🎵 Support for various audio formats (MP3, WAV, OGG, etc.)
- 🚀 REST API interface
- 📝 Automatic punctuation

### 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/Ivantech123/Speech-to-text-tool.git
cd Speech-to-text-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create .env file with:
GOOGLE_API_KEY=your_api_key
PORT=5000
FLASK_ENV=development
FLASK_APP=server.py
```

### 🚀 Usage

1. Start the server:
```bash
python server.py
```

2. Send requests to the API:
```bash
curl -X POST -F "file=@audio.mp3" -F "language=ru-RU" http://localhost:5000/transcribe
```

### 📡 API Reference

#### Transcribe Audio
- **Endpoint:** `POST /transcribe`
- **Parameters:**
  - `file`: Audio file (multipart/form-data)
  - `language`: Language code (optional, defaults to "ru-RU")
- **Response:**
```json
{
  "success": true,
  "results": [
    {
      "transcript": "Transcribed text",
      "confidence": 0.98
    }
  ]
}
```

### 🧪 Testing
Run the test suite:
```bash
python test_api.py
```

---

<a name="русский"></a>
## 🇷🇺 Русский

### 📋 Обзор
Мощный сервер на базе Flask для преобразования речи в текст с использованием Google Cloud Speech-to-Text API. Идеально подходит для интеграции с чат-системами и приложениями, требующими возможности транскрибации голоса.

### ✨ Возможности
- 🎯 Высокая точность распознавания речи
- 🌍 Поддержка нескольких языков (по умолчанию: русский)
- 🔄 Автоматическое преобразование аудиоформатов
- 📊 Оценка уверенности в распознавании
- 🎵 Поддержка различных форматов аудио (MP3, WAV, OGG и др.)
- 🚀 REST API интерфейс
- 📝 Автоматическая пунктуация

### 🛠️ Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Ivantech123/Speech-to-text-tool.git
cd Speech-to-text-tool
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
# Создайте файл .env с содержимым:
GOOGLE_API_KEY=ваш_api_ключ
PORT=5000
FLASK_ENV=development
FLASK_APP=server.py
```

### 🚀 Использование

1. Запустите сервер:
```bash
python server.py
```

2. Отправьте запрос к API:
```bash
curl -X POST -F "file=@audio.mp3" -F "language=ru-RU" http://localhost:5000/transcribe
```

### 📡 API Справочник

#### Транскрибация аудио
- **Endpoint:** `POST /transcribe`
- **Параметры:**
  - `file`: Аудиофайл (multipart/form-data)
  - `language`: Код языка (необязательно, по умолчанию "ru-RU")
- **Ответ:**
```json
{
  "success": true,
  "results": [
    {
      "transcript": "Транскрибированный текст",
      "confidence": 0.98
    }
  ]
}
```

### 🧪 Тестирование
Запустите набор тестов:
```bash
python test_api.py
```

---

<div align="center">

### 🌟 Star us on GitHub
If you find this tool useful, please consider giving it a star!

</div>
