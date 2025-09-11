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

<!-- <img width="3840" height="989" alt="Image" src="https://github.com/user-attachments/assets/58f69b0a-d237-4328-8664-57c8c9751bb4" /> -->

![Image](https://github.com/user-attachments/assets/f4f76acf-750f-4858-8965-84cff5a5c898)

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
## ScreenShots 

### Home Page 
<img width="1217" height="924" alt="Image" src="https://github.com/user-attachments/assets/5dd1006c-4269-4166-917b-a5f9442d670a" />

--- 
### Config Page 
<img width="1109" height="904" alt="Image" src="https://github.com/user-attachments/assets/1331902c-ffc4-41ac-bc52-ff72295fe290" />


## Authors
>---
>- **Abdul kader jailani**
>- **Arul karthikeyan**
>- **Rakul**
>- **NandhiRaja**
>---

