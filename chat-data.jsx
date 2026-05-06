// chat-data.jsx
// Knowledge fixtures + lightweight mock AI logic for GO!CS prototype.

const SAKURA = {
  name: 'Sakura Ramen',
  fileName: 'Sakura_Ramen_Info.pdf',
  fileSize: '142 KB',
  pages: 6,
};

const RISK_KEYWORDS = [
  'price', 'pricing', 'refund', 'guarantee', 'legal', 'medical',
  'financial', 'availability', 'contract', 'latest', 'warranty', 'promise'
];

const FALLBACK_LINES = [
  "I could not find enough information in the uploaded company information to answer this confidently.",
  'Please contact the team directly or upload more details to improve this AI assistant.'
];

const SAKURA_QA = [
  {
    q: 'What are your business hours?',
    confidence: 'high',
    source: 'Sakura_Ramen_Info.pdf · page 1 — Hours',
    a: [
      "We're open every day:",
      '• Mon–Thu — 11:30 AM to 9:30 PM',
      '• Fri–Sat — 11:30 AM to 10:30 PM',
      '• Sun — 12:00 PM to 9:00 PM',
      'Last orders are taken 30 minutes before closing.',
    ],
  },
  {
    q: 'Do you take reservations?',
    confidence: 'high',
    source: 'Sakura_Ramen_Info.pdf · page 2 — Reservations',
    a: [
      'Yes — we take reservations for parties of 4 or more.',
      'You can book online at sakuraramen.com/book or call us at (415) 555-0148.',
      'Walk-ins are always welcome at the bar.',
    ],
  },
  {
    q: 'What ramen do you serve?',
    confidence: 'high',
    source: 'Sakura_Ramen_Info.pdf · page 3 — Menu',
    a: [
      'Our four signature bowls:',
      '• Tonkotsu Shio — 18-hour pork bone broth, $17',
      '• Spicy Miso — house chili oil, ground pork, $18',
      '• Yuzu Shoyu — chicken & dashi, citrus finish, $17',
      '• Vegan Shiitake — mushroom dashi, charred corn, $16',
      'All bowls come with chashu or tofu, ajitama egg, nori, and scallion.',
    ],
  },
  {
    q: 'Do you have vegan or gluten-free options?',
    confidence: 'high',
    source: 'Sakura_Ramen_Info.pdf · page 3 — Menu',
    a: [
      'Yes. The Vegan Shiitake bowl is fully plant-based.',
      'For gluten-free guests, we offer rice noodles as a swap on any bowl (+$2).',
      'Please let your server know about allergies — we prep GF orders separately.',
    ],
  },
  {
    q: 'Where are you located?',
    confidence: 'high',
    source: 'Sakura_Ramen_Info.pdf · page 1 — Location',
    a: [
      "We're at 412 Hayes Street, San Francisco, CA 94102.",
      'Two blocks from Civic Center BART. Street parking on Octavia after 6 PM.',
    ],
  },
  {
    q: 'Do you offer catering?',
    confidence: 'medium',
    source: 'Sakura_Ramen_Info.pdf · page 5 — Private Events',
    a: [
      'We do private events and large takeout trays — minimum 12 people.',
      "Email events@sakuraramen.com with your date and headcount and we'll send a menu.",
    ],
  },
  {
    q: 'What is your refund policy?',
    confidence: 'low',
    source: null,
    a: FALLBACK_LINES,
  },
];

const SAKURA_GREETING = {
  role: 'ai',
  text: "Hi! I'm the Sakura Ramen assistant. Ask me about our menu, hours, reservations, or location.",
  confidence: null,
  source: null,
};

function tokenize(text) {
  return String(text || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter((w) => w.length > 2);
}

function isRiskQuestion(message) {
  const lower = String(message || '').toLowerCase();
  return RISK_KEYWORDS.some((kw) => lower.includes(kw));
}

function findKnowledgeMatch(message) {
  const lower = String(message || '').toLowerCase().trim();
  const exact = SAKURA_QA.find((qa) => qa.q.toLowerCase() === lower);
  if (exact) return exact;

  const words = tokenize(lower);
  let best = null;
  let bestScore = 0;

  SAKURA_QA.forEach((qa) => {
    const qWords = new Set(tokenize(qa.q));
    let score = 0;
    words.forEach((w) => {
      if (qWords.has(w)) score += 1;
    });
    if (score > bestScore) {
      bestScore = score;
      best = qa;
    }
  });

  if (bestScore >= 2) return best;
  return null;
}

Object.assign(window, {
  SAKURA,
  SAKURA_QA,
  SAKURA_GREETING,
  RISK_KEYWORDS,
  FALLBACK_LINES,
  isRiskQuestion,
  findKnowledgeMatch,
});
