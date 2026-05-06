# GO!CS Product PRD

## 0. Product Name

**GO!CS**

Full meaning:

**Generate Online Customer Service**

Brand sentence:

> GO!CS turns business documents into an accurate, no-hallucination, ready-to-use AI customer service assistant.

Chinese positioning:

> GO!CS 让商家只需上传资料，就能马上生成一个准确、不乱答、可上线的客服 AI。

---

## 1. Product Vision

GO!CS is an upload-first AI customer service generator powered by Logos Data Engine.

The product is not designed as a heavy chatbot SaaS platform at the MVP stage. It is designed as a lightweight AI generation experience where a user can upload company information and immediately test an AI customer service assistant.

The main user feeling should be:

> I uploaded my company information, and GO!CS instantly created a customer service AI for me.

---

## 2. Core Product Philosophy

GO!CS must follow these principles:

1. **Upload first, configure later.**
2. **Users should not need to understand AI.**
3. **The AI must only answer from uploaded business information.**
4. **If the AI is not sure, it must not guess.**
5. **The first useful result must appear as fast as possible.**
6. **The MVP must be light enough to build and launch in one week.**
7. **Accuracy is more important than sounding impressive.**

---

## 3. Target Users

### 3.1 Primary Users

Small and medium business owners who need customer service automation but do not have technical knowledge.

Examples:

- Restaurants
- Beauty salons
- Clinics
- Education centers
- Ecommerce sellers
- Agencies
- Service businesses
- Legal service providers
- Property agents
- Training providers

### 3.2 User Pain Points

Users currently face these problems:

1. They answer the same customer questions repeatedly.
2. They do not have enough manpower for fast replies.
3. They want AI support but do not know how to configure chatbot systems.
4. Existing chatbot builders feel too complicated.
5. Generic AI chatbots may hallucinate or give wrong answers.
6. Businesses want to connect AI to customer channels such as website, Telegram, WhatsApp, and Facebook.

---

## 4. Product Promise

GO!CS promises:

> Upload your information. Generate your AI customer service. Test it instantly. Go live when ready.

The product should communicate three major benefits:

1. **Fast** — generate a working AI customer service assistant quickly.
2. **Accurate** — answers are grounded in uploaded company information.
3. **Simple** — no complex setup, prompt engineering, or technical configuration.

---

## 5. Product Scope

### 5.1 Must Have

The Product must include:

1. Upload-first landing page.
2. File upload and paste text support.
3. Lightweight AI behavior settings.
4. Automatic bot creation.
5. Document processing.
6. Knowledge chunking.
7. AI answer API.
8. Test chat page.
9. Confidence status.
10. Fallback when information is missing.
11. Public chat link.
12. Website widget code.
13. Basic Telegram connection if time allows.

### 5.2 Should Have

These are useful but not critical:

1. Suggested questions generated from uploaded material.
2. Simple conversation history.
3. Simple source preview.
4. Email capture before sharing.
5. Basic human handover message.

### 5.3 Not in Product

Do not build these in the first version:

1. Workspace system.
2. Team permissions.
3. Billing.
4. Full dashboard.
5. Advanced analytics.
6. CRM inbox.
7. Multi-bot management.
8. Complex QA test runner.
9. Full WhatsApp official integration.
10. Full Facebook Messenger integration.
11. Agent marketplace.
12. Fine-tuning system.

---

## 6. Final Product User Flow

```text
1. User opens website.
2. User uploads company document or pastes information.
3. User selects simple AI behavior settings.
4. User clicks "Generate My AI".
5. System automatically creates AI customer service assistant.
6. System processes the uploaded information.
7. User enters Test Chat.
8. User immediately asks questions.
9. User shares link, embeds website widget, or connects Telegram.
```

---

## 7. Page Requirements

## 7.1 Page 1: Upload Landing Page

Route:

```text
/
```

### Purpose

Allow users to upload information and generate an AI customer service assistant immediately.

### Main Headline

```text
Upload your company information. Generate an accurate AI customer service assistant instantly.
```

### Subheadline

```text
GO!CS helps businesses turn FAQs, menus, price lists, service packages, SOPs, and policies into a ready-to-use AI customer service assistant.
```

### Main Components

1. Upload box.
2. Paste text box.
3. AI behavior settings.
4. Business type dropdown.
5. Tone selector.
6. Generate button.

### Upload Box

Supported formats:

```text
PDF, DOCX, website, TXT, FAQ, Price List, Menu, SOP
```

### AI Behavior Settings

Default selected checkboxes:

```text
[x] Only answer using my uploaded information
[x] Avoid guessing when information is unclear
[x] Ask customer to contact human support if unsure
[x] Reply in customer's language automatically
[x] Keep answers short and customer-friendly
```

### Business Type

Optional dropdown:

```text
Auto-detect
Restaurant
Ecommerce
Legal
Education
Beauty
Clinic
Property
Service Business
Others
```

### Tone

Options:

```text
Professional
Friendly
Luxury
Casual
Short and Direct
```

### Main CTA

```text
Generate My AI Customer Service
```

### Acceptance Criteria

1. User can upload a file.
2. User can paste text.
3. User can select basic behavior settings.
4. User can click generate.
5. System creates a generation session.
6. User is redirected to generating page.

---

## 7.2 Page 2: Generating Page

Route:

```text
/generating/:sessionId
```

### Purpose

Show that GO!CS is reading and preparing the AI customer service assistant.

### UI Copy

```text
Creating your AI customer service...

Reading your company information
Understanding your business
Building your AI knowledge base
Preparing customer replies
Setting up your AI assistant
```

### Backend Actions

1. Create bot record.
2. Upload file to storage.
3. Extract text.
4. Split text into knowledge chunks.
5. Generate embeddings.
6. Store knowledge chunks.
7. Generate suggested questions.
8. Prepare default fallback rules.
9. Return bot public token.

### Acceptance Criteria

1. User can see processing progress.
2. System handles file processing errors.
3. Successful generation redirects user to test chat.
4. Failed generation shows clear retry option.

---

## 7.3 Page 3: Test Chat Page

Route:

```text
/bot/:publicToken/test
```

### Purpose

Allow users to immediately test the generated AI customer service assistant.

### Main UI

Left side:

```text
Chat interface
Suggested questions
Message input
```

Right side:

```text
AI Answer Status
Uploaded knowledge summary
AI rules
Share button
```

### Suggested Questions

The system should auto-generate questions such as:

```text
What services do you provide?
What is your pricing?
How can customers contact you?
What are your business hours?
What is your refund policy?
```

### Confidence Display

Use simple labels:

```text
High Confidence
Medium Confidence
Not Enough Information
```

Do not show technical terms such as embedding, chunk score, vector score, or RAG.

### AI Answer Rule

The AI must obey:

```text
Only answer based on uploaded information. If information is missing, say that there is not enough information and suggest contacting a human or uploading more information.
```

### Acceptance Criteria

1. User can ask questions.
2. AI answers from uploaded knowledge.
3. AI does not invent unsupported facts.
4. AI shows simple confidence status.
5. Missing information triggers fallback.
6. User can navigate to share page.

---

## 7.4 Page 4: Share Page

Route:

```text
/bot/:publicToken/share
```

### Purpose

Allow users to make the AI customer service assistant usable by others.

### Options

#### Option 1: Public Chat Link

```text
Copy Link
```

#### Option 2: Website Widget

```text
Copy Widget Code
```

Example:

```html
<script src="https://gocs.ai/widget/PUBLIC_TOKEN.js"></script>
```

#### Option 3: Telegram

```text
Enter Telegram Bot Token
Connect Telegram
```

#### Option 4: WhatsApp

For MVP:

```text
Request Setup / Coming Soon
```

#### Option 5: Facebook Messenger

For MVP:

```text
Request Setup / Coming Soon
```

### Acceptance Criteria

1. User can copy public chat link.
2. User can copy widget code.
3. User can enter Telegram token if Telegram integration is enabled.
4. WhatsApp and Facebook do not block MVP launch.

---

## 7.5 Page 5: Public Chat Page

Route:

```text
/chat/:publicToken
```

### Purpose

Customer-facing chat page that business users can share with their customers.

### Requirements

1. Simple chat interface.
2. Business name or bot name.
3. AI replies using uploaded knowledge.
4. If unsure, AI triggers fallback.
5. Mobile-friendly design.

---

## 8. Database Requirements

Only five tables are required for MVP.

## 8.1 bots

```sql
create table bots (
  id uuid primary key default gen_random_uuid(),
  name text default 'AI Customer Service',
  owner_email text,
  status text default 'ready',
  source_type text default 'upload',
  answer_mode text default 'knowledge_only',
  business_type text default 'auto',
  tone text default 'professional',
  fallback_message text default 'I am not fully sure based on the information I have. Let me forward this to a human team member.',
  confidence_threshold numeric default 0.7,
  public_token text unique,
  suggested_questions jsonb default '[]',
  settings jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

## 8.2 knowledge_files

```sql
create table knowledge_files (
  id uuid primary key default gen_random_uuid(),
  bot_id uuid references bots(id) on delete cascade,
  file_name text,
  file_type text,
  file_url text,
  raw_text text,
  status text default 'processed',
  created_at timestamptz default now()
);
```

## 8.3 knowledge_chunks

```sql
create table knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  bot_id uuid references bots(id) on delete cascade,
  file_id uuid references knowledge_files(id) on delete cascade,
  chunk_text text not null,
  chunk_index int,
  embedding vector(1536),
  metadata jsonb default '{}',
  created_at timestamptz default now()
);
```

## 8.4 conversations

```sql
create table conversations (
  id uuid primary key default gen_random_uuid(),
  bot_id uuid references bots(id) on delete cascade,
  channel text default 'web',
  visitor_id text,
  status text default 'open',
  needs_human boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

## 8.5 messages

```sql
create table messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade,
  sender_type text not null,
  message_text text not null,
  confidence numeric,
  confidence_label text,
  source_text text,
  needs_human boolean default false,
  created_at timestamptz default now()
);
```

---

## 9. API Requirements

## 9.1 Generate Bot

```text
POST /api/generate-bot
```

### Input

Multipart form:

```text
file optional
pasted_text optional
owner_email optional
business_type optional
tone optional
settings json
```

### Backend Logic

1. Validate that file or pasted text exists.
2. Create bot record.
3. Store uploaded file if provided.
4. Extract text.
5. Create knowledge file record.
6. Split text into chunks.
7. Generate embeddings.
8. Store chunks.
9. Generate suggested questions.
10. Return public token and test URL.

### Output

```json
{
  "bot_id": "uuid",
  "public_token": "token",
  "test_url": "/bot/token/test",
  "suggested_questions": []
}
```

---

## 9.2 Get Bot Info

```text
GET /api/bot/:publicToken
```

### Output

```json
{
  "name": "AI Customer Service",
  "status": "ready",
  "business_type": "restaurant",
  "tone": "professional",
  "suggested_questions": [],
  "knowledge_file_count": 1
}
```

---

## 9.3 Ask Bot

```text
POST /api/bot/:publicToken/ask
```

### Input

```json
{
  "message": "What is your pricing?",
  "visitor_id": "visitor_123",
  "channel": "web"
}
```

### Backend Logic

1. Load bot by public token.
2. Search relevant knowledge chunks.
3. If no relevant chunk found, return fallback.
4. Generate answer using strict knowledge-only system prompt.
5. Calculate confidence.
6. Save conversation and messages.
7. Return answer.

### Output

```json
{
  "answer": "Based on the uploaded information...",
  "confidence": 0.86,
  "confidence_label": "High Confidence",
  "status": "answered",
  "source_used": true,
  "needs_human": false
}
```

---

## 9.4 Widget Script

```text
GET /widget/:publicToken.js
```

### Purpose

Return embeddable website widget JavaScript.

---

## 9.5 Telegram Connect

```text
POST /api/telegram/connect
```

### Input

```json
{
  "public_token": "token",
  "telegram_bot_token": "token"
}
```

---

## 9.6 Telegram Webhook

```text
POST /api/webhooks/telegram/:publicToken
```

### Purpose

Receive Telegram messages and reply using the GO!CS ask API.

---

## 10. AI Answer Engine Requirements

## 10.1 Strict System Prompt

```text
You are GO!CS, an accuracy-first AI customer service assistant.

Rules:
1. Answer only using the provided business information.
2. Do not invent facts, prices, policies, guarantees, availability, or business commitments.
3. If the answer is not found in the provided information, say that you do not have enough information.
4. If the question is unclear, ask a clarifying question.
5. Keep the answer short, clear, and customer-service friendly.
6. Reply in the same language as the customer unless the business setting says otherwise.
7. Accuracy is more important than fluency.
8. If confidence is low, suggest contacting a human team member.
```

## 10.2 Confidence Logic

Use three labels:

```text
High Confidence: 0.80 - 1.00
Medium Confidence: 0.60 - 0.79
Not Enough Information: below 0.60
```

## 10.3 Fallback Message

```text
I could not find enough information in the uploaded company information to answer this confidently. Please contact the team directly or upload more details to improve this AI assistant.
```

## 10.4 Risk Keywords

Questions containing these topics should require stronger source support:

```text
price
refund
guarantee
legal
medical
financial
availability
contract
latest
warranty
promise
```

---

## 11. Technical Stack

Recommended MVP stack:

```text
Next.js
React
TailwindCSS
Supabase Auth optional
Supabase Postgres
Supabase Storage
pgvector
OpenAI or compatible LLM API
Vercel deployment
```

Auth is optional for the first demo. If not using login, use public token and optional owner email capture.

---

## 12. One-Week Development Plan

## Day 1: Upload Landing + Bot Generation Foundation

Tasks:

1. Build landing upload page.
2. Build file upload component.
3. Build paste text mode.
4. Create bots table.
5. Create knowledge_files table.
6. Create POST /api/generate-bot.
7. Generate public token.
8. Redirect user to generating page.

Acceptance:

```text
User opens website, uploads information, clicks generate, and system creates a bot session.
```

---

## Day 2: Text Extraction + Chunking

Tasks:

1. Extract text from PDF, DOCX, TXT.
2. Store raw text.
3. Split text into chunks.
4. Create knowledge_chunks table.
5. Store chunks.
6. Show generation progress.

Acceptance:

```text
Uploaded document becomes searchable knowledge chunks.
```

---

## Day 3: AI Answer API

Tasks:

1. Build POST /api/bot/:publicToken/ask.
2. Search relevant chunks.
3. Generate answer from chunks only.
4. Add fallback logic.
5. Add confidence labels.
6. Save conversations and messages.

Acceptance:

```text
AI answers questions from uploaded knowledge and refuses unsupported questions.
```

---

## Day 4: Test Chat Page

Tasks:

1. Build /bot/:publicToken/test.
2. Build chat UI.
3. Add suggested questions.
4. Show confidence label.
5. Add share button.

Acceptance:

```text
User can immediately test generated AI customer service.
```

---

## Day 5: Public Chat + Website Widget

Tasks:

1. Build /chat/:publicToken.
2. Build widget script endpoint.
3. Build share page.
4. Add copy link and copy widget code.

Acceptance:

```text
User can share public link and embed widget on website.
```

---

## Day 6: Telegram Basic Integration

Tasks:

1. Build Telegram token input.
2. Save Telegram configuration.
3. Register webhook.
4. Receive Telegram messages.
5. Reply using ask API.

Acceptance:

```text
Telegram user can message the bot and receive an answer from uploaded knowledge.
```

---

## Day 7: Polish + QA + Demo

Tasks:

1. Fix bugs.
2. Improve loading states.
3. Improve error states.
4. Improve mobile responsiveness.
5. Prepare demo file.
6. Prepare demo script.
7. Deploy MVP.

Acceptance:

```text
Complete journey works: Upload → Generate → Test → Share → Widget / Telegram.
```

---

## 13. MVP Success Metrics

| Metric | Target |
|---|---:|
| Time from upload to test chat | Under 3 minutes |
| User setup steps | Under 5 actions |
| AI unsupported-answer fallback accuracy | Over 90% |
| Hallucination rate in test cases | Under 5% |
| User can test without training | 100% |
| Public link works | 100% |
| Widget embed works | 90%+ |

---

## 14. Demo Script

```text
GO!CS is an upload-first AI customer service generator.

A business owner does not need to configure a complex chatbot system.
They simply upload their FAQ, menu, pricing, service package, or SOP.

GO!CS reads the information, builds a knowledge base, and instantly generates an AI customer service assistant.

The AI only answers from the uploaded company information.
If it cannot find the answer, it does not guess. It says there is not enough information and suggests human confirmation.

After testing, the user can share a public chat link, embed it on a website, or connect Telegram.

The goal is simple:
Upload information. Generate accurate AI customer service. Go live.
```

---

## 15. Codex Master Prompt

```text
Build GO!CS, a lightweight upload-first AI customer service generator powered by Logos Data Engine.

This is not a heavy SaaS dashboard. The MVP must be extremely simple.

Core flow:
1. User opens website.
2. User uploads company document or pastes company information.
3. User selects simple AI behavior settings.
4. User clicks Generate My AI Customer Service.
5. System automatically creates an AI customer service assistant.
6. System processes the uploaded information.
7. User enters test chat.
8. User immediately asks questions.
9. User can share public chat link, copy website widget code, or connect Telegram.

Build only these pages:
- /
- /generating/:sessionId
- /bot/:publicToken/test
- /bot/:publicToken/share
- /chat/:publicToken

Build only these database tables:
- bots
- knowledge_files
- knowledge_chunks
- conversations
- messages

Build these API routes:
- POST /api/generate-bot
- GET /api/bot/:publicToken
- POST /api/bot/:publicToken/ask
- GET /widget/:publicToken.js
- POST /api/telegram/connect
- POST /api/webhooks/telegram/:publicToken

AI rules:
1. Only answer using uploaded knowledge.
2. Do not invent facts.
3. If no relevant information exists, say not enough information.
4. If confidence is low, suggest human confirmation.
5. Reply in the same language as the user.
6. Keep answers short and customer-service friendly.

Do not build:
- workspace system
- billing
- team permission
- advanced analytics
- CRM inbox
- multi-bot management
- full WhatsApp integration
- full Facebook integration

The final MVP must feel like:
Upload → Generate → Test → Share.
```
