# AI Trading Assistant

> **AI-ассистент трейдера** на базе Finam TradeAPI с поддержкой MCP инструментов

## 📁 Структура проекта

```
├── src/app/
│   ├── adapters/          # Finam API клиенты (sync/async)
│   ├── core/              # LLM, MCP клиент, config
│   └── interfaces/        # UI (Streamlit, CLI)
├── src/mcp_server/        # MCP сервер с торговыми инструментами
├── scripts/               # Генерация и валидация submission
├── data/processed/        # train.csv, test.csv, submission.csv
└── docs/                  # Assets.json и документация
```

## 🔧 Возможности

- **Streamlit UI** - веб-интерфейс с поддержкой MCP инструментов
- **Advanced CLI** - интерактивный CLI с function calling
- **MCP Server** - 10+ торговых инструментов (котировки, портфель, заказы)
- **Async API Client** - с автоматическим обновлением JWT токенов
- **Docker** - изолированное окружение с отдельным MCP контейнером

## 🚀 Быстрый старт

### Вариант 1: Docker

```bash
# 1. Скопируйте пример конфигурации
cp .env.example .env

# 2. Отредактируйте .env и добавьте API ключи
# OPENROUTER_API_KEY=your_key
# FINAM_ACCESS_TOKEN=your_token (опционально)

# 3. Запустите приложение
make up
# или: docker-compose up -d

# 4. Откройте в браузере
# http://localhost:8501
```

### Вариант 2: Локально

```bash
# 1. Установите зависимости
poetry install

# 2. Настройте .env
cp .env.example .env

# 3. Запустите веб-интерфейс
poetry run streamlit run src/app/interfaces/chat_app.py

# ИЛИ CLI чат
poetry run chat-cli-adv
```

## 📋 Основные команды

```bash
# Запуск Docker
make up          # Запустить приложение
make down        # Остановить приложение
make logs        # Просмотр логов

# CLI интерфейсы
poetry run chat-cli-adv       # CLI с MCP инструментами
poetry run mcp-server         # MCP сервер (порт 8765)

# Утилиты
make generate    # Генерация submission.csv
make validate    # Валидация submission
make metrics     # Подсчет accuracy
make lint        # Проверка кода
make format      # Форматирование кода
```
