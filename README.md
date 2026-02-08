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
- Frontend: React + Vite + Recharts

---

## 2. Koncepcja projektu

### 2.1. Idea przewodnia

Kluczową innowacją projektu jest podejście **company-based** - chatbot nie analizuje pojedynczych raportów, ale ma dostęp do **wszystkich raportów** przypisanych do danej firmy. Pozwala to na:

- **Analizę trendów** - porównywanie wyników między okresami
- **Wykrywanie zmian** - identyfikacja wzrostów/spadków w czasie
- **Kontekstowe odpowiedzi** - bazujące na pełnej historii finansowej
- **Inteligentne porównania** - między kwartałami i latami
- **Wizualizację danych** - generowanie wykresów na żądanie

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
  ✓ Generuje wykres liniowy
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
7. **Wizualizację danych** - interaktywne wykresy w czacie

### Uzasadnienie wyboru tematu

Raporty finansowe spółek giełdowych są skomplikowane i trudne do analizy. Dodatkowo:
- **Problem izolacji danych** - analiza pojedynczego raportu nie pokazuje pełnego obrazu
- **Brak kontekstu czasowego** - trudno porównywać trendy bez narzędzi
- **Bariera techniczna** - nie każdy potrafi efektywnie analizować dane finansowe

Nasz system rozwiązuje te problemy poprzez:
- Centralizację wszystkich raportów firmy w jednym miejscu
- Automatyczną analizę trendów przez AI
- Przystępny interfejs konwersacyjny z wykresami

---

## 4. Architektura systemu

### 4.1. Diagram architektury

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                       │
│              [Vite + Tailwind + Recharts]                │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌──────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                       │
│  ┌────────────┬─────────────┬──────────────┬───────────┐ │
│  │ Companies  │  Reports    │     Chat     │ Analytics │ │
│  │    API     │     API     │     API      │    API    │ │
│  └────────────┴─────────────┴──────────────┴───────────┘ │
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
│   │   ├── companies.py           # API zarządzania firmami
│   │   ├── reports.py             # API raportów
│   │   ├── chat.py                # API chatbota
│   │   └── analytics.py           # 🆕 API analityki i wykresów
│   ├── services/
│   │   ├── gemini_service.py      # Integracja z AI
│   │   ├── pdf_processor.py       # Przetwarzanie PDF
│   │   └── chart_data_service.py  # 🆕 Logika wykresów
│   ├── models/
│   │   └── schemas.py             # Modele danych
│   └── database/
│       └── database.py            # Schemat bazy
├── data/
│   └── reports/                   # Przechowywanie PDF
├── requirements.txt
├── .env
├── README.md
├── QUICK_START.md                 # Przewodnik uruchomienia
└── test_api.py                    # Workflow testowy
```

---

## 5. Schemat bazy danych

### 5.1. Diagram ERD

```
┌─────────────────────────────────────┐
│           COMPANIES                 │
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
│    │ report_year           INTEGER  │
│    │ report_quarter        INTEGER  │
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

#### Tabela: `companies` (Firmy)

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

#### Tabela: `reports` (Raporty)

**Cel:** Przechowywanie raportów finansowych przypisanych do firm

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | INTEGER | Klucz główny |
| `company_id` | INTEGER | 🔗 Klucz obcy do `companies` |
| `filename` | VARCHAR | Unikalna nazwa w systemie |
| `original_filename` | VARCHAR | Oryginalna nazwa pliku |
| `report_type` | VARCHAR | Typ: quarterly, annual, other |
| `report_period` | VARCHAR | Okres: "Q3 2024", "2023" |
| `report_year` | INTEGER | Rok raportu (dla sortowania) |
| `report_quarter` | INTEGER | Kwartał: 1-4 lub NULL |
| `upload_date` | DATETIME | Data uploadu |
| `file_size` | INTEGER | Rozmiar pliku |
| `file_path` | VARCHAR | Ścieżka do pliku |
| `extracted_text` | TEXT | Wyekstrahowany tekst |
| `key_metrics` | JSON | Wskaźniki finansowe |
| `summary` | TEXT | Podsumowanie AI |
| `status` | VARCHAR | Status przetwarzania |

#### Tabela: `chat_sessions`

**Cel:** Sesje konwersacji z chatbotem dla konkretnych firm

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | INTEGER | Klucz główny |
| `session_id` | VARCHAR | UUID sesji |
| `company_id` | INTEGER | 🔗 Firma której dotyczy rozmowa |
| `created_at` | DATETIME | Rozpoczęcie sesji |
| `updated_at` | DATETIME | Ostatnia aktywność |

---

## 6. API Endpoints

### 6.1. Companies API (Zarządzanie firmami)

| Method | Endpoint | Opis | Request | Response |
|--------|----------|------|---------|----------|
| POST | `/api/companies/` | Utwórz firmę | `{name, ticker, description, industry}` | Dane firmy + ID |
| GET | `/api/companies/` | Lista firm | Query: skip, limit | Array firm z liczbą raportów |
| GET | `/api/companies/{id}` | Szczegóły firmy | Path: company_id | Firma + lista raportów |
| PUT | `/api/companies/{id}` | Zaktualizuj firmę | Partial update | Zaktualizowane dane |
| DELETE | `/api/companies/{id}` | Usuń firmę | Path: company_id | Confirmation (kaskadowo usuwa raporty) |

### 6.2. Reports API (Raporty)

| Method | Endpoint | Opis | Kluczowe zmiany |
|--------|----------|------|-----------------|
| POST | `/api/reports/upload` | Upload raportu | Wymaga `company_id` w Form Data |
| POST | `/api/reports/auto-upload` | Auto-upload | Automatyczne rozpoznawanie firmy |
| GET | `/api/reports/company/{company_id}` | Raporty firmy | Wszystkie raporty firmy |
| GET | `/api/reports/{id}` | Szczegóły raportu | Bez zmian |
| DELETE | `/api/reports/{id}` | Usuń raport | Bez zmian |

### 6.3. Chat API

| Method | Endpoint | Opis | Kluczowe zmiany |
|--------|----------|------|-----------------|
| POST | `/api/chat/` | Wyślij wiadomość | Wymaga `company_id` |
| GET | `/api/chat/history/{session_id}` | Historia | Bez zmian |
| DELETE | `/api/chat/session/{session_id}` | Usuń sesję | Bez zmian |
| POST | `/api/chat/analyze/{company_id}` | Analiza trendów | Generuje analizę trendów |

### 6.4. 🆕 Analytics API (Wykresy)

| Method | Endpoint | Opis | Response |
|--------|----------|------|----------|
| GET | `/api/analytics/chart-data/{company_id}` | Dane wykresów | JSON z danymi dla Recharts |

---

## 7. Komponenty systemu

### 7.1. PDF Processor

**Kluczowe funkcje:**
- Ekstrakcja tekstu (PyPDF2 + fallback pdfplumber)
- Wykrywanie okresu raportu (Regex + AI)
- Parsowanie wskaźników finansowych (Regex + AI)
- Ekstrakcja tabel

### 7.2. Gemini Service

**Nowa funkcja: Multi-Report Context**

```python
def _prepare_context(
    self,
    company_name: str,
    all_reports_text: List[Dict[str, str]],  # WSZYSTKIE raporty
    chat_history: List[ChatMessage]
) -> str:
    """Przygotuj kontekst z WSZYSTKICH raportów firmy"""
```

**Kluczowe zmiany:**
- Kontekst zawiera **wszystkie raporty** firmy
- System prompt dostosowany do analizy trendów
- Inteligentne sugestie bazujące na liczbie raportów
- Wykrywanie intencji użytkownika dotyczących wykresów

### 7.3. 🆕 Chart Data Service

Odpowiada za przygotowanie danych dla frontendu w formacie zrozumiałym dla biblioteki wykresów.

---

## 8. Przepływ danych

### 8.1. Workflow użytkownika

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
            - Wykrywanie okresu (AI)
            - Parsowanie wskaźników (AI)
            - Generowanie podsumowania AI
                 ↓
7. UŻYTKOWNIK → Zadaje pytanie:
                "Pokaż wykres przychodów"
                 ↓
8. CHATBOT → Rozpoznaje intencję wykresu
           → Pobiera dane historyczne
           → Zwraca konfigurację wykresu
                 ↓
9. FRONTEND → Rysuje interaktywny wykres liniowy
```

---

## 9. Postęp realizacji

### ✅ Zrealizowane funkcjonalności

**Backend - Architektura:**
- [x] Nowy schemat bazy danych (companies → reports)
- [x] SQLAlchemy models z relacjami (1:N)
- [x] Companies API (CRUD)
- [x] Reports API (company-based)
- [x] Chat API (multi-report)
- [x] Analytics API (wykresy)

**Backend - Funkcjonalności:**
- [x] Multi-report analysis
- [x] Trend analysis endpoint
- [x] Company-based sessions
- [x] Przetwarzanie PDF (Regex + AI fallback)
- [x] Integracja z Gemini AI
- [x] Rozszerzony system prompt (analiza trendów, wykresy)
- [x] Automatyczne podsumowania
- [x] Historia konwersacji

**Frontend:**
- [x] React + Vite
- [x] Lista firm i raportów
- [x] Upload plików
- [x] Czat z historią
- [x] 🆕 Wizualizacja wykresów (Recharts)

**Dokumentacja:**
- [x] README.md (zaktualizowany)
- [x] QUICK_START.md
- [x] test_api.py

---

## 10. Innowacje projektu

### 10.1. Multi-Report Context

**Problem:** Tradycyjne chatboty analizują pojedyncze dokumenty

**Nasze rozwiązanie:**
- Chatbot ma dostęp do **wszystkich raportów** firmy
- Kontekst zawiera dane z wielu okresów
- AI może porównywać i znajdować trendy

### 10.2. Hybrydowa Ekstrakcja Danych

**Problem:** Regex jest szybki ale zawodny, AI jest dokładne ale wolne/drogie.

**Nasze rozwiązanie:**
- System najpierw próbuje Regex.
- Jeśli kluczowe dane (przychody) nie zostaną znalezione, system automatycznie używa AI ("koło ratunkowe").
- Zapewnia to balans między wydajnością a dokładnością.

### 10.3. Wizualizacja w Czacie

**Problem:** Tekstowe odpowiedzi o liczbach są trudne do przyswojenia.

**Nasze rozwiązanie:**
- Chatbot potrafi generować wykresy w odpowiedzi na zapytanie.
- Wykresy są interaktywne i osadzone bezpośrednio w konwersacji.

---

## 11. Podsumowanie

Projekt chatbota do analizy raportów finansowych został pomyślnie zrealizowany z **kluczową innowacją** - podejściem **company-based multi-report analysis** oraz **wizualizacją danych**.

**Główne osiągnięcia:**
- ✅ Funkcjonalny backend API z pełnym CRUD
- ✅ Inteligentny chatbot analizujący wiele raportów jednocześnie
- ✅ Nowoczesna architektura z async SQLAlchemy
- ✅ Wizualizacja danych na wykresach
- ✅ Kompletna dokumentacja i testy

System przewyższa tradycyjne rozwiązania poprzez możliwość **analizy trendów**, **porównywania wyników** między okresami oraz **wizualizacji danych**, co daje użytkownikom pełniejszy obraz sytuacji finansowej spółek.

---

**Data sporządzenia:** 3 lutego 2026  
**Autorzy:** Michał Cichosz, Radosław Gęgotek  
**Wersja:** 3.0 (Charts & Analytics)