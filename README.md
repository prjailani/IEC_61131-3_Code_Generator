> # Human Text to IEC 61131-3 Structured Text Code Generator

##  Overview
This project converts **natural language instructions (NLP)** into **IEC 61131-3 Structured Text (ST)** code.  
It integrates **AI (GPT + RAG)**, a **validation engine**, and a **re-correction loop** to ensure generated code is **valid, context-aware, and consistent**.

---

## Features
- **Natural Language → Structured Text (ST)** conversion.  
- **Intermediate JSON Representation** before final ST code generation.  
- **Validation Engine** to check syntax/semantics.  
- **Auto-Correction Loop**: Regenerates intermediate code until valid.  
- **RAG Integration** for realistic variable/component metadata.  
- **MongoDB** backend for metadata persistence.  
- **Frontend Integration** with React (Vite).  

---

## Tech Stack

- **Backend: FastAPI**

- **Database: MongoDB**

- **AI: GPT + RAG (knowledge-based generation)**

- **Frontend: React + Vite**

--- 

## Workflow

<img width="3840" height="989" alt="Image" src="https://github.com/user-attachments/assets/58f69b0a-d237-4328-8664-57c8c9751bb4" />


---
## Directory Structure

```
Root
|
├── AI_Integration
│   ├── kb
│   │   └── templates
│   │       ├── Details.txt
│   │       ├── iec_ir.schema.txt
│   │       └── variables.json
│   ├── main.py
│   ├── Prompts.py
│
├── backend
│   ├── fetchvariables.py
│   ├── generator.py
│   ├── main.py
│   └── validator.py
│
├── index.html
├── package.json
├── requirements.txt
├── vite.config.js
└── src
    ├── assets
    │   └── copy.png
    ├── components
    │   ├── App.jsx
    │   └── users.jsx
    ├── index.css
    └── main.jsx

```
---

## Authors
>---
>- **Abdul kader jailani**
>- **Arul karthikeyan**
>- **Rakul**
>- **NandhiRaja**
>---

