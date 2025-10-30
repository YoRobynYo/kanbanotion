Kanbanotion — Project Setup & Workflow Guide

This document is the single source of truth for setting up, running, and managing the Kanbanotion project.
Quick Reference: Daily Workflow

This is what you'll do every day. It assumes the one-time setup is complete.

Directory Structure:

    TOP-LEVEL (Git Root): /Users/robynmai/Live-Builds/kanbanotion
    PROJECT-LEVEL (App Root): /Users/robynmai/Live-Builds/kanbanotion/kanban

You will keep a few terminals open.

🖥️ Terminal 1 — SCSS Watcher (at PROJECT-LEVEL)

    Go into the project sub-folder:
    cd /Users/robynmai/Live-Builds/kanbanotion/kanban
    Run the watcher: npm run build:css
    Keep this running to auto-compile your styles.

🧠 Terminal 2 — Backend AI Server (at PROJECT-LEVEL)

    Go into the project sub-folder:
    cd /Users/robynmai/Live-Builds/kanbanotion/kanban
    Activate your environment and run the server:
    source venv/bin/activate
    python backend/app.py
    Keep this running. Your AI server is at http://127.0.0.1:8000.

🌐 Terminal 3 — Frontend Live Server (at PROJECT-LEVEL)

    Go into the project sub-folder:
    cd /Users/robynmai/Live-Builds/kanbanotion/kanban
    Run the server: python -m http.server 8080
    Visit your project in the browser at: http://localhost:8080

One-Time Project Setup

Do these steps only once for the entire project.

1. GitHub Repository Setup (One Time Only)

    Go to GitHub.com, create a new, empty repository named kanbanotion.
    Copy the repository URL (e.g., https://github.com/YoRobynYo/kanbanotion.git).

2. Local Project & Git Initialization (One Time Only)

    Open a terminal at your TOP-LEVEL folder:
    cd /Users/robynmai/Live-Builds/kanbanotion
    Initialize the Git repository:
    git init
    Add all project files:
    git add .
    Make your first commit:
    git commit -m "Initial project commit"
    Rename the branch to main:
    git branch -M main
    Connect to your GitHub repository (paste the URL you copied):
    git remote add origin https://github.com/YoRobynYo/kanbanotion.git
    Push your project to GitHub for the first time:
    git push -u origin main

3. Backend Environment (at PROJECT-LEVEL)

    Go into the project sub-folder:
    cd /Users/robynmai/Live-Builds/kanbanotion/kanban
    Create and activate a virtual environment:
    python -m venv venv
    source venv/bin/activate
    Install backend dependencies:
    pip install fastapi "uvicorn[standard]" ollama pydantic

4. Frontend Environment (at PROJECT-LEVEL)

    Go into the project sub-folder:
    cd /Users/robynmai/Live-Builds/kanbanotion/kanban
    Initialize npm and install Sass:
    npm init -y
    npm install sass --save-dev
    Add the build script to your package.json file:
    npm pkg set "scripts.build:css"="sass styles/main.scss styles/main.css --watch"

Daily Git Workflow

After you finish a piece of work, use these commands in a terminal at the TOP-LEVEL (/kanbanotion) folder.

    Stage all changes:
    git add .
    Commit the changes with a message:
    git commit -m "Your descriptive message about what you did"
    Push to GitHub:
    git push

Build Phases and To-Dos

Push your code to GitHub after each major feature.

✅ Phase 1: Core Kanban Board (Done)

    Built the HTML structure for a 5-column board.
    Styled the board with a clean, functional layout using SCSS.
    Implemented full drag-and-drop functionality for tasks.
    Added the ability to create new tasks in any column.
    Implemented data persistence using localStorage so the board state is saved.
    Added Edit and Delete functionality to all tasks.
    Set up the complete project structure with a main-sub layout.
    Configured the Git repository and a professional .gitignore file.

🚀 Phase 2: Chat Widget UI & Frontend Logic (Next)

    Style the chat widget with a "glassmorphism" UI effect.
    Make the chat button open and close the main chat window.
    Use js/chat.js to handle sending a message and displaying a response.
    Create the web_build_context.txt file to define the AI's personality and process.
    Set up the simplified FastAPI backend (backend/app.py) to serve the AI.

🔧 Phase 3: Backend Integration & Final Polish

    Connect the frontend chat widget to the backend AI server.
    Ensure the AI guide follows the instructions in web_build_context.txt.
    Refine the AI's step-by-step process instructions.
    Implement responsive design for the entire application.
    Final deployment & GitHub update.

Design and Technical Requirements

(This section from your original document is excellent and can be kept as-is)

    Page load time: Optimize for speed (minify, compress, lazy-load images)
    Mobile responsiveness: Works across all devices (use media queries)
    ...and so on...

Notes and Tips

(This section from your original document is also perfect)

    You only need to create the virtual environment and install dependencies once. After that, just run source venv/bin/activate when you start work.
    Stop any running server/watchers with Ctrl + C.
    If port 8080 is taken, try python -m http.server 8081 and visit http://localhost:8081.

debugging the servers 

    ERROR: [Errno 48] Address already in use
    run this :: lsof -i :8000
    look for the process id :: Their Process IDs (PIDs) are 5859 and 5890.
    stop those id running in the terminal :: kill -9 5859 
    and stop the other one running also :: kill -9 5890
    test the terminals :: lsof -i :8000
    then start the terminal if it's free :: uvicorn backend.main:app --reload