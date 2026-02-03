# HTS Oracle Frontend

[![React](https://img.shields.io/badge/React-19+-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)

> Chat-first React UI for HTS classification. Supports clarifying questions, session-based follow-ups, and result cards with duty details.

## 🎯 Overview

The frontend is a lightweight chat experience that sends messages to `/api/chat`, keeps the session id for multi-turn clarification, and renders results as expandable cards with copy + USITC links.

## ✨ Key Features

- **Chat-based workflow** with clarifying questions
- **Session persistence** for multi-turn classification
- **Result cards** with confidence, duty, and special rates
- **Copy + USITC link** for quick verification
- **Responsive layout** optimized for desktop and tablet

## 🏗️ Component Structure

```
src/
├── App.jsx                      # Chat flow + API calls
├── components/
│   ├── chat/
│   │   ├── ChatInput.jsx
│   │   └── ChatMessage.jsx
│   ├── layout/
│   │   ├── Header.jsx
│   │   └── MainLayout.jsx
│   └── results/
│       └── ResultCard.jsx
└── styles/
    └── globals.css
```

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** with npm
- **Backend API** running (defaults to `http://localhost:8080`)

### Installation

```bash
# From project root
cd frontend
npm install
```

### Environment Configuration

Create `.env.development` (optional):

```bash
VITE_API_URL=http://localhost:8080
```

### Run the App

```bash
npm run dev
```

App starts at `http://localhost:5173`.

## 📖 Usage

1. Enter a product description
2. If needed, answer a clarifying question
3. Review results and expand for details
4. Use the USITC link to verify codes

Example prompts:
- "Cotton t-shirts manufactured in Vietnam"
- "Stainless steel pipes for construction, 2-inch diameter"
- "LED light bulbs, 60-watt equivalent, household use"

## 🧪 Testing

```bash
npm run test
npm run test:ui
npm run test:debug
```

## 🔧 Build & Preview

```bash
npm run build
npm run preview
```

## 🔒 Notes

- The UI expects the `/api/chat` response shape (result vs question)
- Session id is stored in React state for follow-up turns

---

For backend API details, see [Backend README](../backend/README.md).
