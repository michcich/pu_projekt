import PyPDF2
import pdfplumber
import re
from typing import Dict, Optional, List


class PDFProcessor:
    def __init__(self):
        pass
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2 as primary method"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text with PyPDF2: {e}")
            # Fallback to pdfplumber
            return self._extract_with_pdfplumber(file_path)
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Fallback method using pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text with pdfplumber: {e}")
            return ""
    
    def extract_tables(self, file_path: str) -> List[List]:
        """Extract tables from PDF using pdfplumber"""
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            print(f"Error extracting tables: {e}")
        return tables
    
    def extract_company_name(self, text: str) -> Optional[str]:
        """Try to extract company name from report text"""
        # Look for common patterns
        patterns = [
            r"(?:Spółka|Firma|Company):\s*([A-ZĄĆĘŁŃÓŚŹŻ\w\s\-\.]+)",
            r"([A-ZĄĆĘŁŃÓŚŹŻ\w\s]+)\s+S\.?A\.?",
            r"Raport\s+(?:roczny|kwartalny|okresowy)\s+([A-ZĄĆĘŁŃÓŚŹŻ\w\s]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 3 and len(company) < 100:
                    return company
        
        return None
    
    def extract_report_period(self, text: str) -> Optional[str]:
        """Try to extract report period from text"""
        patterns = [
            r"(?:za|okres|period)?\s*(\d{4})\s*(?:rok|year)",
            r"Q([1-4])\s*(\d{4})",
            r"(\d{1,2})\.(\d{4})",
            r"(?:styczeń|luty|marzec|kwiecień|maj|czerwiec|lipiec|sierpień|wrzesień|październik|listopad|grudzień)\s+(\d{4})",
        ]

        best_match = None
        min_start = float('inf')

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.start() < min_start:
                    min_start = match.start()
                    best_match = match.group(0)
        
        return best_match
    
    def extract_financial_metrics(self, text: str) -> Dict[str, Optional[float]]:
        """Extract basic financial metrics from text"""
        metrics = {
            "revenue": None,
            "net_income": None,
            "total_assets": None,
            "total_liabilities": None,
            "equity": None,
        }
        
        # Patterns for financial data
        # Supports: 1 234 567, 1.234.567, 1,234,567
        # Supports units: tys, mln, mld
        patterns = {
            "revenue": [
                r"(?:przychody|revenues?)[\s:]+(?:ze\s+sprzedaży\s+)?[\s\w]*?[\s:]+([\d\s\.,]+)\s*(?:mln|mld|tys)?\s*(?:PLN|zł)",
                r"(?:sprzedaż|sales)[\s:]+[\s\w]*?[\s:]+([\d\s\.,]+)\s*(?:mln|mld|tys)?"
            ],
            "net_income": [
                r"(?:zysk|wynik)\s+(?:netto|net)[\s:]+[\s\w]*?[\s:]+([\d\s\.,\-]+)\s*(?:mln|mld|tys)?",
                r"(?:profit|net\s+income)[\s:]+[\s\w]*?[\s:]+([\d\s\.,\-]+)\s*(?:mln|mld|tys)?"
            ],
            "total_assets": [
                r"(?:aktywa|assets)\s+(?:razem|total)[\s:]+[\s\w]*?[\s:]+([\d\s\.,]+)\s*(?:mln|mld|tys)?",
                r"(?:suma|total)\s+aktywów[\s:]+[\s\w]*?[\s:]+([\d\s\.,]+)\s*(?:mln|mld|tys)?"
            ],
        }
        
        for metric, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value_str = match.group(1).strip()
                        unit_match = re.search(r"(mln|mld|tys)", match.group(0), re.IGNORECASE)
                        unit = unit_match.group(1).lower() if unit_match else ""
                        
                        # Clean number string
                        # Remove spaces
                        clean_val = value_str.replace(" ", "")
                        # Handle decimal separator (comma to dot if needed)
                        if "," in clean_val and "." not in clean_val:
                            clean_val = clean_val.replace(",", ".")
                        elif "," in clean_val and "." in clean_val:
                             # Assume 1,234.56 or 1.234,56 - remove thousands separator
                             if clean_val.index(",") < clean_val.index("."):
                                 clean_val = clean_val.replace(",", "")
                             else:
                                 clean_val = clean_val.replace(".", "").replace(",", ".")
                        
                        value = float(clean_val)
                        
                        # Apply multiplier based on unit
                        if unit == "mld":
                            value *= 1_000_000_000
                        elif unit == "mln":
                            value *= 1_000_000
                        elif unit == "tys":
                            value *= 1_000
                        # If no unit found, assume it might be in thousands if it's a financial report (common convention)
                        # But safer to leave as is or assume base unit if not specified.
                        # Let's assume if it's a small number (<10000) in a big company report, it might be in millions, 
                        # but regex is risky here. Let's stick to explicit units or raw number.
                        
                        metrics[metric] = value
                        break
                    except (ValueError, AttributeError):
                        continue
        
        return metrics
    
    def process_report(self, file_path: str) -> Dict:
        """Complete processing of a PDF report"""
        result = {
            "text": "",
            "company_name": None,
            "report_period": None,
            "metrics": {},
            "tables_count": 0,
            "success": False,
            "error": None
        }
        
        try:
            # Extract text
            text = self.extract_text(file_path)
            if not text:
                result["error"] = "Failed to extract text from PDF"
                return result
            
            result["text"] = text
            
            # Extract metadata
            result["company_name"] = self.extract_company_name(text)
            result["report_period"] = self.extract_report_period(text)
            
            # Extract metrics
            result["metrics"] = self.extract_financial_metrics(text)
            
            # Count tables
            tables = self.extract_tables(file_path)
            result["tables_count"] = len(tables)
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result