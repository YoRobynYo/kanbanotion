# backend-template (Backend)

FastAPI + Stripe + LangChain backend.

## Quick start
1) cd backend && cp .env.example .env
2) Edit .env (JWT_SECRET, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, OPENAI_API_KEY optional)
3) Create venv and install:
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
4) Run API:
   uvicorn app.main:app --reload --port 8000
5) In another terminal run Stripe webhook:
   stripe login
   stripe listen --forward-to localhost:8000/api/stripe/webhook

Docs: http://localhost:8000/docs

6) ## Features

### Core AI Chat
- `/api/chat` - AI conversation endpoint
- Rate limiting (500 requests/day)
- Ollama (dev) → Groq (prod) switching

### User Management  
- `/api/auth/register` - User registration
- `/api/auth/login` - Authentication
- JWT tokens

### E-commerce (Optional)
- Product catalog
- Order management  
- Stripe payments
- Analytics

### Usage
Start with AI chat only, enable e-commerce features as needed.
