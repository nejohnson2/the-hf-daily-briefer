import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Use SQLite locally by default, PostgreSQL on Heroku
    uri = os.environ.get("DATABASE_URL", "sqlite:///hf_daily.db")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+pg8000://", 1)
    elif uri.startswith("postgresql://") and "+pg8000" not in uri:
        uri = uri.replace("postgresql://", "postgresql+pg8000://", 1)
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ollama / LLM
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "ollama")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

    # HuggingFace
    HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN", None)
