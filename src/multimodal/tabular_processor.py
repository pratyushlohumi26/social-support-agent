"""
Tabular data processing
"""

import pandas as pd
import numpy as np
import io
import PyPDF2
from typing import Dict, List, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)

class TabularProcessor:
    """Advanced tabular data processing"""

    def __init__(self):
        self.bank_patterns = {
            "emirates_nbd": {
                "account_pattern": r"Account No[.:]\s*(\d{4}-\d{4}-\d{4}-\d{4})",
                "balance_pattern": r"Balance[.:]\s*AED\s*([0-9,]+\.\d{2})"
            }
        }

    async def extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""

    async def read_excel_csv(self, file_data: bytes, file_type: str) -> pd.DataFrame:
        """Read Excel or CSV file"""
        try:
            if file_type.lower() == "xlsx":
                return pd.read_excel(io.BytesIO(file_data))
            elif file_type.lower() == "csv":
                return pd.read_csv(io.BytesIO(file_data))
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"File reading failed: {e}")
            return pd.DataFrame()

    async def analyze_bank_transactions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze bank transaction patterns"""
        try:
            analysis = {
                "total_transactions": len(df),
                "income_transactions": [],
                "expense_transactions": [],
                "stability_indicators": {}
            }

            # Find amount columns
            amount_cols = [col for col in df.columns if any(keyword in col.lower() 
                          for keyword in ['amount', 'debit', 'credit'])]

            if amount_cols:
                amount_col = amount_cols[0]
                df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')

                # Separate income and expenses
                income_transactions = df[df[amount_col] > 0][amount_col].tolist()
                expense_transactions = df[df[amount_col] < 0][amount_col].abs().tolist()

                analysis["income_transactions"] = income_transactions
                analysis["expense_transactions"] = expense_transactions

                # Stability indicators
                if income_transactions:
                    analysis["stability_indicators"]["income_consistency"] = 1 - (
                        np.std(income_transactions) / np.mean(income_transactions)
                    ) if np.mean(income_transactions) > 0 else 0
                    analysis["stability_indicators"]["avg_monthly_income"] = np.mean(income_transactions)

            return analysis

        except Exception as e:
            logger.error(f"Transaction analysis failed: {e}")
            return {"error": str(e)}
