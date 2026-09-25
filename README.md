# ClearanceX 🚢

**ClearanceX** is an Intelligent Decision Support System that automates the ingestion, reconciliation, and validation of complex shipping dossiers for both **Imports** and **Exports**. Built with **Explainable AI (XAI)** at its core, it acts as a copilot for shipping executives to instantly flag discrepancies, verify data via traceable visual attributions, and generate one-click ASYCUDA-compliant export files for Sri Lanka Customs.

## 🎯 The Problem
In the apparel manufacturing sector, clearing imported raw materials or exporting finished goods requires compiling a detailed Customs Declaration (CUSDEC) via the ASYCUDA system. This manual process relies on unstructured, multi-page shipping dossiers (Commercial Invoices, Packing Lists, Airway Bills, etc.), leading to frequent discrepancies, human error, rejected declarations, and severe financial penalties (e.g., port demurrage or bank payment freezes).

## 🚀 The Solution
ClearanceX mitigates these risks by providing an automated pipeline that:
- Reads unstructured supply chain documents using LayoutLMv3 and Spatial OCR.
- Extracts multi-line tabular items and header-level metadata.
- Cross-references values (e.g., Gross Weight, Package Count, Incoterms) across different documents to flag mismatches.
- Compiles validated data into standard ASYCUDA-compliant XML/TXT files for Direct Trader Input (DTI) bulk upload.

## ✨ Key Features
- **Document Ingestion & OCR:** Automatic classification of shipping documents with $\ge 95\%$ confidence and bounding box coordinate extraction.
- **Entity Extraction & Normalization:** Extracts critical details like Consignee details, Incoterms, Gross/Net weights, and item descriptions, normalizing varying terminologies into canonical forms.
- **Cross-Document Reconciliation Engine:** Compares data points across multiple documents (e.g., Packing List vs. Transport Documents) and highlights variances.
- **Explainable AI (XAI) Interface:** 
  - **Visual Attribution:** Split-screen view highlighting the exact location in the original PDF source.
  - **Conflict Explanations:** Natural language explanations and actionable recommendations for every mismatch.
  - **Confidence Scoring:** Color-coded confidence scores (Green $\ge 90\%$, Yellow $70\text{--}89\%$, Red $< 70\%$) for extracted values.
- **One-Click ASYCUDA Export:** Generates bulk upload files (XML/TXT) to eliminate manual copy-pasting during customs declarations.

## 🏗️ Tech Stack
- **Frontend:** React-based dual-pane UI for visual validation and decision support.
- **Backend:** Python (FastAPI) for high-performance API endpoints.
- **AI/ML Core:** Vision-Language Models (LayoutLMv3), Spatial OCR.
- **Database:** PostgreSQL for structured data persistence.

## 🛠️ Getting Started

### Prerequisites
- Node.js & npm (for Frontend)
- Python 3.9+ (for Backend)
- PostgreSQL

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ClearanceX
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 📜 License
This project is licensed under the terms of the LICENSE file included in the repository.
