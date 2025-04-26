# Notulen

Modern meeting documentation with AI transcription, summarization, and intelligent querying.

## Overview

Notulen is a comprehensive meeting management platform that helps teams document, organize, and extract insights from their meetings:

- **Record**: Capture audio directly in the app or upload existing recordings
- **Transcribe**: Automatically convert speech to accurate text transcripts
- **Summarize**: Generate concise meeting summaries and extract action items
- **Query**: Ask questions about any past meeting through a natural language chatbot

## Features

- **Meeting Recording and Management**:
  - Record meetings directly within the application
  - Upload existing audio recordings
  - Organize meetings by groups and projects
  - Secure storage with user-based access controls

- **AI-Powered Processing**:
  - Automatic speech-to-text transcription
  - Meeting summarization with key points extraction
  - Action item identification and assignment
  - Participant recognition

- **Intelligent Assistant**:
  - Natural language queries about meeting content
  - Search across all your meeting history
  - Get answers about decisions, action items, and responsibilities
  - Context-aware responses that understand meeting history

- **Team Collaboration**:
  - Share meeting recordings, transcripts, and summaries
  - Group-based access management
  - Collaborative note-taking and annotation

- **Integrations**:
  - OpenAI for advanced natural language processing
  - Supabase for secure authentication and data storage

## Technical Stack

- **Frontend**: Vue 3 with TypeScript, Vite, Tailwind CSS, and shadcn/vue components
- **Backend**: FastAPI Python API with a structured project setup
- **Authentication**: Supabase auth system with login, registration, and profile management
- **Storage**: Secure file storage for audio recordings and processing results
- **AI**: OpenAI for transcription, summarization, and conversational AI

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm (v7 or higher)
- Python 3.13 or higher
- pip (Python package installer)
- Supabase account and project (for authentication and storage)
- OpenAI API key (for AI functionality)

### Environment Setup

1. Create a `.env` file in the frontend directory:
```
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

2. Create a `.env` file in the backend directory:
```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

2. Create a `.env` file in the workers directory:
```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/brebribre/notulen.git
cd notulen
```

2. Install dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

4. Setup the workers environment:
```bash
cd ../workers
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### Development

To run the development server, from the root folder notulen:
```bash
npm run dev
```

## License

MIT
