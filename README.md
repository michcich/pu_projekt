# Sprawozdanie z realizacji projektu
## Chatbot do analizy raportów finansowych spółek giełdowych

---

## 1. Informacje podstawowe

**Temat projektu:** System chatbota wspomagającego analizę raportów finansowych przedsiębiorstw notowanych na giełdzie z podejściem **multi-report analysis**

**Zespół projektowy:**
- **Michał Cichosz** – projekt koncepcji chatbota, przygotowanie logiki działania systemu, dokumentacja projektowa
- **Radosław Gęgotek** – projekt aplikacji React (frontend), analiza danych finansowych, przygotowanie źródeł danych (raporty finansowe), testowanie działania chatbota

**Okres realizacji:** Styczeń 2026

**Technologie:**
- Backend: Python 3.10+, FastAPI
- AI/ML: Google Gemini API (gemini-1.5-flash)
- Baza danych: SQLite + SQLAlchemy (async)
- Przetwarzanie PDF: PyPDF2, pdfplumber
- Frontend: React

---

## 2. Koncepcja projektu

### 2.1. Idea przewodnia

Kluczową innowacją projektu jest podejście **company-based** - chatbot nie analizuje pojedynczych raportów, ale ma dostęp do **wszystkich raportów** przypisanych do danej firmy. Pozwala to na:

- **Analizę trendów** - porównywanie wyników między okresami
- **Wykrywanie zmian** - identyfikacja wzrostów/spadków w czasie
- **Kontekstowe odpowiedzi** - bazujące na pełnej historii finansowej
- **Inteligentne porównania** - między kwartałami i latami

### 2.2. Architektura danych

```
FIRMA (Company)
  ├── Raport Q1 2024 (Report)
  ├── Raport Q2 2024 (Report)
  ├── Raport Q3 2024 (Report)
  └── Raport Q4 2024 (Report)

CHATBOT otrzymuje zapytanie:
  "Jaki jest trend przychodów?"
  
CHATBOT analizuje:
  ✓ Wszystkie 4 raporty jednocześnie
  ✓ Porównuje dane między okresami
  ✓ Identyfikuje wzrosty/spadki
  ✓ Odpowiada z pełnym kontekstem
```

---

## 3. Cel projektu

Celem projektu jest stworzenie inteligentnego chatbota, który umożliwia użytkownikom:

1. **Zarządzanie bazą firm** - organizacja raportów według spółek
2. **Upload wielu raportów** - budowanie historii finansowej
3. **Zadawanie pytań w języku naturalnym** - bez znajomości SQL czy Excel
4. **Otrzymywanie analiz trendów** - bazujących na wielu okresach
5. **Porównywanie wyników** - między kwartałami i latami
6. **Automatyczne podsumowania** - kluczowych wskaźników

### Uzasadnienie wyboru tematu

Raporty finansowe spółek giełdowych są skomplikowane i trudne do analizy. Dodatkowo:
- **Problem izolacji danych** - analiza pojedynczego raportu nie pokazuje pełnego obrazu
- **Brak kontekstu czasowego** - trudno porównywać trendy bez narzędzi
- **Bariera techniczna** - nie każdy potrafi efektywnie analizować dane finansowe

Nasz system rozwiązuje te problemy poprzez:
- Centralizację wszystkich raportów firmy w jednym miejscu
- Automatyczną analizę trendów przez AI
- Przystępny interfejs konwersacyjny

---

## 4. Architektura systemu

### 4.1. Diagram architektury

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (Angular)                     │
│              [Planowany - W trakcie realizacji]          │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌──────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                       │
│  ┌────────────┬─────────────┬──────────────────────────┐ │
│  │ Companies  │  Reports    │     Chat                 │ │
│  │    API     │     API     │     API                  │ │
│  └────────────┴─────────────┴──────────────────────────┘ │
└───────┬──────────────┬──────────────┬───────────────┬────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
┌──────────┐  ┌──────────────┐  ┌─────────┐  ┌──────────┐
│ Database │  │ PDF Processor│  │ Gemini  │  │   File   │
│ (SQLite) │  │ (PyPDF2)     │  │   API   │  │ Storage  │
└──────────┘  └──────────────┘  └─────────┘  └──────────┘
```

### 4.2. Struktura projektu

```
financial-chatbot-backend/
├── app/
│   ├── main.py                    # Główna aplikacja
│   ├── config.py                  # Konfiguracja
│   ├── api/
│   │   ├── companies.py           # 🆕 API zarządzania firmami
│   │   ├── reports.py             # API raportów (zmodyfikowane)
│   │   └── chat.py                # API chatbota (zmodyfikowane)
│   ├── services/
│   │   ├── gemini_service.py      # Integracja z AI
│   │   └── pdf_processor.py       # Przetwarzanie PDF
│   ├── models/
│   │   └── schemas.py             # Modele danych
│   └── database/
│       └── database.py            # 🆕 Nowy schemat bazy
├── data/
│   └── reports/                   # Przechowywanie PDF
├── requirements.txt
├── .env
├── README.md
├── QUICK_START.md                 # 🆕 Przewodnik uruchomienia
└── test_api.py                    # 🆕 Nowy workflow testowy
```

---

## 5. Schemat bazy danych

### 5.1. Diagram ERD

```
┌─────────────────────────────────────┐
│           COMPANIES                 │  🆕 Główna tabela
│         (Firmy giełdowe)            │
├─────────────────────────────────────┤
│ PK │ id                    INTEGER  │
│ UK │ name                  VARCHAR  │
│    │ ticker                VARCHAR  │
│    │ description           TEXT     │
│    │ industry              VARCHAR  │
│    │ created_at            DATETIME │
│    │ updated_at            DATETIME │
└────────────┬────────────────────────┘
             │ 1
             │
             │ N (Jedna firma → wiele raportów)
             │
┌────────────┴────────────────────────┐
│            REPORTS                  │
│      (Raporty finansowe)            │
├─────────────────────────────────────┤
│ PK │ id                    INTEGER  │
│ FK │ company_id            INTEGER  │  🔗 Powiązanie z firmą
│    │ filename              VARCHAR  │
│    │ original_filename     VARCHAR  │
│    │ report_type           VARCHAR  │
│    │ report_period         VARCHAR  │
│    │ report_year           INTEGER  │  🆕 Dla sortowania
│    │ report_quarter        INTEGER  │  🆕 1-4 lub NULL
│    │ upload_date           DATETIME │
│    │ file_size             INTEGER  │
│    │ file_path             VARCHAR  │
│    │ extracted_text        TEXT     │
│    │ key_metrics           JSON     │
│    │ summary               TEXT     │
│    │ status                VARCHAR  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│        CHAT_SESSIONS                │
│    (Sesje rozmów)                   │
├─────────────────────────────────────┤
│ PK │ id                    INTEGER  │
│ UK │ session_id            VARCHAR  │
│ FK │ company_id            INTEGER  │  🔗 Sesja przypisana do firmy
│    │ created_at            DATETIME │
│    │ updated_at            DATETIME │
└────────────┬────────────────────────┘
             │ 1
             │
             │ N
             │
┌────────────┴────────────────────────┐
│         CHAT_HISTORY                │
│   (Historia wiadomości)             │
├─────────────────────────────────────┤
│ PK │ id                    INTEGER  │
│ FK │ session_id            VARCHAR  │
│    │ role                  VARCHAR  │
│    │ content               TEXT     │
│    │ timestamp             DATETIME │
└─────────────────────────────────────┘
```

### 5.2. Opis tabel

#### 🆕 Tabela: `companies` (Firmy)

**Cel:** Centralna tabela przechowująca informacje o spółkach giełdowych

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | INTEGER | Klucz główny |
| `name` | VARCHAR | Nazwa firmy (UNIQUE) |
| `ticker` | VARCHAR | Symbol giełdowy (np. PKN, CDR) |
| `description` | TEXT | Opis działalności |
| `industry` | VARCHAR | Branża (np. "Energia", "Gaming") |
| `created_at` | DATETIME | Data dodania do systemu |
| `updated_at` | DATETIME | Data ostatniej aktualizacji |

**Relacje:**
- 1 firma → N raportów (one-to-many)
- 1 firma → N sesji chatbota

#### Tabela: `reports` (Raporty) - ZMODYFIKOWANA

**Cel:** Przechowywanie raportów finansowych przypisanych do firm

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | INTEGER | Klucz główny |
| `company_id` | INTEGER | 🔗 Klucz obcy do `companies` |
| `filename` | VARCHAR | Unikalna nazwa w systemie |
| `original_filename` | VARCHAR | Oryginalna nazwa pliku |
| `report_type` | VARCHAR | Typ: quarterly, annual, other |
| `report_period` | VARCHAR | Okres: "Q3 2024", "2023" |
| `report_year` | INTEGER | 🆕 Rok raportu (dla sortowania) |
| `report_quarter` | INTEGER | 🆕 Kwartał: 1-4 lub NULL |
| `upload_date` | DATETIME | Data uploadu |
| `file_size` | INTEGER | Rozmiar pliku |
| `file_path` | VARCHAR | Ścieżka do pliku |
| `extracted_text` | TEXT | Wyekstrahowany tekst |
| `key_metrics` | JSON | Wskaźniki finansowe |
| `summary` | TEXT | Podsumowanie AI |
| `status` | VARCHAR | Status przetwarzania |

**Kluczowe zmiany:**
- Dodano `company_id` jako klucz obcy
- Dodano `report_year` i `report_quarter` dla lepszego sortowania
- Wszystkie raporty muszą być przypisane do firmy

#### Tabela: `chat_sessions` - ZMODYFIKOWANA

**Cel:** Sesje konwersacji z chatbotem dla konkretnych firm

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | INTEGER | Klucz główny |
| `session_id` | VARCHAR | UUID sesji |
| `company_id` | INTEGER | 🔗 Firma której dotyczy rozmowa |
| `created_at` | DATETIME | Rozpoczęcie sesji |
| `updated_at` | DATETIME | Ostatnia aktywność |

**Kluczowa zmiana:**
- Sesja przypisana do firmy (nie pojedynczego raportu)
- Chatbot ma dostęp do wszystkich raportów firmy

---

## 6. API Endpoints

### 6.1. 🆕 Companies API (Zarządzanie firmami)

| Method | Endpoint | Opis | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/companies/` | Utwórz firmę | `{name, ticker, description, industry}` | Dane firmy + ID |
| GET | `/api/companies/` | Lista firm | Query: skip, limit | Array firm z liczbą raportów |
| GET | `/api/companies/{id}` | Szczegóły firmy | Path: company_id | Firma + lista raportów |
| PUT | `/api/companies/{id}` | Zaktualizuj firmę | Partial update | Zaktualizowane dane |
| DELETE | `/api/companies/{id}` | Usuń firmę | Path: company_id | Confirmation (kaskadowo usuwa raporty) |

**Przykład - utworzenie firmy:**
```json
POST /api/companies/
{
  "name": "PKN Orlen",
  "ticker": "PKN",
  "description": "Koncern paliwowy",
  "industry": "Energia i paliwa"
}

Response 201:
{
  "id": 1,
  "name": "PKN Orlen",
  "ticker": "PKN",
  "description": "Koncern paliwowy",
  "industry": "Energia i paliwa",
  "created_at": "2026-01-26T10:00:00",
  "updated_at": "2026-01-26T10:00:00",
  "reports_count": 0
}
```

### 6.2. Reports API (Raporty) - ZMODYFIKOWANE

| Method | Endpoint | Opis | Kluczowe zmiany |
|--------|----------|------|-----------------|
| POST | `/api/reports/upload` | Upload raportu | 🔴 Wymaga `company_id` w Form Data |
| GET | `/api/reports/company/{company_id}` | 🆕 Raporty firmy | Nowy endpoint - wszystkie raporty firmy |
| GET | `/api/reports/{id}` | Szczegóły raportu | Bez zmian |
| DELETE | `/api/reports/{id}` | Usuń raport | Bez zmian |

**Przykład - upload raportu:**
```bash
POST /api/reports/upload
Form Data:
  - company_id: 1  # 🔴 WYMAGANE
  - report_type: "quarterly"
  - file: [PDF FILE]

Response 200:
{
  "id": 5,
  "company_id": 1,
  "company_name": "PKN Orlen",
  "filename": "raport_Q3_2024.pdf",
  "report_period": "Q3 2024",
  "report_year": 2024,
  "report_quarter": 3,
  "status": "processed"
}
```

### 6.3. Chat API - ZMODYFIKOWANE

| Method | Endpoint | Opis | Kluczowe zmiany |
|--------|----------|------|-----------------|
| POST | `/api/chat/` | Wyślij wiadomość | 🔴 Wymaga `company_id` zamiast `report_id` |
| GET | `/api/chat/history/{session_id}` | Historia | Bez zmian |
| GET | `/api/chat/sessions/company/{id}` | 🆕 Sesje firmy | Nowy endpoint |
| DELETE | `/api/chat/session/{session_id}` | Usuń sesję | Bez zmian |
| POST | `/api/chat/clear/{session_id}` | Wyczyść historię | Bez zmian |
| POST | `/api/chat/analyze/{company_id}` | 🆕 Analiza trendów | **NOWA FUNKCJA** |

**Przykład - chat (NOWY):**
```json
POST /api/chat/
{
  "message": "Porównaj przychody między Q1, Q2 i Q3 2024",
  "company_id": 1  # 🔴 ZMIANA: company_id zamiast report_id
}

Response 200:
{
  "response": "Analizując przychody PKN Orlen w 2024:\n- Q1: 45 mld PLN\n- Q2: 48 mld PLN (+6.7%)\n- Q3: 52 mld PLN (+8.3%)\n\nWidoczny jest stały trend wzrostowy...",
  "session_id": "uuid-xxx",
  "company_name": "PKN Orlen",
  "reports_used": 3,  # 🆕 Liczba raportów w analizie
  "suggestions": [
    "Jaki był wzrost rok do roku?",
    "Jak zmieniała się rentowność?"
  ]
}
```

**🆕 Przykład - analiza trendów:**
```bash
POST /api/chat/analyze/1

Response 200:
{
  "company_id": 1,
  "company_name": "PKN Orlen",
  "reports_analyzed": 4,
  "analysis": "Analiza trendów PKN Orlen:\n\n1. Trend przychodów: ROSNĄCY\n   - Stały wzrost QoQ o średnio 7%\n   ...",
  "reports_periods": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
}
```

---

## 7. Komponenty systemu

### 7.1. PDF Processor

**Bez zmian w funkcjonalności**, ale wyniki są przypisywane do firmy.

**Kluczowe funkcje:**
- Ekstrakcja tekstu (PyPDF2 + fallback pdfplumber)
- Wykrywanie okresu raportu
- Parsowanie wskaźników finansowych
- Ekstrakcja tabel

### 7.2. 🆕 Gemini Service - ROZSZERZONE MOŻLIWOŚCI

**Nowa funkcja: Multi-Report Context**

```python
def _prepare_context(
    self,
    company_name: str,
    all_reports_text: List[Dict[str, str]],  # 🆕 WSZYSTKIE raporty
    chat_history: List[ChatMessage]
) -> str:
    """Przygotuj kontekst z WSZYSTKICH raportów firmy"""
```

**Kluczowe zmiany:**
- Kontekst zawiera **wszystkie raporty** firmy
- System prompt dostosowany do analizy trendów
- Inteligentne sugestie bazujące na liczbie raportów
- Nowa metoda `analyze_company_trends()`

**Przykład System Prompt:**
```
WAŻNE - Masz dostęp do WSZYSTKICH raportów firmy:
- Możesz analizować trendy w czasie
- Możesz porównywać kwartały i lata
- Bazuj na kompletnych danych historycznych
- Wskazuj zmiany procentowe między okresami
```

### 7.3. 🆕 Companies Service (Nowy moduł)

Obsługa CRUD operacji dla firm przez `companies.py` API router.

---

## 8. Przepływ danych

### 8.1. 🆕 Workflow użytkownika

```
1. UŻYTKOWNIK → Tworzy firmę "PKN Orlen"
                 ↓
2. SYSTEM → Zapisuje firmę w bazie (id=1)
                 ↓
3. UŻYTKOWNIK → Upload raport Q1 2024 (company_id=1)
4. UŻYTKOWNIK → Upload raport Q2 2024 (company_id=1)
5. UŻYTKOWNIK → Upload raport Q3 2024 (company_id=1)
                 ↓
6. SYSTEM → Przetwarza każdy raport:
            - Ekstrakcja tekstu
            - Wykrywanie okresu
            - Parsowanie wskaźników
            - Generowanie podsumowania AI
                 ↓
7. UŻYTKOWNIK → Zadaje pytanie:
                "Porównaj przychody Q1-Q3"
                 ↓
8. CHATBOT → Pobiera WSZYSTKIE 3 raporty
           → Przygotowuje kontekst dla AI
           → Generuje odpowiedź bazując na pełnych danych
                 ↓
9. UŻYTKOWNIK → Otrzymuje kompleksową analizę:
                "Q1: 45 mld, Q2: 48 mld (+7%), Q3: 52 mld (+8%)
                 Trend wzrostowy, rentowność rośnie..."
```

### 8.2. Multi-Report Analysis Flow

```
┌─────────────────────────────────────┐
│  User Question:                     │
│  "Jaki jest trend przychodów?"     │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  System: Fetch ALL company reports   │
│  ┌──────────┬──────────┬──────────┐ │
│  │ Q1 2024  │ Q2 2024  │ Q3 2024  │ │
│  └──────────┴──────────┴──────────┘ │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Gemini AI: Analyze context          │
│  - Report Q1: Revenue 45 bln         │
│  - Report Q2: Revenue 48 bln (+7%)   │
│  - Report Q3: Revenue 52 bln (+8%)   │
│                                      │
│  → Pattern: Growing trend            │
│  → Average growth: 7.5% QoQ          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Response to User:                   │
│  "Przychody PKN Orlen wykazują       │
│   stały trend wzrostowy. W Q1 były  │
│   45 mld PLN, w Q2 wzrosły do 48    │
│   mld (+7%), a w Q3 osiągnęły 52    │
│   mld (+8%). Średni wzrost kwartał  │
│   do kwartału wynosi 7.5%."         │
└──────────────────────────────────────┘
```

---

## 9. Postęp realizacji

### ✅ Zrealizowane funkcjonalności

**Backend - Architektura:**
- [x] 🆕 Nowy schemat bazy danych (companies → reports)
- [x] 🆕 SQLAlchemy models z relacjami (1:N)
- [x] 🆕 Companies API (CRUD)
- [x] ✏️ Reports API (zmodyfikowane - company-based)
- [x] ✏️ Chat API (zmodyfikowane - multi-report)
- [x] Pydantic schemas (zaktualizowane)

**Backend - Funkcjonalności:**
- [x] 🆕 Multi-report analysis (kluczowa innowacja)
- [x] 🆕 Trend analysis endpoint
- [x] 🆕 Company-based sessions
- [x] Przetwarzanie PDF
- [x] Integracja z Gemini AI
- [x] ✏️ Rozszerzony system prompt (analiza trendów)
- [x] Automatyczne podsumowania
- [x] Historia konwersacji

**Dokumentacja:**
- [x] README.md (zaktualizowany)
- [x] 🆕 QUICK_START.md (przewodnik krok po kroku)
- [x] 🆕 SPRAWOZDANIE.md (to!)
- [x] ✏️ test_api.py (nowy workflow)
- [x] Swagger/ReDoc documentation

### 🚧 W trakcie realizacji

- [ ] Frontend Angular (planowany)
- [ ] Wizualizacje wykresów trendów
- [ ] Export analiz do PDF/Excel

### 📋 Planowane rozszerzenia

- [ ] Web scraping raportów z GPW
- [ ] Porównywanie między firmami
- [ ] Alerty o zmianach wskaźników
- [ ] Autoryzacja użytkowników
- [ ] Deployment (Docker, CI/CD)

---

## 10. Testowanie

### 10.1. Nowy workflow testowy

**Skrypt `test_api.py` testuje:**

```python
TEST 1: Health Check
TEST 2: System Stats
TEST 3: Create Company (PKN Orlen)
TEST 4: Get All Companies
TEST 5: Upload Report for Company
TEST 6: Get Company Details (with reports list)
TEST 7: Chat with AI (multi-report analysis)
TEST 8: Analyze Company Trends
```

### 10.2. Przykładowe scenariusze testowe

**Scenariusz 1: Pełny workflow z jedną firmą**
1. Utwórz firmę "CD Projekt"
2. Upload 4 raporty kwartalne (Q1-Q4 2024)
3. Zadaj: "Porównaj wszystkie kwartały"
4. Chatbot analizuje wszystkie 4 raporty ✅

**Scenariusz 2: Analiza trendów**
1. Firma z 6 raportami (Q1-Q3 2023, Q1-Q3 2024)
2. Zadaj: "Porównaj rok do roku"
3. Chatbot pokazuje zmiany YoY ✅

**Scenariusz 3: Multiple companies**
1. Utwórz PKN i Lotos
2. Upload raporty dla obu
3. Analizuj każdą osobno
4. Porównuj wyniki ✅

---

## 11. Innowacje projektu

### 11.1. 🆕 Multi-Report Context

**Problem:** Tradycyjne chatboty analizują pojedyncze dokumenty

**Nasze rozwiązanie:**
- Chatbot ma dostęp do **wszystkich raportów** firmy
- Kontekst zawiera dane z wielu okresów
- AI może porównywać i znajdować trendy

**Przykład:**
```
Tradycyjny chatbot:
Q: "Jakie były przychody?"
A: "W tym raporcie: 45 mld PLN"

Nasz chatbot:
Q: "Jakie były przychody?"
A: "W Q1: 45 mld, Q2: 48 mld (+7%), Q3: 52 mld (+8%).
    Widoczny trend wzrostowy o średnio 7.5% na kwartał."
```

### 11.2. Company-Centric Architecture

**Korzyści:**
- Lepsze organizowanie danych
- Łatwiejsze zarządzanie wieloma raportami
- Naturalne grupowanie po firmach
- Możliwość porównań między okresami

### 11.3. Intelligent Context Management

**Optymalizacje:**
- Limit ~8000 znaków na raport (mieści się w kontekście Gemini)
- Sortowanie raportów chronologicznie
- Inteligentne sugestie bazujące na liczbie dostępnych raportów

---

## 12. Wnioski i dalsze kroki

### 12.1. Osiągnięte cele

✅ **Główny cel:** Stworzono chatbota analizującego raporty finansowe  
✅ **Innowacja:** Zaimplementowano multi-report analysis  
✅ **Architektura:** Przejście na company-based model  
✅ **AI Integration:** Pełna integracja z Gemini API  
✅ **Dokumentacja:** Kompletna dokumentacja techniczna i użytkowa  

### 12.2. Kluczowe osiągnięcia techniczne

1. **Async SQLAlchemy** - nowoczesny ORM z async/await
2. **Relacyjny model** - Companies → Reports (1:N)
3. **Multi-document AI context** - analiza wielu raportów jednocześnie
4. **Intelligent PDF processing** - fallback mechanisms
5. **RESTful API** - kompletne endpointy CRUD

### 12.3. Wyzwania i rozwiązania

| Wyzwanie | Rozwiązanie |
|----------|-------------|
| Limit kontekstu AI | Ograniczenie tekstu do 8000 znaków/raport |
| Różnorodność formatów PDF | PyPDF2 z fallback na pdfplumber |
| Parsowanie wskaźników | Regex patterns + walidacja |
| Zarządzanie sesjami | UUID + powiązanie z firmą |
| Sortowanie raportów | Dedykowane kolumny year/quarter |

### 12.4. Następne etapy (priorytet)

**Tydzień 1-2:**
- [ ] Frontend Angular - podstawowy UI
- [ ] Komponenty: lista firm, upload, chat
- [ ] Wizualizacja trendów (Chart.js)

**Tydzień 3-4:**
- [ ] Testy z prawdziwymi raportami GPW
- [ ] Optymalizacja parsowania wskaźników
- [ ] Export analiz do PDF

**Długoterminowo:**
- [ ] Web scraping raportów automatyczny
- [ ] System alertów o zmianach
- [ ] Deployment produkcyjny (Docker + CI/CD)
- [ ] Autoryzacja i multi-tenancy

---

## 13. Podsumowanie

Projekt chatbota do analizy raportów finansowych został pomyślnie zrealizowany z **kluczową innowacją** - podejściem **company-based multi-report analysis**. 

**Główne osiągnięcia:**
- ✅ Funkcjonalny backend API z pełnym CRUD
- ✅ Inteligentny chatbot analizujący wiele raportów jednocześnie
- ✅ Nowoczesna architektura z async SQLAlchemy
- ✅ Kompletna dokumentacja i testy

System przewyższa tradycyjne rozwiązania poprzez możliwość **analizy trendów** i **porównywania wyników** między okresami, co daje użytkownikom pełniejszy obraz sytuacji finansowej spółek.

Wykorzystanie Gemini AI oraz modularnej architektury FastAPI zapewnia łatwość rozwoju i skalowania w przyszłości.

---

**Data sporządzenia:** 26 stycznia 2026  
**Autorzy:** Michał Cichosz, Radosław Gęgotek  
**Wersja:** 2.0 (Company-based architecture)