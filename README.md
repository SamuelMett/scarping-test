# IEP PDF Generator

Generates IEP compliance reports, parent meeting notices, and case manager caseload reports as PDFs from an Excel file. **All data is fake test data.**

## Setup
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac
pip install -r requirements.txt
```

## Run
```
python iep_pdf_generator.py
```
PDFs are saved to `output_pdfs/` (compliance, parent_notices, caseloads).

## Settings
Edit the top of `iep_pdf_generator.py`:
- `NUM_STUDENTS`: number of students to process (`None` = all)
- `TODAY`: reference date for status calculations
- `DUE_SOON_DAYS`: window for the "Due Soon" status

## Regenerate test data
```
python generate_test_data.py
```

## Files
```
├── .gitignore
├── README.md
├── requirements.txt
├── iep_pdf_generator.py
├── generate_test_data.py
└── IEP_Test_Data.xlsx     (commit it, or regenerate it with the script)
```
