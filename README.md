Thanks for the clarification! Here's your clean and updated `README.md` without any license references:

---

## 🌈 Rainbow Money PFHC

**Personal Finance Health Calculator**

A robust backend engine to analyze a user’s personal financial health using financial ratios, configurable benchmarks, and optionally LLM-generated advice. Built with FastAPI, Pydantic, and modern Python tooling.

---

### 🚀 Features

* **📈 Metric-Based Evaluation**

  * Savings to Income Ratio
  * Expense to Income Ratio
  * Debt to Income Ratio
  * Liquidity Ratio
  * Emergency Fund Ratio
  * Housing Cost Ratio
  * Insurance Coverage
  * Retirement Readiness
  * Net Worth Adequacy

* **🔍 Personalized Insights**

  * Benchmarks based on city tier & income levels
  * Rupee-gap-based improvement suggestions
  * Commendations for well-performing areas

* **📝 Report Generation**

  * PDF reports via Jinja2 + PDFKit
  * Optional LLM-driven detailed narratives
  * Modes: `basic` (rule-based) and `advanced` (LLM-enhanced)

* **🧪 Performance Tracing**

  * Tracemalloc-based memory usage profiling
  * Execution time logging
  * Rotating file + console logging

* **📦 Modular Design**

  * Clean project structure for maintainability
  * LLM client abstractions for easy swapping
  * CLI test mode for local profiling

---

### 📁 Project Structure

```
PFHC
├── apis/                       # LLM client wrappers (e.g. Together, OpenRouter)
├── assets/                     # Static files (if any)
├── config/                     # Feature flags and constants
├── core/                       # Core financial logic and metric computation
├── data/                       # Test profiles and benchmark files
├── models/                     # Pydantic models
├── templates/                  # Jinja2 templates (PDF + prompts)
├── utils/                      # Logger, PDF utils, prompt formatter
├── main.py                     # FastAPI entrypoint + CLI testing
├── requirements.txt
└── README.md
```

---

### ⚙️ Setup Instructions

1. **Clone the Repo**

   ```bash
   git clone https://github.com/Aryan-Bodhe/Rainbow-Money-PFHC.git
   cd Rainbow-Money-PFHC
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI Server**

   ```bash
   uvicorn main:app --reload
   ```

---

### 📡 API Usage

#### Endpoint: `POST /personal-finance-health-analyzer`

* **Request Body**:

  ```json
  {
    "mode": "advanced",
    "data": {
      "age": 32,
      "gender": "Female",
      "city": "Mumbai",
      "monthly_income": 120000,
      ...
    }
  }
  ```

* **Modes**:

  * `"basic"`: Rule-based engine
  * `"advanced"`: Adds LLM-generated reasoning

* **Response**: JSON report with:

  * Commendations
  * Improvement points
  * (Optional) PDF path

Access Swagger UI:
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 🧪 Test Locally via CLI

```bash
python main.py
```

* Loads sample profile from `data/test_data/average_profile.json`
* Runs full analysis
* Outputs result to `sample_output.json`

---

### ⚙️ Configuration

Controlled via `config/config.py`:

| Setting            | Purpose                    |
| ------------------ | -------------------------- |
| `GENERATE_REPORT`  | Toggle PDF output          |
| `USE_LLM`          | Use LLM-based explanation  |
| `ENABLE_LOGGING`   | Turn logs on/off           |
| `CREATE_HISTOGRAM` | Attach visuals in response |

---
