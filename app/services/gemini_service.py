import google.generativeai as genai
from typing import List, Dict, Optional
import json
from app.config import settings
from app.models.schemas import ChatMessage, MessageRole


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        self.system_prompt = """Jesteś asystentem AI specjalizującym się w analizie raportów finansowych polskich spółek giełdowych.

Twoje zadania:
- Analizuj dane finansowe z raportów kwartalnych i rocznych
- Porównuj wyniki między różnymi okresami (kwartały, lata)
- Identyfikuj trendy na podstawie wielu raportów
- Wyjaśniaj wskaźniki finansowe w prosty sposób
- Odpowiadaj po polsku, chyba że użytkownik poprosi o inny język

WAŻNE - Masz dostęp do WSZYSTKICH raportów firmy:
- Możesz analizować trendy w czasie
- Możesz porównywać kwartały i lata
- Bazuj na kompletnych danych historycznych
- Wskazuj zmiany procentowe między okresami

Zasady:
- Bazuj tylko na danych z dostarczonych raportów
- Jeśli czegoś nie ma w raportach, powiedz o tym wprost
- Używaj konkretnych liczb, dat i okresów
- Jeśli widzisz niepokojące sygnały, wskaż je
- Formatuj liczby czytelnie (np. 1 234 567 PLN)
- Podawaj źródło informacji (z którego raportu/okresu)

Styl odpowiedzi:
- Krótki i konkretny
- Profesjonalny ale przystępny
- Z przykładami gdy to potrzebne
- Używaj danych z wielu okresów do analizy trendów
"""
    
    def _prepare_context(
        self, 
        company_name: str,
        all_reports_text: List[Dict[str, str]], 
        chat_history: List[ChatMessage]
    ) -> str:
        """Przygotuj kontekst z WSZYSTKICH raportów firmy"""
        
        context_parts = [self.system_prompt]
        
        # Dodaj informację o firmie
        context_parts.append(f"\n=== FIRMA: {company_name} ===\n")
        
        # Dodaj WSZYSTKIE raporty firmy
        if all_reports_text:
            context_parts.append(f"\n--- DOSTĘPNE RAPORTY ({len(all_reports_text)}) ---\n")
            for report_data in all_reports_text:
                period = report_data.get('period', 'Nieznany okres')
                text = report_data.get('text', '')
                context_parts.append(f"\n### RAPORT: {period} ###")
                context_parts.append(text[:8000])  # Limit na raport
                context_parts.append("### KONIEC RAPORTU ###\n")
        
        # Dodaj historię konwersacji
        if chat_history:
            context_parts.append("\n--- HISTORIA KONWERSACJI ---")
            for msg in chat_history[-10:]:
                role_label = "Użytkownik" if msg.role == MessageRole.USER else "Asystent"
                context_parts.append(f"{role_label}: {msg.content}")
            context_parts.append("--- KONIEC HISTORII ---\n")
        
        return "\n".join(context_parts)
    
    async def generate_response(
        self,
        user_message: str,
        company_name: str,
        all_reports_text: List[Dict[str, str]] = None,
        chat_history: List[ChatMessage] = None
    ) -> Dict[str, any]:
        """Generuj odpowiedź na podstawie WSZYSTKICH raportów firmy"""
        
        try:
            if chat_history is None:
                chat_history = []
            if all_reports_text is None:
                all_reports_text = []
            
            context = self._prepare_context(company_name, all_reports_text, chat_history)
            full_prompt = f"{context}\n\nUżytkownik: {user_message}\n\nAsystent:"
            
            response = self.model.generate_content(full_prompt)
            
            return {
                "success": True,
                "response": response.text,
                "suggestions": self._generate_suggestions(user_message, len(all_reports_text))
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"Przepraszam, wystąpił błąd: {str(e)}",
                "suggestions": []
            }
    
    def _generate_suggestions(self, last_question: str, reports_count: int) -> List[str]:
        """Generuj sugestie pytań uwzględniając dostępność wielu raportów"""
        
        # Jeśli jest więcej niż 1 raport, sugeruj analizy trendów
        if reports_count > 1:
            base_suggestions = [
                "Porównaj wyniki między kwartałami",
                "Jaki jest trend przychodów w czasie?",
                "Jak zmieniało się zadłużenie?",
                "Pokaż kluczowe wskaźniki w układzie czasowym"
            ]
        else:
            base_suggestions = [
                "Jakie są główne wskaźniki rentowności?",
                "Jaka jest sytuacja zadłużenia spółki?",
                "Podsumuj kluczowe informacje",
                "Jakie są mocne strony firmy?"
            ]
        
        # Kontekstowe sugestie
        if "przychody" in last_question.lower() or "revenue" in last_question.lower():
            if reports_count > 1:
                return [
                    "Jaki był wzrost przychodów rok do roku?",
                    "Pokaż trend przychodów w ostatnich okresach",
                    "Które kwartały były najlepsze?"
                ]
            else:
                return [
                    "Jakie są główne źródła przychodów?",
                    "Jak przychody wpłynęły na zysk?",
                    "Jaka jest marża na przychodach?"
                ]
        elif "zysk" in last_question.lower() or "profit" in last_question.lower():
            if reports_count > 1:
                return [
                    "Jak zmienia się marża zysku w czasie?",
                    "Porównaj rentowność między okresami",
                    "Kiedy firma była najbardziej rentowna?"
                ]
            else:
                return [
                    "Jaka jest marża zysku netto?",
                    "Co wpłynęło na zmianę zysku?",
                    "Porównaj zysk operacyjny z netto"
                ]
        
        return base_suggestions[:3]
    
    async def generate_summary(self, report_text: str) -> str:
        """Wygeneruj podsumowanie pojedynczego raportu"""
        
        try:
            prompt = f"""Na podstawie poniższego raportu finansowego wygeneruj zwięzłe podsumowanie (max 200 słów) zawierające:
1. Okres raportu
2. Kluczowe wyniki finansowe (przychody, zysk)
3. Najważniejsze wnioski

RAPORT:
{report_text[:10000]}

PODSUMOWANIE:"""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Nie udało się wygenerować podsumowania: {str(e)}"
    
    async def analyze_company_trends(
        self, 
        company_name: str,
        all_reports_data: List[Dict]
    ) -> Dict:
        """Przeanalizuj trendy firmy na podstawie wszystkich raportów"""
        
        try:
            # Przygotuj dane do analizy
            reports_summary = []
            for report in all_reports_data:
                period = report.get('period', 'Nieznany')
                metrics = report.get('metrics', {})
                reports_summary.append(f"Okres: {period}, Dane: {metrics}")
            
            reports_str = "\n".join(reports_summary)
            
            prompt = f"""Przeanalizuj trendy finansowe firmy {company_name} na podstawie raportów:

{reports_str}

Podaj:
1. Trend przychodów (rosnący/malejący/stabilny)
2. Trend rentowności
3. Zmiana zadłużenia
4. Kluczowe obserwacje
5. Ocenę ogólną sytuacji

ANALIZA TRENDÓW:"""
            
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "analysis": response.text,
                "reports_analyzed": len(all_reports_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_company_info(self, text: str) -> Dict[str, any]:
        """Wyodrębnij informacje o firmie z tekstu raportu"""
        try:
            prompt = f"""Przeanalizuj początek raportu finansowego i wyodrębnij dane firmy w formacie JSON.
            
            TEKST:
            {text[:5000]}
            
            Zwróć TYLKO obiekt JSON w formacie:
            {{
                "name": "Pełna nazwa firmy",
                "ticker": "Symbol giełdowy (jeśli jest, inaczej null)",
                "industry": "Branża (wywnioskuj z opisu)",
                "description": "Krótki opis działalności (max 1 zdanie)",
                "report_period": "Okres raportu (np. Q3 2024, 2023)",
                "report_year": 2024 (rok jako int),
                "report_quarter": 3 (kwartał jako int 1-4 lub null dla rocznego)
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Clean response to ensure valid JSON
            json_str = response.text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3]
            elif json_str.startswith("```"):
                json_str = json_str[3:-3]
                
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Error extracting company info: {e}")
            return None