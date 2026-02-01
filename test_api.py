"""
Skrypt testowy - NOWY WORKFLOW z firmami
Uruchom po starcie serwera: python test_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test czy serwer działa"""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_stats():
    """Test statystyk systemu"""
    print("=" * 60)
    print("TEST 2: System Stats")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_create_company():
    """Test tworzenia firmy"""
    print("=" * 60)
    print("TEST 3: Create Company")
    print("=" * 60)
    
    company_data = {
        "name": "PKN Orlen",
        "ticker": "PKN",
        "description": "Największy koncern paliwowy w Polsce",
        "industry": "Energia i paliwa"
    }
    
    response = requests.post(f"{BASE_URL}/api/companies/", json=company_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"Created company:")
        print(f"  ID: {data['id']}")
        print(f"  Name: {data['name']}")
        print(f"  Ticker: {data['ticker']}")
        return data['id']
    elif response.status_code == 400:
        print("Company already exists - fetching existing...")
        companies = requests.get(f"{BASE_URL}/api/companies/").json()
        for company in companies:
            if company['name'] == company_data['name']:
                print(f"  ID: {company['id']}")
                print(f"  Name: {company['name']}")
                return company['id']
    else:
        print(f"Error: {response.text}")
        return None
    print()


def test_get_companies():
    """Test pobierania listy firm"""
    print("=" * 60)
    print("TEST 4: Get All Companies")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/companies/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        companies = response.json()
        print(f"Total companies: {len(companies)}")
        for company in companies:
            print(f"  - {company['name']} ({company['ticker']}) - {company['reports_count']} reports")
    print()


def test_upload_report(company_id, file_path):
    """Test uploadu raportu dla firmy"""
    print("=" * 60)
    print(f"TEST 5: Upload Report for Company ID {company_id}")
    print("=" * 60)
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/pdf')}
            data = {
                'company_id': company_id,
                'report_type': 'quarterly'
            }
            response = requests.post(
                f"{BASE_URL}/api/reports/upload",
                files=files,
                data=data
            )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Report uploaded successfully:")
            print(f"  Report ID: {data['id']}")
            print(f"  Company: {data['company_name']}")
            print(f"  Period: {data.get('report_period', 'N/A')}")
            print(f"  Status: {data['status']}")
            return data['id']
        else:
            print(f"Error: {response.text}")
            return None
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        print("   Skip this test if you don't have a PDF file yet")
        return None
    print()


def test_get_company_details(company_id):
    """Test pobierania szczegółów firmy z raportami"""
    print("=" * 60)
    print(f"TEST 6: Get Company Details (ID: {company_id})")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/companies/{company_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Company: {data['name']}")
        print(f"Ticker: {data['ticker']}")
        print(f"Industry: {data['industry']}")
        print(f"Reports count: {data['reports_count']}")
        if data['reports']:
            print("\nReports:")
            for report in data['reports']:
                print(f"  - {report['report_period']} ({report['report_type']}) - {report['status']}")
    print()


def test_chat_with_company(company_id):
    """Test konwersacji z chatbotem dla firmy"""
    print("=" * 60)
    print(f"TEST 7: Chat with AI about Company ID {company_id}")
    print("=" * 60)
    
    messages = [
        "Cześć! Co możesz mi powiedzieć o tej firmie?",
        "Jakie były przychody w ostatnim okresie?",
        "Porównaj wyniki między dostępnymi raportami",
        "Jakie są trendy w czasie?"
    ]
    
    session_id = None
    
    for i, message in enumerate(messages, 1):
        print(f"\n[{i}] User: {message}")
        
        payload = {
            "message": message,
            "company_id": company_id,
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data['session_id']
            print(f"[{i}] Assistant: {data['response'][:300]}...")
            print(f"    Company: {data['company_name']}")
            print(f"    Reports used: {data['reports_used']}")
            if data.get('suggestions'):
                print(f"    Suggestions: {data['suggestions'][:2]}")
        else:
            print(f"Error: {response.text}")
            break
    
    print()
    return session_id


def test_analyze_company(company_id):
    """Test analizy trendów firmy"""
    print("=" * 60)
    print(f"TEST 8: Analyze Company Trends (ID: {company_id})")
    print("=" * 60)
    
    response = requests.post(f"{BASE_URL}/api/chat/analyze/{company_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Company: {data['company_name']}")
        print(f"Reports analyzed: {data['reports_analyzed']}")
        
        # Pobieranie wyników z zagnieżdżonego słownika 'result'
        result = data.get('result', {})
        analysis_text = result.get('analysis', 'Brak treści analizy')
        
        # Opcjonalnie: Wyświetlanie okresów, jeśli są w 'result', jeśli nie - pomijamy
        if 'reports_periods' in result:
             print(f"Periods: {result['reports_periods']}")
             
        print(f"\nAnalysis:\n{analysis_text[:400]}...")
    else:
        print(f"Error: {response.text}")
    print()


def main():
    print("\n" + "=" * 60)
    print("FINANCIAL CHATBOT API - FULL WORKFLOW TEST")
    print("=" * 60 + "\n")
    
    # Test 1: Health check
    test_health_check()
    
    # Test 2: Stats
    test_stats()
    
    # Test 3: Utwórz firmę
    company_id = test_create_company()
    if not company_id:
        print("❌ Failed to create/get company. Stopping tests.")
        return
    
    # Test 4: Lista firm
    test_get_companies()
    
    # Test 5: Upload raportu (opcjonalny - potrzebny PDF)
    test_file = "test_report.pdf"
    report_id = test_upload_report(company_id, test_file)
    
    # Test 6: Szczegóły firmy
    test_get_company_details(company_id)
    
    # Test 7: Chat z AI
    if report_id:
        session_id = test_chat_with_company(company_id)
        
        # Test 8: Analiza trendów
        test_analyze_company(company_id)
    else:
        print("⚠️  No reports uploaded - skipping chat and analysis tests")
        print("   Upload a PDF report to test the full workflow")
    
    # Final stats
    print("\n" + "=" * 60)
    print("FINAL STATS")
    print("=" * 60)
    test_stats()
    
    print("\n✅ All tests completed!\n")


if __name__ == "__main__":
    main()