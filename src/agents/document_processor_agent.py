"""
Document Processor Agent
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PyPDF2 import PdfReader
except ImportError:  # pragma: no cover - graceful degradation in case dependency is missing
    PdfReader = None  # type: ignore[assignment]

from .base_agent import AgentError, BaseAgent

logger = logging.getLogger(__name__)


class DocumentProcessorAgent(BaseAgent):
    """UAE document processing agent"""

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    MIN_TEXT_CHARACTERS = 40

    def __init__(self):
        super().__init__("document_processor")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process UAE documents"""
        try:
            baseline = self._rule_based_result(input_data)
            documents = input_data.get("documents", [])
            document_insights, scanned_images = self._collect_document_insights(documents)
            baseline["document_insights"] = document_insights

            if self.llm_client and getattr(self.llm_client, "available", False):
                llm_result = await self._analyze_with_llm(
                    input_data,
                    document_insights=document_insights,
                    scanned_images=scanned_images,
                )
                if llm_result:
                    baseline = self._merge_llm_results(baseline, llm_result, document_insights)

            await self.log_processing(input_data, baseline, success=True)
            return baseline

        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            await self.log_processing(input_data, {}, success=False, error_message=error_msg)
            raise AgentError(error_msg)

    def _rule_based_result(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        applicant_name = input_data.get("personal_info", {}).get("full_name", "Unknown")
        documents = input_data.get("documents", []) or []
        processed_docs = []
        extracted_data = {
            "emirates_id": {
                "id_number": input_data.get("personal_info", {}).get("emirates_id", ""),
                "name": applicant_name,
                "confidence": 0.9,
            },
            "bank_statement": {
                "monthly_income": input_data.get("employment_info", {}).get("monthly_salary", 0),
                "monthly_expenses": None,
                "stability_score": 80,
            },
        }

        for doc in documents:
            doc_type = doc.get("document_type")
            if doc_type:
                processed_docs.append(doc_type.lower())
                if doc_type.lower() not in extracted_data:
                    extracted_data[doc_type.lower()] = {
                        "filename": doc.get("filename"),
                        "status": doc.get("status"),
                    }

        processed_set = sorted(set(processed_docs)) or ["emirates_id", "bank_statement"]
        documents_valid = bool(processed_docs)

        return {
            "success": True,
            "documents_processed": processed_set,
            "documents_valid": documents_valid,
            "extracted_data": extracted_data,
            "analysis_source": "rule_based",
        }

    async def _analyze_with_llm(
        self,
        input_data: Dict[str, Any],
        document_insights: List[Dict[str, Any]],
        scanned_images: List[str],
    ) -> Dict[str, Any] | None:
        personal_info = input_data.get("personal_info", {})
        employment_info = input_data.get("employment_info", {})

        context = """
You are validating documents for UAE social support applications. Assess Emirates ID,
bank statements, and salary certificates for authenticity, data consistency, and
potential concerns. Return scores between 0 and 1.
"""

        prompt = f"""
Review the following application details and summarise document findings:

Applicant: {personal_info.get('full_name', 'Unknown')}
Emirates ID: {personal_info.get('emirates_id', 'N/A')}
Emirate: {personal_info.get('emirate', 'dubai')}
Employment Status: {employment_info.get('employment_status', 'unknown')}
Monthly Salary: {employment_info.get('monthly_salary', 0)}

Required JSON fields:
{{
    "success": bool,
    "documents_processed": list[str],
    "documents_valid": bool,
    "authenticity_scores": {{"emirates_id": float, "financial_documents": float}},
    "issues_found": list[str],
    "extracted_data": dict,
    "overall_confidence": float
}}
"""

        document_summary = self._build_document_summary(document_insights)
        if document_summary:
            prompt = f"{prompt}\nDocument Details:\n{document_summary}"

        expected_shape = {
            "success": True,
            "documents_processed": ["string"],
            "documents_valid": True,
            "authenticity_scores": {"emirates_id": 0.0, "financial_documents": 0.0},
            "issues_found": ["string"],
            "extracted_data": {},
            "overall_confidence": 0.0,
        }

        try:
            llm_payload = await self.llm_analyze(
                prompt,
                context,
                output_format=expected_shape,
                images=scanned_images or None,
            )
            if isinstance(llm_payload, dict) and llm_payload.get("success") is not False:
                return llm_payload
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM document analysis failed: %s", exc)

        return None

    def _merge_llm_results(
        self,
        baseline: Dict[str, Any],
        llm_result: Dict[str, Any],
        document_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        merged = baseline.copy()

        merged["documents_processed"] = llm_result.get(
            "documents_processed", baseline.get("documents_processed", [])
        )
        merged["documents_valid"] = llm_result.get("documents_valid", baseline.get("documents_valid", True))
        merged["extracted_data"] = llm_result.get("extracted_data", baseline.get("extracted_data", {}))

        if "authenticity_scores" in llm_result:
            merged["authenticity_scores"] = llm_result["authenticity_scores"]
        if "issues_found" in llm_result:
            merged["issues_found"] = llm_result["issues_found"]
        if "overall_confidence" in llm_result:
            merged["overall_confidence"] = llm_result["overall_confidence"]

        merged["analysis_source"] = "llm"
        if document_insights:
            merged["document_insights"] = document_insights
        return merged

    def _collect_document_insights(
        self, documents: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        insights: List[Dict[str, Any]] = []
        scanned_images: List[str] = []

        for doc in documents:
            doc_type = doc.get("document_type", "document")
            filename = doc.get("filename")
            status = doc.get("status")
            file_path = doc.get("file_path")
            snippet: Optional[str] = None
            scanned = False
            resolved_path: Optional[Path] = Path(file_path) if file_path else None

            if resolved_path and resolved_path.is_file():
                suffix = resolved_path.suffix.lower()
                if suffix == ".pdf":
                    extracted_text = self._extract_text_from_pdf(resolved_path)
                    if extracted_text and len(extracted_text.strip()) >= self.MIN_TEXT_CHARACTERS:
                        snippet = extracted_text.strip()[:400]
                    else:
                        scanned = True
                elif self._is_image_file(resolved_path):
                    scanned = True

            if scanned and resolved_path:
                scanned_images.append(str(resolved_path))

            insights.append(
                {
                    "document_type": doc_type,
                    "filename": filename,
                    "status": status,
                    "scanned": scanned,
                    "snippet": snippet,
                }
            )

        return insights, scanned_images

    def _build_document_summary(self, insights: List[Dict[str, Any]]) -> str:
        lines = []
        for insight in insights:
            parts = [f"- {insight['document_type']}"]
            if insight.get("filename"):
                parts.append(f"({insight['filename']})")
            if insight.get("scanned"):
                parts.append("[scanned document]")
            snippet = insight.get("snippet")
            if snippet:
                sanitized = snippet.replace("\n", " ").strip()
                parts.append(f": {sanitized[:200].strip()}")
            lines.append(" ".join(parts))
        return "\n".join(lines)

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        if PdfReader is None:
            return ""
        if not pdf_path.is_file():
            return ""

        try:
            reader = PdfReader(pdf_path)
            text_parts: List[str] = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            return "\n".join(text_parts).strip()
        except Exception as exc:
            logger.debug("PDF text extraction failed (%s): %s", pdf_path, exc)
            return ""

    def _is_image_file(self, path: Path) -> bool:
        return path.suffix.lower() in self.IMAGE_EXTENSIONS
