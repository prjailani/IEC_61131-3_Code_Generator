# Human Text to IEC 61131-3 Structured Text Code Generator

## Overview

This project converts **natural language instructions** into **IEC 61131-3 Structured Text (ST)** code.  
It integrates **AI (Groq LLM + RAG)**, a **validation engine**, and a **re-correction loop** to ensure generated code is **valid, context-aware, and consistent**.

## Features

- **Natural Language → Structured Text (ST)** conversion
- **Intermediate JSON Representation** before final ST code generation
- **Validation Engine** to check syntax and semantics
- **Auto-Correction Loop**: Regenerates intermediate code until valid
- **RAG Integration** for realistic variable/component metadata
- **MongoDB** backend for device metadata persistence
- **Modern React Frontend** with responsive UI

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 19 + Vite + TailwindCSS |
| Backend | FastAPI + Python |
| Database | MongoDB |
| AI/LLM | Groq (LLaMA 3.1) + LangChain + RAG |

## Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Natural        │────►│  AI Generation   │────►│  Validation     │
│  Language Input │     │  (JSON IR)       │     │  Engine         │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                              ┌────────────────────┐      │
                              │  Re-generation     │◄─────┤ (if errors)
                              │  Loop              │      │
                              └────────────────────┘      │
                                                          ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  ST Code        │◄────│  Code Generator │
                        │  Output         │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- MongoDB (Atlas or local)
- Groq API key ([get one here](https://console.groq.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IEC_61131-3_Code_Generator
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example files
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp AI_Integration/.env.example AI_Integration/.env
   
   # Edit the .env files with your credentials
   ```

5. **Start the application**
   ```bash
   # Option 1: Start everything together
   npm run dev:full
   
   # Option 2: Start separately
   npm run dev:frontend    # Terminal 1
   npm run dev:backend     # Terminal 2
   ```

6. **Open the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

## Project Structure

```
IEC_61131-3_Code_Generator/
├── AI_Integration/
│   ├── kb/
│   │   └── templates/
│   │       ├── Details.txt
│   │       ├── iec_ir.schema.txt
│   │       └── variables.json
│   ├── main.py          # AI/LLM integration
│   ├── Prompts.py       # System prompts
│   └── .env.example
│
├── backend/
│   ├── main.py          # FastAPI server
│   ├── generator.py     # JSON → ST converter
│   ├── validator.py     # Code validation
│   ├── fetchvariables.py # DB sync utility
│   └── .env.example
│
├── src/
│   ├── components/
│   │   ├── App.jsx      # Main application
│   │   └── users.jsx    # Variables management
│   ├── index.css        # Styles
│   └── main.jsx         # Entry point
│
├── .env.example         # Environment template
├── package.json         # Node dependencies
├── requirements.txt     # Python dependencies
└── README.md
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start frontend only |
| `npm run dev:full` | Start frontend + backend + sync |
| `npm run dev:frontend` | Start Vite dev server |
| `npm run dev:backend` | Start FastAPI server |
| `npm run sync:variables` | Sync variables from DB |
| `npm run build` | Build for production |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Fix ESLint errors |

## Environment Variables

### Required
| Variable | Description |
|----------|-------------|
| `MONGO_URI` | MongoDB connection string |
| `GROQ_API_KEY` | Groq API key for LLM |

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://127.0.0.1:8000` | Backend API URL |
| `DB_NAME` | `iec_code_generator` | MongoDB database name |
| `COLLECTION_NAME` | `variables` | MongoDB collection name |
| `GROQ_MODEL_NAME` | `llama-3.1-70b-versatile` | LLM model to use |
| `RAG_K` | `3` | Number of RAG results |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | CORS origins |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/generate-code` | Generate ST code from text |
| GET | `/get-variables` | Get all device variables |
| POST | `/save-variables` | Save device variables |
| POST | `/upload-variables-json` | Upload variables from file |
| DELETE | `/remove-duplicates` | Remove duplicate variables |

## Security Notes

- **Never commit `.env` files** - they contain secrets
- In production, restrict `ALLOWED_ORIGINS` to your domain
- The MongoDB URI should use proper credentials
- Rotate API keys periodically

## Authors

- **Abdul kader jailani**
- **Arul karthikeyan**
- **Rakul**
- **NandhiRaja**

## License

MIT License - see LICENSE file for details
