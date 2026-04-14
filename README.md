# NPTEL Principles of Industrial Engineering - Quiz Practice

Python-based practice system for:
- Week-wise tests (Week 1 to Week 12)
- Random test series (can include all 120 questions)
- No negative marking
- Answers shown only at the end
- Option order shuffled every attempt

## Project Structure

- `quiz_app.py` - Streamlit quiz app
- `data/questions.json` - Main question bank (all weeks combined)
- `data/questions.sample.json` - Expected question format sample
- `tools/pdf_to_questions.py` - PDF-to-JSON extractor (first-pass automation)

## 1) Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Add Your 12 PDFs

Place all assignment PDFs in a folder, for example:

`data/raw_pdfs/`

Recommended naming:
- `week01.pdf`
- `week02.pdf`
- ...
- `week12.pdf`

## 3) Build Question Bank

Run:

```bash
python tools/pdf_to_questions.py --pdf-dir data/raw_pdfs --output data/questions.json
```

Then quickly verify `data/questions.json` for any formatting issues.  
Target count is `120` questions total.

Current setup note:
- Assignments 1-11 are extracted from PDFs with embedded key cues.
- Week 12 is currently populated with concept-verified answers (official key pending).

## 4) Start Quiz App

```bash
streamlit run quiz_app.py
```

## Notes

- Random mode can be set to all questions (default max count).
- Each fresh attempt can reshuffle options automatically.
- You can retake instantly with new shuffling.
