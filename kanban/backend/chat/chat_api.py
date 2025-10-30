# backend/chat/chat_api.py || v4.5 – Blueprint, PDF & Course Auto-Integration
from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.ai_client import get_ai_client
import os, json, re
from PyPDF2 import PdfReader

router = APIRouter()

# --- SETUP ---
class ChatRequest(BaseModel):
    message: str

ai_client = get_ai_client()

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
COURSE_DIR = os.path.join(BASE_DIR, "courses")

print(f"📂 BASE_DIR: {BASE_DIR}")
print(f"📂 MEMORY_PATH: {MEMORY_PATH}")
print(f"📂 BLUEPRINT_DIR: {BLUEPRINT_DIR}")
print(f"📂 PDF_DIR: {PDF_DIR}")
print(f"📂 COURSE_DIR: {COURSE_DIR}")

# Ensure directories exist
os.makedirs(BLUEPRINT_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(COURSE_DIR, exist_ok=True)

# --- Blueprint Loader ---
def load_blueprint_files():
    files = {}
    if os.path.exists(BLUEPRINT_DIR):
        for filename in os.listdir(BLUEPRINT_DIR):
            if filename.endswith(".txt"):
                key = filename.replace(".txt", "")
                files[key] = os.path.join(BLUEPRINT_DIR, filename)
    print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
    return files

# --- PDF Loader ---
def load_pdf_files():
    files = {}
    if os.path.exists(PDF_DIR):
        for i, filename in enumerate(sorted(os.listdir(PDF_DIR)), 1):
            if filename.lower().endswith(".pdf"):
                key = f"pdf-{i:02d}"
                files[key] = {"path": os.path.join(PDF_DIR, filename), "name": filename}
    print(f"📄 Loaded {len(files)} PDFs: {', '.join(files.keys()) or 'none'}")
    return files

# --- Course Loader (Recursive) ---
def load_course_files():
    files = {}
    if os.path.exists(COURSE_DIR):
        for root, _, filenames in os.walk(COURSE_DIR):
            for filename in filenames:
                if filename.endswith((".js", ".txt", ".md", ".html")):
                    rel_path = os.path.relpath(os.path.join(root, filename), COURSE_DIR)
                    key = f"course-{rel_path.replace(os.sep, '-')}"
                    files[key] = os.path.join(root, filename)
    print(f"🎓 Loaded {len(files)} course files: {', '.join(list(files.keys())[:6]) if files else 'none'}...")
    return files

BLUEPRINT_FILES = load_blueprint_files()
PDF_FILES = load_pdf_files()
COURSE_FILES = load_course_files()

# --- Load Context ---
try:
    with open(KANBAN_PATH, "r", encoding="utf-8") as f:
        kanbanotion_context = f.read()
    
    resource_list = "\n\n=== AVAILABLE RESOURCES ===\n"
    if BLUEPRINT_FILES:
        resource_list += f"📘 Blueprints: {', '.join(BLUEPRINT_FILES.keys())}\n"
    if PDF_FILES:
        resource_list += f"📄 PDFs: {', '.join([v['name'] for v in PDF_FILES.values()])}\n"
    if COURSE_FILES:
        resource_list += f"🎓 Courses: {len(COURSE_FILES)} files in total\n"
    
    kanbanotion_context += "\n" + resource_list
    print("✅ Kanban context loaded successfully.")
except FileNotFoundError:
    kanbanotion_context = "You are Koby, a development assistant for Robyn."
    print("❌ Kanban context missing; using fallback.")

# --- Helpers ---
def extract_pdf_text(key: str, full=False):
    pdf_info = PDF_FILES.get(key)
    if not pdf_info: 
        return None
    
    try:
        reader = PdfReader(pdf_info["path"])
        text = ""
        pages = reader.pages if full else reader.pages[:5]
        
        for page in pages:
            text += page.extract_text() or ""
        
        if len(text) > 3000:
            text = text[:3000] + "...\n\n[Use 'details {key}' for full content]"
        
        return f"📄 {pdf_info['name']}\n\n{text}"
    except Exception as e:
        return f"[Error reading PDF '{key}': {str(e)}]"

def load_course_content(key: str):
    path = COURSE_FILES.get(key)
    if not path or not os.path.exists(path):
        return None
    
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    if len(content) > 3000:
        content = content[:3000] + "\n\n[... truncated for brevity]"
    
    return f"🎓 Course File: {os.path.basename(path)}\n\n{content}"

def find_course_match(user_message: str):
    msg = user_message.lower()
    for key in COURSE_FILES.keys():
        if any(part in msg for part in key.lower().split('-')):
            return key
    return None

# --- Memory Management ---
def load_memory():
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Memory corrupted, resetting.")
    
    print("💾 Creating new memory file.")
    return [{"role": "system", "content": kanbanotion_context}]

def save_memory():
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(conversation_history, f, indent=2, ensure_ascii=False)

conversation_history = load_memory()

# --- Chat Endpoints ---
@router.post("/chat/reset")
async def reset_chat():
    global conversation_history
    conversation_history = [{"role": "system", "content": kanbanotion_context}]
    save_memory()
    print("🔄 Memory reset.")
    return {"status": "ok", "message": "Chat memory reset."}

@router.post("/chat")
async def handle_chat(request: ChatRequest):
    global conversation_history
    user_message = request.message.strip()
    user_message_lower = user_message.lower()
    
    # PDF detection
    if any(k in user_message_lower for k in PDF_FILES.keys()):
        pdf_key = next(k for k in PDF_FILES if k in user_message_lower)
        pdf_text = extract_pdf_text(pdf_key, full=("full" in user_message_lower or "details" in user_message_lower))
        
        if pdf_text:
            conversation_history.append({"role": "user", "content": f"{user_message}\n\n{pdf_text}"})
            ai_response = ai_client.chat_completion(messages=conversation_history)
            conversation_history.append({"role": "assistant", "content": ai_response})
            save_memory()
            return {"reply": ai_response}
    
    # Course detection
    course_key = find_course_match(user_message_lower)
    if course_key:
        course_content = load_course_content(course_key)
        if course_content:
            conversation_history.append({"role": "user", "content": f"{user_message}\n\n{course_content}"})
            ai_response = ai_client.chat_completion(messages=conversation_history)
            conversation_history.append({"role": "assistant", "content": ai_response})
            save_memory()
            return {"reply": ai_response}
    
    # Default chat
    conversation_history.append({"role": "user", "content": user_message})
    ai_response = ai_client.chat_completion(messages=conversation_history)
    conversation_history.append({"role": "assistant", "content": ai_response})
    save_memory()
    
    return {"reply": ai_response}




# backend/chat/chat_api.py || v4.5 – Blueprint, PDF & Course Auto-Integration

# from fastapi import APIRouter
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json, re
# from PyPDF2 import PdfReader

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
# PDF_DIR = os.path.join(BASE_DIR, "pdfs")
# COURSE_DIR = os.path.join(BASE_DIR, "courses")

# print(f"📂 BASE_DIR: {BASE_DIR}")
# print(f"📂 MEMORY_PATH: {MEMORY_PATH}")
# print(f"📂 BLUEPRINT_DIR: {BLUEPRINT_DIR}")
# print(f"📂 PDF_DIR: {PDF_DIR}")
# print(f"📂 COURSE_DIR: {COURSE_DIR}")

# # --- Blueprint Loader ---
# def load_blueprint_files():
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.endswith(".txt"):
#                 key = filename.replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
#     return files

# # --- PDF Loader ---
# def load_pdf_files():
#     files = {}
#     if os.path.exists(PDF_DIR):
#         for i, filename in enumerate(sorted(os.listdir(PDF_DIR)), 1):
#             if filename.lower().endswith(".pdf"):
#                 key = f"pdf-{i:02d}"
#                 files[key] = {"path": os.path.join(PDF_DIR, filename), "name": filename}
#     print(f"📄 Loaded {len(files)} PDFs: {', '.join(files.keys()) or 'none'}")
#     return files

# # --- Course Loader (Recursive) ---
# def load_course_files():
#     files = {}
#     if os.path.exists(COURSE_DIR):
#         for root, _, filenames in os.walk(COURSE_DIR):
#             for filename in filenames:
#                 if filename.endswith((".js", ".txt", ".md", ".html")):
#                     rel_path = os.path.relpath(os.path.join(root, filename), COURSE_DIR)
#                     key = f"course-{rel_path.replace(os.sep, '-')}"
#                     files[key] = os.path.join(root, filename)
#     print(f"🎓 Loaded {len(files)} course files: {', '.join(list(files.keys())[:6])}...")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()
# PDF_FILES = load_pdf_files()
# COURSE_FILES = load_course_files()

# # --- Load Context ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
#     resource_list = "\n\n=== AVAILABLE RESOURCES ===\n"
#     if BLUEPRINT_FILES:
#         resource_list += f"📘 Blueprints: {', '.join(BLUEPRINT_FILES.keys())}\n"
#     if PDF_FILES:
#         resource_list += f"📄 PDFs: {', '.join([v['name'] for v in PDF_FILES.values()])}\n"
#     if COURSE_FILES:
#         resource_list += f"🎓 Courses: {len(COURSE_FILES)} files in total\n"
#     kanbanotion_context += "\n" + resource_list
#     print("✅ Kanban context loaded successfully.")
# except FileNotFoundError:
#     kanbanotion_context = "You are Koby, a development assistant for Robyn."
#     print("❌ Kanban context missing; using fallback.")

# # --- Helpers ---
# def extract_pdf_text(key: str, full=False):
#     pdf_info = PDF_FILES.get(key)
#     if not pdf_info: return None
#     try:
#         reader = PdfReader(pdf_info["path"])
#         text = ""
#         pages = reader.pages if full else reader.pages[:5]
#         for page in pages:
#             text += page.extract_text() or ""
#         if len(text) > 3000:
#             text = text[:3000] + "...\n\n[Use 'details {key}' for full content]"
#         return f"📄 {pdf_info['name']}\n\n{text}"
#     except Exception as e:
#         return f"[Error reading PDF '{key}': {str(e)}]"

# def load_course_content(key: str):
#     path = COURSE_FILES.get(key)
#     if not path or not os.path.exists(path):
#         return None
#     with open(path, "r", encoding="utf-8", errors="ignore") as f:
#         content = f.read()
#     if len(content) > 3000:
#         content = content[:3000] + "\n\n[... truncated for brevity]"
#     return f"🎓 Course File: {os.path.basename(path)}\n\n{content}"

# def find_course_match(user_message: str):
#     msg = user_message.lower()
#     for key in COURSE_FILES.keys():
#         if any(part in msg for part in key.lower().split('-')):
#             return key
#     return None

# # --- Memory Management ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         try:
#             with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#                 return json.load(f)
#         except json.JSONDecodeError:
#             pass
#     print("💾 Creating new memory file.")
#     return [{"role": "system", "content": kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Chat Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     global conversation_history
#     conversation_history = [{"role": "system", "content": kanbanotion_context}]
#     save_memory()
#     print("🔄 Memory reset.")
#     return {"status": "ok"}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     global conversation_history
#     user_message = request.message.strip().lower()

#     # PDF detection
#     if any(k in user_message for k in PDF_FILES.keys()):
#         pdf_key = next(k for k in PDF_FILES if k in user_message)
#         pdf_text = extract_pdf_text(pdf_key)
#         if pdf_text:
#             conversation_history.append({"role": "user", "content": f"{user_message}\n\n{pdf_text}"})
#             ai_response = ai_client.chat_completion(messages=conversation_history)
#             conversation_history.append({"role": "assistant", "content": ai_response})
#             save_memory()
#             return {"reply": ai_response}

#     # Course detection
#     course_key = find_course_match(user_message)
#     if course_key:
#         course_content = load_course_content(course_key)
#         if course_content:
#             conversation_history.append({"role": "user", "content": f"{user_message}\n\n{course_content}"})
#             ai_response = ai_client.chat_completion(messages=conversation_history)
#             conversation_history.append({"role": "assistant", "content": ai_response})
#             save_memory()
#             return {"reply": ai_response}

#     # Default chat
#     conversation_history.append({"role": "user", "content": user_message})
#     ai_response = ai_client.chat_completion(messages=conversation_history)
#     conversation_history.append({"role": "assistant", "content": ai_response})
#     save_memory()
#     return {"reply": ai_response}



# backend/chat/api.py || chat memory (v4.5 – Debug + Auto Memory Check)

# from fastapi import APIRouter
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json, re
# from PyPDF2 import PdfReader

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
# PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# # Debug prints
# print("📂 BASE_DIR:", BASE_DIR)
# print("📂 MEMORY_PATH:", MEMORY_PATH)
# print("📂 BLUEPRINT_DIR:", BLUEPRINT_DIR)
# print("📂 PDF_DIR:", PDF_DIR)

# # --- Ensure directories exist ---
# os.makedirs(BLUEPRINT_DIR, exist_ok=True)
# os.makedirs(PDF_DIR, exist_ok=True)

# # --- Blueprint Auto-Loader ---
# def load_blueprint_files():
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.endswith(".txt"):
#                 key = filename.replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(sorted(files.keys())) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- PDF Auto-Loader ---
# def load_pdf_files():
#     files = {}
#     if os.path.exists(PDF_DIR):
#         for i, filename in enumerate(sorted(os.listdir(PDF_DIR)), 1):
#             if filename.lower().endswith(".pdf"):
#                 key = f"pdf-{i:02d}"
#                 files[key] = {'path': os.path.join(PDF_DIR, filename), 'name': filename}
#     print(f"📄 Loaded {len(files)} PDFs: {', '.join(files.keys()) or 'none'}")
#     return files

# PDF_FILES = load_pdf_files()

# # --- Load Context ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
#     resource_list = "\n\n--- AVAILABLE RESOURCES ---\n"
#     if BLUEPRINT_FILES:
#         resource_list += f"Blueprints: {', '.join(BLUEPRINT_FILES.keys())}\n"
#     if PDF_FILES:
#         resource_list += f"PDFs: {', '.join([v['name'] for v in PDF_FILES.values()])}\n"
#     kanbanotion_context += resource_list
#     print("✅ Kanban context loaded successfully.")
# except FileNotFoundError:
#     print("❌ Missing kanbanotion.txt, using fallback context.")
#     kanbanotion_context = "You are Koby, a helpful assistant for Robyn."

# # --- Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#                 print("💾 Memory loaded successfully.")
#                 return data
#             except json.JSONDecodeError:
#                 print("⚠️ Memory corrupted, resetting.")
#     print("💾 Creating new memory file.")
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Extract PDF Text ---
# def extract_pdf_text(key: str, full=False):
#     pdf_info = PDF_FILES.get(key)
#     if not pdf_info: 
#         return f"PDF '{key}' not found."
#     try:
#         reader = PdfReader(pdf_info['path'])
#         text = ""
#         for page in reader.pages[:(None if full else 5)]:
#             text += page.extract_text() + "\n"
#         if len(text) > 3000:
#             text = text[:3000] + "\n[Truncated for preview]"
#         return f"📄 {pdf_info['name']}\n{text}"
#     except Exception as e:
#         return f"[Error reading {pdf_info['name']}: {e}]"

# # --- Chat Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     print("🔄 Chat memory reset.")
#     return {"status": "ok", "message": "Chat memory reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     global conversation_history
#     msg = request.message.strip().lower()

#     # --- Check for PDF ---
#     if "pdf" in msg:
#         for key, pdf in PDF_FILES.items():
#             if key in msg or pdf["name"].lower() in msg:
#                 pdf_text = extract_pdf_text(key, full=("full" in msg))
#                 conversation_history.append({'role': 'user', 'content': pdf_text})
#                 ai_response = ai_client.chat_completion(messages=conversation_history)
#                 conversation_history.append({'role': 'assistant', 'content': ai_response})
#                 save_memory()
#                 return {"reply": ai_response}

#     # --- Check for Blueprint ---
#     if "blueprint" in msg:
#         for key, path in BLUEPRINT_FILES.items():
#             if key in msg:
#                 with open(path, "r", encoding="utf-8") as f:
#                     blueprint_content = f.read()
#                 conversation_history.append({'role': 'user', 'content': blueprint_content})
#                 ai_response = ai_client.chat_completion(messages=conversation_history)
#                 conversation_history.append({'role': 'assistant', 'content': ai_response})
#                 save_memory()
#                 return {"reply": ai_response}

#     # --- Normal AI Chat ---
#     conversation_history.append({'role': 'user', 'content': request.message})
#     ai_response = ai_client.chat_completion(messages=conversation_history)
#     conversation_history.append({'role': 'assistant', 'content': ai_response})
#     save_memory()
#     return {"reply": ai_response}




# backend/chat/api.py || chat memory (v5.0 – Automatic Blueprint & PDF Detection)

# from fastapi import APIRouter, UploadFile
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json, re
# from PyPDF2 import PdfReader

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
# PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# # --- Auto-Loader for Blueprints ---
# def load_blueprint_files():
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for i, filename in enumerate(sorted(os.listdir(BLUEPRINT_DIR)), 1):
#             if filename.lower().endswith(".txt"):
#                 key = f"blueprint-{i:02d}"
#                 files[key] = {
#                     'path': os.path.join(BLUEPRINT_DIR, filename),
#                     'name': filename
#                 }
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- Auto-Loader for PDFs ---
# def load_pdf_files():
#     files = {}
#     if os.path.exists(PDF_DIR):
#         for i, filename in enumerate(sorted(os.listdir(PDF_DIR)), 1):
#             if filename.lower().endswith(".pdf"):
#                 key = f"pdf-{i:02d}"
#                 files[key] = {
#                     'path': os.path.join(PDF_DIR, filename),
#                     'name': filename
#                 }
#     print(f"📄 Loaded {len(files)} PDFs: {', '.join(files.keys()) or 'none'}")
#     return files

# PDF_FILES = load_pdf_files()

# # --- Load Base Context ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
# except FileNotFoundError:
#     print(f"❌ ERROR: '{KANBAN_PATH}' not found. Using default context.")
#     kanbanotion_context = "You are Koby, a helpful AI assistant."

# # Append loaded resources
# resource_list = "\n\n|================ AVAILABLE RESOURCES ================|\n"
# if BLUEPRINT_FILES:
#     resource_list += f"\n📘 Blueprints available: {', '.join([v['name'] for v in BLUEPRINT_FILES.values()])}"
# if PDF_FILES:
#     resource_list += f"\n📄 PDFs available: {', '.join([v['name'] for v in PDF_FILES.values()])}"
# kanbanotion_context += resource_list

# # --- Helper: Load Blueprint Content ---
# def get_blueprint_content(key: str):
#     info = BLUEPRINT_FILES.get(key)
#     if not info or not os.path.exists(info['path']):
#         return None
#     with open(info['path'], "r", encoding="utf-8") as f:
#         content = f.read()
#     if len(content) > 4000:
#         return content[:4000] + "\n\n[... content truncated for brevity]"
#     return content

# # --- Helper: Extract PDF Text ---
# def extract_pdf_text(key: str, full=False):
#     info = PDF_FILES.get(key)
#     if not info or not os.path.exists(info['path']):
#         return None
#     try:
#         reader = PdfReader(info['path'])
#         text = ""
#         pages = reader.pages if full else reader.pages[:5]
#         for page in pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n"
#         if len(text) > 3000:
#             text = text[:3000] + "\n\n[Use 'details {key}' for full content]"
#         return f"📄 PDF: {info['name']}\n\n{text}"
#     except Exception as e:
#         return f"[Error reading PDF '{key}': {str(e)}]"

# # --- Helper: Match Blueprint by Number or Keyword ---
# def match_blueprint(user_message: str):
#     user_lower = user_message.lower()
#     # Match number: blueprint-01, 01
#     match = re.search(r'blueprint[- ]?(\d+)', user_lower)
#     if match:
#         num = match.group(1).zfill(2)
#         for key in BLUEPRINT_FILES.keys():
#             if num in key:
#                 return key
#     # Match keyword
#     for key, info in BLUEPRINT_FILES.items():
#         if info['name'].lower() in user_lower:
#             return key
#     return None

# # --- Helper: Match PDF by Number or Keyword ---
# def match_pdf(user_message: str):
#     user_lower = user_message.lower()
#     # Match number: pdf-01, 01
#     match = re.search(r'pdf[- ]?(\d+)', user_lower)
#     if match:
#         num = match.group(1).zfill(2)
#         for key in PDF_FILES.keys():
#             if num in key:
#                 return key
#     # Match keyword in filename
#     for key, info in PDF_FILES.items():
#         if info['name'].lower() in user_lower:
#             return key
#     return None

# # --- Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         try:
#             with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#                 return json.load(f)
#         except json.JSONDecodeError:
#             print("⚠️ Memory corrupted. Starting fresh.")
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Summarize History ---
# MAX_HISTORY = 30
# SUMMARY_TRIGGER = 20
# def summarize_history():
#     global conversation_history
#     old_msgs = conversation_history[:-10]
#     prompt = "Summarize in under 100 words: " + str(old_msgs)
#     summary = ai_client.chat_completion([
#         {"role": "system", "content": "You are a summarizing assistant."},
#         {"role": "user", "content": prompt}
#     ])
#     conversation_history = [
#         {'role': 'system', 'content': kanbanotion_context},
#         {'role': 'assistant', 'content': f"Summary so far: {summary}"}
#     ] + conversation_history[-10:]
#     save_memory()

# # --- API Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     print("🔄 Chat memory reset.")
#     return {"status": "ok", "message": "Conversation reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     global conversation_history
#     user_message = request.message.strip()
#     user_lower = user_message.lower()

#     # --- Blueprint Handling ---
#     blueprint_key = match_blueprint(user_message)
#     if blueprint_key:
#         content = get_blueprint_content(blueprint_key)
#         if content:
#             enriched = f"{user_message}\n\n[System note: Blueprint '{blueprint_key}' content below]\n\n{content}"
#             conversation_history.append({'role': 'user', 'content': enriched})
#             try:
#                 response = ai_client.chat_completion(messages=conversation_history)
#                 conversation_history.append({'role': 'assistant', 'content': response})
#                 save_memory()
#                 return {"reply": response}
#             except Exception as e:
#                 conversation_history.pop()
#                 return {"error": f"AI client error: {str(e)}"}, 500

#     # --- PDF Handling ---
#     pdf_key = match_pdf(user_message)
#     if pdf_key:
#         full = "details" in user_lower or "full" in user_lower
#         pdf_text = extract_pdf_text(pdf_key, full)
#         if pdf_text:
#             enriched = f"{user_message}\n\n[System note: PDF '{pdf_key}' content below]\n\n{pdf_text}"
#             conversation_history.append({'role': 'user', 'content': enriched})
#             try:
#                 response = ai_client.chat_completion(messages=conversation_history)
#                 conversation_history.append({'role': 'assistant', 'content': response})
#                 save_memory()
#                 return {"reply": response}
#             except Exception as e:
#                 conversation_history.pop()
#                 return {"error": f"AI client error: {str(e)}"}, 500

#     # --- Normal AI Chat ---
#     conversation_history.append({'role': 'user', 'content': user_message})
#     try:
#         if len(conversation_history) > SUMMARY_TRIGGER:
#             summarize_history()
#         response = ai_client.chat_completion(messages=conversation_history)
#         conversation_history.append({'role': 'assistant', 'content': response})
#         if len(conversation_history) > MAX_HISTORY:
#             conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY:]
#         save_memory()
#         return {"reply": response}
#     except Exception as e:
#         conversation_history.pop()
#         return {"error": f"AI client error: {str(e)}"}, 500




# backend/chat/api.py || chat memory (v4.5 – Corrected Blueprint & PDF Integration)

# from fastapi import APIRouter, UploadFile
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json, re
# from PyPDF2 import PdfReader

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
# PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# # --- Blueprint Auto-Loader ---
# def load_blueprint_files():
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.startswith("blueprint-") and filename.endswith(".txt"):
#                 key = filename.replace("blueprint-", "").replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(sorted(files.keys())) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- PDF Auto-Loader (with numbered prefix) ---
# def load_pdf_files():
#     files = {}
#     if os.path.exists(PDF_DIR):
#         for i, filename in enumerate(sorted(os.listdir(PDF_DIR)), 1):
#             if filename.lower().endswith(".pdf"):
#                 key = f"pdf-{i:02d}"
#                 files[key] = {
#                     'path': os.path.join(PDF_DIR, filename),
#                     'name': filename
#                 }
#     print(f"📄 Loaded {len(files)} PDFs: {', '.join(files.keys()) or 'none'}")
#     return files

# PDF_FILES = load_pdf_files()

# # --- Load Context ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()

#     # Auto-append available resources
#     resource_list = "\n\n|================================================================|"
#     resource_list += "\n<============= ::: AVAILABLE RESOURCES ::: =============>"
#     resource_list += "\n|================================================================|\n"

#     if BLUEPRINT_FILES:
#         resource_list += f"\n📘 Blueprints available: {', '.join(sorted(BLUEPRINT_FILES.keys()))}"
#     if PDF_FILES:
#         pdf_list = [f"{k} ({v['name']})" for k, v in PDF_FILES.items()]
#         resource_list += f"\n📄 PDFs available: {', '.join(pdf_list)}"

#     resource_list += "\n\nWhen Robyn asks about blueprints or PDFs, you already have access to them through the system.\n"
#     kanbanotion_context += resource_list
#     print(f"✅ Loaded '{KANBAN_PATH}' with {len(BLUEPRINT_FILES)} blueprints and {len(PDF_FILES)} PDFs")

# except FileNotFoundError:
#     print(f"❌ ERROR: '{KANBAN_PATH}' not found. Using default context.")
#     kanbanotion_context = "You are Koby, a helpful assistant and expert in JS and Python development for Robyn."

# # --- Helper: Load Blueprint ---
# def get_blueprint_content(topic: str) -> str:
#     path = BLUEPRINT_FILES.get(topic)
#     if not path or not os.path.exists(path):
#         return None
#     with open(path, "r", encoding="utf-8") as f:
#         content = f.read()
#     if len(content) > 4000:
#         return content[:4000] + "\n\n[... content truncated for brevity]"
#     return content

# # --- Helper: Extract PDF Text ---
# def extract_pdf_text(key: str, full: bool = False) -> str:
#     pdf_info = PDF_FILES.get(key)
#     if not pdf_info or not os.path.exists(pdf_info['path']):
#         return None
#     try:
#         reader = PdfReader(pdf_info['path'])
#         text = ""
#         if full:
#             for page in reader.pages:
#                 text += page.extract_text() + "\n"
#         else:
#             for page in reader.pages[:5]:
#                 text += page.extract_text() + "\n"
#         if len(text) > 3000:
#             text = text[:3000] + f"...\n\n[Use 'details {key}' for full content]"
#         return f"📄 PDF: {pdf_info['name']}\n\n{text}"
#     except Exception as e:
#         return f"[Error reading PDF '{key}': {str(e)}]"

# # --- Helper: Smart Blueprint Matching ---
# def find_blueprint_match(user_message: str):
#     user_lower = user_message.lower()
#     match = re.search(r'blueprint[- ]?(\d+)', user_lower)
#     if match:
#         num = match.group(1).zfill(2)
#         for key in BLUEPRINT_FILES.keys():
#             if num in key:
#                 return key
#     for key in BLUEPRINT_FILES.keys():
#         if key in user_lower:
#             return key
#     return None

# # --- Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#             try:
#                 return json.load(f)
#             except json.JSONDecodeError:
#                 print("⚠️ Memory file corrupted. Starting fresh.")
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Smart Context Management ---
# MAX_HISTORY = 30
# SUMMARY_TRIGGER = 20

# def summarize_history():
#     global conversation_history
#     print("🧠 Summarizing old memory for efficiency...")
#     old_messages = conversation_history[:-10]
#     prompt = "Summarize this conversation in under 100 words, keeping the key goals and decisions: " + str(old_messages)
#     summary = ai_client.chat_completion([
#         {"role": "system", "content": "You are a summarizing assistant."},
#         {"role": "user", "content": prompt}
#     ])
#     conversation_history = [
#         {'role': 'system', 'content': kanbanotion_context},
#         {'role': 'assistant', 'content': f"Summary so far: {summary}"}
#     ] + conversation_history[-10:]
#     save_memory()

# # --- API Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     print("🔄 Chat memory reset.")
#     return {"status": "ok", "message": "Conversation has been reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     global conversation_history
#     user_message = request.message.strip()
#     user_lower = user_message.lower()

#     # --- Blueprint Request ---
#     if "blueprint" in user_lower and BLUEPRINT_FILES:
#         topic = find_blueprint_match(user_message)
#         if topic:
#             blueprint_content = get_blueprint_content(topic)
#             if blueprint_content:
#                 enriched_message = f"{user_message}\n\n[System note: Blueprint '{topic}' content below for reference]\n\n{blueprint_content}"
#                 conversation_history.append({'role': 'user', 'content': enriched_message})
#                 try:
#                     ai_response = ai_client.chat_completion(messages=conversation_history)
#                     conversation_history.append({'role': 'assistant', 'content': ai_response})
#                     save_memory()
#                     return {"reply": ai_response}
#                 except Exception as e:
#                     conversation_history.pop()
#                     return {"error": f"AI client error: {str(e)}"}, 500
#             else:
#                 enriched_message = f"{user_message}\n\n[System note: Blueprint '{topic}' was requested but not found]"
#         else:
#             enriched_message = f"{user_message}\n\n[System note: Available blueprints are: {', '.join(sorted(BLUEPRINT_FILES.keys()))}]"
#         conversation_history.append({'role': 'user', 'content': enriched_message})
#         try:
#             ai_response = ai_client.chat_completion(messages=conversation_history)
#             conversation_history.append({'role': 'assistant', 'content': ai_response})
#             save_memory()
#             return {"reply": ai_response}
#         except Exception as e:
#             conversation_history.pop()
#             return {"error": f"AI client error: {str(e)}"}, 500

#     # --- PDF Request ---
#     pdf_key = next((k for k in PDF_FILES.keys() if k in user_lower), None)
#     if pdf_key:
#         full_content = "details" in user_lower or "full" in user_lower
#         pdf_text = extract_pdf_text(pdf_key, full=full_content)
#         if pdf_text:
#             enriched_message = f"{user_message}\n\n[System note: PDF content below for reference]\n\n{pdf_text}"
#             conversation_history.append({'role': 'user', 'content': enriched_message})
#             try:
#                 ai_response = ai_client.chat_completion(messages=conversation_history)
#                 conversation_history.append({'role': 'assistant', 'content': ai_response})
#                 save_memory()
#                 return {"reply": ai_response}
#             except Exception as e:
#                 conversation_history.pop()
#                 return {"error": f"AI client error: {str(e)}"}, 500

#     # --- Normal AI Chat Flow ---
#     conversation_history.append({'role': 'user', 'content': user_message})
#     try:
#         if len(conversation_history) > SUMMARY_TRIGGER:
#             summarize_history()
#         ai_response = ai_client.chat_completion(messages=conversation_history)
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         if len(conversation_history) > MAX_HISTORY:
#             conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY:]
#         save_memory()
#         return {"reply": ai_response}
#     except Exception as e:
#         conversation_history.pop()
#         return {"error": f"AI client error: {str(e)}"}, 500




# backend/chat/api.py || chat memory (v4.4 – PDF + Blueprint Loader)

# from fastapi import APIRouter, UploadFile
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json
# from PyPDF2 import PdfReader

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
# PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# # --- Blueprint Auto-Loader ---
# def load_blueprint_files():
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.startswith("blueprint-") and filename.endswith(".txt"):
#                 key = filename.replace("blueprint-", "").replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- PDF Auto-Loader (with numbered prefix) ---
# def load_pdf_files():
#     files = {}
#     if os.path.exists(PDF_DIR):
#         for i, filename in enumerate(sorted(os.listdir(PDF_DIR)), 1):
#             if filename.lower().endswith(".pdf"):
#                 key = f"pdf-{i:02d}"
#                 files[key] = os.path.join(PDF_DIR, filename)
#     print(f"📄 Loaded {len(files)} PDFs: {', '.join(files.keys()) or 'none'}")
#     return files

# PDF_FILES = load_pdf_files()

# # --- Load Context ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
#     print(f"✅ Loaded '{KANBAN_PATH}'")
# except FileNotFoundError:
#     print(f"❌ ERROR: '{KANBAN_PATH}' not found. Using default context.")
#     kanbanotion_context = "You are Koby, a helpful assistant and expert in JS and Python development for Robyn."

# # --- Helper: Load Blueprint ---
# def get_blueprint_content(topic: str) -> str:
#     path = BLUEPRINT_FILES.get(topic)
#     if not path or not os.path.exists(path):
#         return f"[Blueprint '{topic}' not found...]"
#     with open(path, "r", encoding="utf-8") as f:
#         content = f.read()
#     return content[:3000] + "\n\n[... truncated]" if len(content) > 3000 else content

# # --- Helper: Load PDF Summary ---
# def get_pdf_summary(key: str) -> str:
#     path = PDF_FILES.get(key)
#     if not path or not os.path.exists(path):
#         return f"[PDF '{key}' not found...]"
#     try:
#         reader = PdfReader(path)
#         text = ""
#         for page in reader.pages[:3]:  # first 3 pages for summary
#             text += page.extract_text() + "\n"
#         return f"[PDF Summary: first pages]\n{text[:1000]}...\n(Use 'details {key}' for more)"
#     except Exception as e:
#         return f"[Error reading PDF '{key}': {str(e)}]"

# # --- Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#             try:
#                 return json.load(f)
#             except json.JSONDecodeError:
#                 pass
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Smart Context Management ---
# MAX_HISTORY = 30
# SUMMARY_TRIGGER = 20

# def summarize_history():
#     global conversation_history
#     old_messages = conversation_history[:-10]
#     prompt = "Summarize this conversation in under 100 words, keeping the key goals and decisions: " + str(old_messages)
#     summary = ai_client.chat_completion([
#         {"role": "system", "content": "You are a summarizing assistant."},
#         {"role": "user", "content": prompt}
#     ])
#     conversation_history = [
#         {'role': 'system', 'content': kanbanotion_context},
#         {'role': 'assistant', 'content': f"Summary so far: {summary}"}
#     ] + conversation_history[-10:]
#     save_memory()

# # --- API Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     return {"status": "ok", "message": "Conversation has been reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     global conversation_history
#     user_message = request.message.strip()
#     user_lower = user_message.lower()

#     # Blueprint requests
#     if ("blueprint" in user_lower or "show me" in user_lower) and BLUEPRINT_FILES:
#         topic = next((k for k in BLUEPRINT_FILES.keys() if k in user_lower), None)
#         if topic:
#             text = get_blueprint_content(topic)
#             ai_response = f"📘 Blueprint: {topic.upper()}\n\n{text}"
#         else:
#             ai_response = f"Yes, of course! Which blueprint would you like? Available: {', '.join(BLUEPRINT_FILES.keys())}"
#         conversation_history.append({'role': 'user', 'content': user_message})
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         save_memory()
#         return {"reply": ai_response}

#     # PDF requests
#     if any(k in user_lower for k in PDF_FILES.keys()):
#         key = next((k for k in PDF_FILES.keys() if k in user_lower), None)
#         if "details" in user_lower:
#             # TODO: future: send full PDF in chunks
#             ai_response = f"Full details for {key} can be retrieved (currently limited to summary)."
#         else:
#             ai_response = get_pdf_summary(key)
#         conversation_history.append({'role': 'user', 'content': user_message})
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         save_memory()
#         return {"reply": ai_response}

#     # Normal AI chat flow
#     conversation_history.append({'role': 'user', 'content': user_message})
#     try:
#         if len(conversation_history) > SUMMARY_TRIGGER:
#             summarize_history()
#         ai_response = ai_client.chat_completion(messages=conversation_history)
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         if len(conversation_history) > MAX_HISTORY:
#             conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY:]
#         save_memory()
#         return {"reply": ai_response}
#     except Exception as e:
#         conversation_history.pop()
#         return {"error": f"AI client error: {str(e)}"}, 500



# backend/chat/api.py || chat memory (v.4.3 – Blueprint + PDF Loader)

# from fastapi import APIRouter, UploadFile
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")
# PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# # --- Load Context File ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
#     print(f"✅ Loaded '{KANBAN_PATH}'")
# except FileNotFoundError:
#     print(f"❌ ERROR: '{KANBAN_PATH}' not found. Using default context.")
#     kanbanotion_context = "You are Koby, a helpful assistant for Robyn."

# # --- Blueprint Auto-Loader ---
# def load_blueprint_files():
#     """Scan the blueprints folder and map available files."""
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.startswith("blueprint-") and filename.endswith(".txt"):
#                 key = filename.replace("blueprint-", "").replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- PDF Auto-Loader ---
# from PyPDF2 import PdfReader

# def load_pdf_texts():
#     """Load all PDFs from folder and store as text chunks."""
#     pdf_texts = {}
#     if os.path.exists(PDF_DIR):
#         for filename in os.listdir(PDF_DIR):
#             if filename.lower().endswith(".pdf"):
#                 path = os.path.join(PDF_DIR, filename)
#                 try:
#                     reader = PdfReader(path)
#                     text = ""
#                     for page in reader.pages:
#                         page_text = page.extract_text()
#                         if page_text:
#                             text += page_text + "\n"
#                     pdf_texts[filename] = text[:3000] + ("\n\n[... truncated]" if len(text) > 3000 else "")
#                     print(f"📄 Loaded PDF: {filename}")
#                 except Exception as e:
#                     print(f"❌ Error loading PDF '{filename}': {e}")
#     return pdf_texts

# PDF_TEXTS = load_pdf_texts()

# # --- Helper: Load Blueprint Content ---
# def get_blueprint_content(topic: str) -> str:
#     path = BLUEPRINT_FILES.get(topic)
#     if not path or not os.path.exists(path):
#         print(f"⚠️ Blueprint '{topic}' requested but not found.")
#         return f"[Blueprint '{topic}' not found...]"
#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             content = f.read()
#         if len(content) > 3000:
#             return content[:3000] + "\n\n[... truncated]"
#         return content
#     except Exception as e:
#         print(f"❌ Error loading blueprint '{topic}': {e}")
#         return f"[Error loading blueprint: {str(e)}]"

# # --- Load/Save Persistent Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#                 print("💾 Loaded persistent chat memory.")
#                 return data
#             except json.JSONDecodeError:
#                 print("⚠️ Memory file corrupted. Starting fresh.")
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Smart Context Management ---
# MAX_HISTORY = 30
# SUMMARY_TRIGGER = 20

# def summarize_history():
#     """Compress older conversation context into a summary."""
#     print("🧠 Summarizing old memory for efficiency...")
#     global conversation_history

#     old_messages = conversation_history[:-10]
#     prompt = "Summarize this conversation in under 100 words, keeping the key goals and decisions: " + str(old_messages)

#     summary = ai_client.chat_completion([
#         {"role": "system", "content": "You are a summarizing assistant."},
#         {"role": "user", "content": prompt}
#     ])

#     conversation_history = [
#         {'role': 'system', 'content': kanbanotion_context},
#         {'role': 'assistant', 'content': f"Summary so far: {summary}"}
#     ] + conversation_history[-10:]
#     save_memory()

# # --- API Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     """Reset conversation memory (PDFs and blueprints remain)."""
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     print("🔄 Chat memory reset.")
#     return {"status": "ok", "message": "Conversation has been reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     """Handles chat messages and returns AI-generated response."""
#     global conversation_history
#     user_message = request.message.strip()
#     user_lower = user_message.lower()

#     # --- Detect Blueprint Requests ---
#     if ("blueprint" in user_lower or "show me" in user_lower or "pull up" in user_lower) and BLUEPRINT_FILES:
#         topic = next((key for key in BLUEPRINT_FILES.keys() if key in user_lower), None)
#         if topic:
#             blueprint_text = get_blueprint_content(topic)
#             ai_response = f"📘 Blueprint: {topic.upper()}\n\n{blueprint_text}"
#         else:
#             ai_response = f"Yes, of course! Which blueprint would you like? Available: {', '.join(BLUEPRINT_FILES.keys())}"
#         conversation_history.append({'role': 'user', 'content': user_message})
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         save_memory()
#         return {"reply": ai_response}

#     # --- Detect PDF Requests ---
#     if "pdf" in user_lower or "document" in user_lower:
#         # Show list if multiple PDFs
#         if PDF_TEXTS:
#             pdf_names = list(PDF_TEXTS.keys())
#             ai_response = f"📄 I have access to the following PDFs:\n" + "\n".join(pdf_names)
#         else:
#             ai_response = "⚠️ No PDFs loaded yet."
#         conversation_history.append({'role': 'user', 'content': user_message})
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         save_memory()
#         return {"reply": ai_response}

#     # --- Normal AI Chat Flow ---
#     conversation_history.append({'role': 'user', 'content': user_message})
#     try:
#         if len(conversation_history) > SUMMARY_TRIGGER:
#             summarize_history()

#         ai_response = ai_client.chat_completion(messages=conversation_history)
#         conversation_history.append({'role': 'assistant', 'content': ai_response})

#         if len(conversation_history) > MAX_HISTORY:
#             conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY:]

#         save_memory()
#         return {"reply": ai_response}

#     except Exception as e:
#         print(f"❌ Error communicating with AI client: {e}")
#         conversation_history.pop()
#         return {"error": "An internal error occurred while processing the request."}, 500



# backend/chat/api.py || chat memory (v.4.3 – PDF + Blueprint Loader)


# from fastapi import APIRouter, UploadFile
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json
# from PyPDF2 import PdfReader

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")

# # --- Blueprint Auto-Loader ---
# def load_blueprint_files():
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.startswith("blueprint-") and filename.endswith(".txt"):
#                 key = filename.replace("blueprint-", "").replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- Load Context File ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
#     print(f"✅ Loaded '{KANBAN_PATH}'")
# except FileNotFoundError:
#     print(f"❌ ERROR: '{KANBAN_PATH}' not found. Using default context.")
#     kanbanotion_context = "You are Koby, a helpful assistant and expert in JS and Python development for Robyn."

# # --- Helper: Load Blueprint Content ---
# def get_blueprint_content(topic: str) -> str:
#     path = BLUEPRINT_FILES.get(topic)
#     if not path or not os.path.exists(path):
#         print(f"⚠️ Blueprint '{topic}' requested but not found.")
#         return f"[Blueprint '{topic}' not found...]"
#     try:
#         print(f"📘 Loading blueprint: {topic} from {path}")
#         with open(path, "r", encoding="utf-8") as f:
#             content = f.read()
#         if len(content) > 3000:
#             return content[:3000] + "\n\n[... truncated]"
#         return content
#     except Exception as e:
#         print(f"❌ Error loading blueprint '{topic}': {e}")
#         return f"[Error loading blueprint: {str(e)}]"

# # --- PDF Helpers ---
# CHUNK_SIZE = 2000  # characters per chunk

# def extract_pdf_text(pdf_file) -> str:
#     reader = PdfReader(pdf_file)
#     text = ""
#     for page in reader.pages:
#         page_text = page.extract_text() or ""
#         text += page_text + "\n"
#     return text

# def chunk_text(text, chunk_size=CHUNK_SIZE):
#     chunks = []
#     for i in range(0, len(text), chunk_size):
#         chunks.append(text[i:i+chunk_size])
#     return chunks

# def summarize_chunks(chunks):
#     summaries = []
#     for chunk in chunks:
#         summary = ai_client.chat_completion([
#             {"role": "system", "content": "You are a summarizing assistant."},
#             {"role": "user", "content": f"Summarize this text concisely:\n{chunk}"}
#         ])
#         summaries.append(summary)
#     return "\n".join(summaries)

# # --- Load/Save Persistent Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#                 print("💾 Loaded persistent chat memory.")
#                 return data
#             except json.JSONDecodeError:
#                 print("⚠️ Memory file corrupted. Starting fresh.")
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Smart Context Management ---
# MAX_HISTORY = 30
# SUMMARY_TRIGGER = 20

# def summarize_history():
#     print("🧠 Summarizing old memory for efficiency...")
#     global conversation_history

#     old_messages = conversation_history[:-10]
#     prompt = "Summarize this conversation in under 100 words, keeping the key goals and decisions: " + str(old_messages)

#     summary = ai_client.chat_completion([
#         {"role": "system", "content": "You are a summarizing assistant."},
#         {"role": "user", "content": prompt}
#     ])

#     conversation_history = [
#         {'role': 'system', 'content': kanbanotion_context},
#         {'role': 'assistant', 'content': f"Summary so far: {summary}"}
#     ] + conversation_history[-10:]
#     save_memory()

# # --- API Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     print("🔄 Chat memory reset.")
#     return {"status": "ok", "message": "Conversation has been reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest, pdf: UploadFile = None):
#     """Handles chat messages and optional PDF uploads."""
#     global conversation_history
#     user_message = request.message.strip()
#     user_lower = user_message.lower()

#     # --- Detect Blueprint Requests ---
#     if ("blueprint" in user_lower or "show me" in user_lower or "pull up" in user_lower) and BLUEPRINT_FILES:
#         topic = next((key for key in BLUEPRINT_FILES.keys() if key in user_lower), None)
#         if topic:
#             blueprint_text = get_blueprint_content(topic)
#             ai_response = f"📘 Blueprint: {topic.upper()}\n\n{blueprint_text}"
#         else:
#             ai_response = f"Yes, of course! Which blueprint would you like? Available: {', '.join(BLUEPRINT_FILES.keys())}"
#         conversation_history.append({'role': 'user', 'content': user_message})
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         save_memory()
#         return {"reply": ai_response}

#     # --- Process PDF if uploaded ---
#     pdf_text = ""
#     if pdf:
#         pdf_text = extract_pdf_text(pdf.file)
#         if len(pdf_text) > CHUNK_SIZE:
#             chunks = chunk_text(pdf_text)
#             pdf_text = summarize_chunks(chunks)

#     # --- Normal AI Chat Flow ---
#     conversation_history.append({'role': 'user', 'content': user_message})
#     if pdf_text:
#         conversation_history.append({'role': 'system', 'content': f"Reference PDF content:\n{pdf_text}"})

#     try:
#         if len(conversation_history) > SUMMARY_TRIGGER:
#             summarize_history()

#         ai_response = ai_client.chat_completion(messages=conversation_history)
#         conversation_history.append({'role': 'assistant', 'content': ai_response})

#         if len(conversation_history) > MAX_HISTORY:
#             conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY:]

#         save_memory()
#         return {"reply": ai_response}

#     except Exception as e:
#         print(f"❌ Error communicating with AI client: {e}")
#         conversation_history.pop()  # Remove user message that caused error
#         return {"error": "An internal error occurred while processing the request."}, 500








# backend/chat/api.py || chat memory (v.4.2 – Dynamic Blueprint Loader)

# from fastapi import APIRouter
# from pydantic import BaseModel
# from backend.services.ai_client import get_ai_client
# import os, json

# router = APIRouter()

# # --- SETUP ---
# class ChatRequest(BaseModel):
#     message: str

# ai_client = get_ai_client()

# # --- Paths ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KANBAN_PATH = os.path.join(BASE_DIR, "kanbanotion.txt")
# MEMORY_PATH = os.path.join(BASE_DIR, "memory.json")
# BLUEPRINT_DIR = os.path.join(BASE_DIR, "blueprints")

# # --- Blueprint Auto-Loader ---
# def load_blueprint_files():
#     """Scan the blueprints folder and map available files."""
#     files = {}
#     if os.path.exists(BLUEPRINT_DIR):
#         for filename in os.listdir(BLUEPRINT_DIR):
#             if filename.startswith("blueprint-") and filename.endswith(".txt"):
#                 key = filename.replace("blueprint-", "").replace(".txt", "")
#                 files[key] = os.path.join(BLUEPRINT_DIR, filename)
#     print(f"📘 Loaded {len(files)} blueprints: {', '.join(files.keys()) or 'none'}")
#     return files

# BLUEPRINT_FILES = load_blueprint_files()

# # --- Load Context File ---
# try:
#     with open(KANBAN_PATH, "r", encoding="utf-8") as f:
#         kanbanotion_context = f.read()
#     print(f"✅ Loaded '{KANBAN_PATH}'")
# except FileNotFoundError:
#     print(f"❌ ERROR: '{KANBAN_PATH}' not found. Using default context.")
#     kanbanotion_context = "You are Koby, a helpful assistant and expert in JS and Python development for Robyn."

# # --- Helper: Load Blueprint Content ---
# def get_blueprint_content(topic: str) -> str:
#     path = BLUEPRINT_FILES.get(topic)
#     if not path or not os.path.exists(path):
#         print(f"⚠️ Blueprint '{topic}' requested but not found.")
#         return f"[Blueprint '{topic}' not found...]"
#     try:
#         print(f"📘 Loading blueprint: {topic} from {path}")
#         with open(path, "r", encoding="utf-8") as f:
#             content = f.read()
#         if len(content) > 3000:
#             return content[:3000] + "\n\n[... truncated]"
#         return content
#     except Exception as e:
#         print(f"❌ Error loading blueprint '{topic}': {e}")
#         return f"[Error loading blueprint: {str(e)}]"

# # --- Load/Save Persistent Memory ---
# def load_memory():
#     if os.path.exists(MEMORY_PATH):
#         with open(MEMORY_PATH, "r", encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#                 print("💾 Loaded persistent chat memory.")
#                 return data
#             except json.JSONDecodeError:
#                 print("⚠️ Memory file corrupted. Starting fresh.")
#     return [{'role': 'system', 'content': kanbanotion_context}]

# def save_memory():
#     with open(MEMORY_PATH, "w", encoding="utf-8") as f:
#         json.dump(conversation_history, f, indent=2, ensure_ascii=False)

# conversation_history = load_memory()

# # --- Smart Context Management ---
# MAX_HISTORY = 30
# SUMMARY_TRIGGER = 20

# def summarize_history():
#     """Compress older conversation context into a summary."""
#     print("🧠 Summarizing old memory for efficiency...")
#     global conversation_history

#     old_messages = conversation_history[:-10]
#     prompt = "Summarize this conversation in under 100 words, keeping the key goals and decisions: " + str(old_messages)

#     summary = ai_client.chat_completion([
#         {"role": "system", "content": "You are a summarizing assistant."},
#         {"role": "user", "content": prompt}
#     ])

#     conversation_history = [
#         {'role': 'system', 'content': kanbanotion_context},
#         {'role': 'assistant', 'content': f"Summary so far: {summary}"}
#     ] + conversation_history[-10:]
#     save_memory()

# # --- API Endpoints ---
# @router.post("/chat/reset")
# async def reset_chat():
#     """Reset conversation memory."""
#     global conversation_history
#     conversation_history = [{'role': 'system', 'content': kanbanotion_context}]
#     save_memory()
#     print("🔄 Chat memory reset.")
#     return {"status": "ok", "message": "Conversation has been reset."}

# @router.post("/chat")
# async def handle_chat(request: ChatRequest):
#     """Handles chat messages and returns AI-generated response."""
#     global conversation_history
#     user_message = request.message.strip()
#     user_lower = user_message.lower()

#     # --- Detect Blueprint Requests ---
#     if ("blueprint" in user_lower or "show me" in user_lower or "pull up" in user_lower) and BLUEPRINT_FILES:
#         topic = next((key for key in BLUEPRINT_FILES.keys() if key in user_lower), None)
#         if topic:
#             blueprint_text = get_blueprint_content(topic)
#             ai_response = f"📘 Blueprint: {topic.upper()}\n\n{blueprint_text}"
#         else:
#             ai_response = f"Yes, of course! Which blueprint would you like? Available: {', '.join(BLUEPRINT_FILES.keys())}"
#         conversation_history.append({'role': 'user', 'content': user_message})
#         conversation_history.append({'role': 'assistant', 'content': ai_response})
#         save_memory()
#         return {"reply": ai_response}

#     # --- Normal AI Chat Flow ---
#     conversation_history.append({'role': 'user', 'content': user_message})
#     try:
#         if len(conversation_history) > SUMMARY_TRIGGER:
#             summarize_history()

#         ai_response = ai_client.chat_completion(messages=conversation_history)
#         conversation_history.append({'role': 'assistant', 'content': ai_response})

#         if len(conversation_history) > MAX_HISTORY:
#             conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY:]

#         save_memory()
#         return {"reply": ai_response}

#     except Exception as e:
#         print(f"❌ Error communicating with AI client: {e}")
#         conversation_history.pop()  # Remove user message that caused error
#         return {"error": "An internal error occurred while processing the request."}, 500
