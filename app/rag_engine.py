import os
from typing import List, Dict, Any, Optional
from pypdf import PdfReader

class ParcelPilotKnowledgeBase:
    def __init__(self, docs_dir: str = "data/docs"):
        self.docs_dir = docs_dir
        self.documents: List[Dict[str, Any]] = []
        self._load_and_tag_documents()

    def _load_and_tag_documents(self):
        for filename in sorted(os.listdir(self.docs_dir)):
            if not filename.endswith(".pdf"):
                continue

            file_path = os.path.join(self.docs_dir, filename)
            reader = PdfReader(file_path)
            content = " ".join([page.extract_text() or "" for page in reader.pages])

            # Classify authority tiers
            doc_type = "general"
            authority_level = 2
            account_id = None

            if "DEPRECATED" in filename.upper():
                doc_type = "deprecated"
                authority_level = 0  # Excluded from current queries
            elif "ENTERPRISE_AGREEMENT" in filename.upper() or "SERVICE_AGREEMENT" in filename.upper():
                doc_type = "customer_agreement"
                authority_level = 4  # Highest priority
                if "NORTHSTAR" in filename.upper():
                    account_id = "ACCT-001"
                elif "LUMENWORKS" in filename.upper():
                    account_id = "ACCT-002"
            elif "SOP" in filename.upper() or "CURRENT" in filename.upper():
                doc_type = "policy_current"
                authority_level = 3
            elif "PRODUCT_OPERATIONS" in filename.upper():
                doc_type = "product_guide"
                authority_level = 2

            self.documents.append({
                "filename": filename,
                "content": content,
                "doc_type": doc_type,
                "authority_level": authority_level,
                "account_id": account_id
            })

    def search(self, query: str, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        q_tokens = set(query.lower().split())

        for doc in self.documents:
            # Never return deprecated policy for active guidance
            if doc["doc_type"] == "deprecated":
                continue

            # Scope customer agreements strictly
            if doc["account_id"] and account_id and doc["account_id"] != account_id:
                continue

            doc_lower = doc["content"].lower()
            overlap_score = sum(1 for token in q_tokens if token in doc_lower)

            if overlap_score > 0:
                results.append({
                    "filename": doc["filename"],
                    "doc_type": doc["doc_type"],
                    "authority_level": doc["authority_level"],
                    "account_id": doc["account_id"],
                    "content": doc["content"],
                    "relevance_score": overlap_score
                })

        results.sort(key=lambda x: (x["authority_level"], x["relevance_score"]), reverse=True)
        return results