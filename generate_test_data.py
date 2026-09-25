"""
Generate fake IEP test data -> IEP_Test_Data.xlsx

  - 566 students, 11 schools, 46 case managers
  - each case manager works at one school, caseloads of 2-25 students (uneven)
  - grade level matches the school type (elementary K-5, middle 6-8, high 9-12)
  - DOB matches the grade level
  - all IEP due / reevaluation dates are in the future relative to BASE_DATE

Seeded, so every run produces the same file.
Run:  python generate_test_data.py
"""

import random
from datetime import date, timedelta

import pandas as pd

# ======================== SETTINGS ========================
OUTPUT_FILE = "IEP_Test_Data.xlsx"
SEED = 42
NUM_STUDENTS = 566
NUM_CASE_MANAGERS = 46
MIN_CASELOAD, MAX_CASELOAD = 2, 25
BASE_DATE = date(2026, 9, 24)   # all deadlines fall after this date
# ==========================================================

SCHOOLS = {
    "Oakwood Elementary School": "elementary",
    "Maple Grove Elementary School": "elementary",
    "Riverside Elementary School": "elementary",
    "Sunset Palms Elementary School": "elementary",
    "Cedar Hills Elementary School": "elementary",
    "Lakeview Middle School": "middle",
    "Pinecrest Middle School": "middle",
    "Harbor View Middle School": "middle",
    "Westfield High School": "high",
    "Northgate High School": "high",
    "Coral Bay High School": "high",
}

GRADES = {
    "elementary": ["K", "1", "2", "3", "4", "5"],
    "middle": ["6", "7", "8"],
    "high": ["9", "10", "11", "12"],
}

# IDEA categories, weighted roughly like national prevalence
DISABILITIES = {
    "Specific Learning Disability": 32,
    "Speech or Language Impairment": 19,
    "Other Health Impairment": 15,
    "Autism": 12,
    "Developmental Delay": 6,
    "Intellectual Disability": 6,
    "Emotional Disturbance": 5,
    "Multiple Disabilities": 2,
    "Hearing Impairment": 1,
    "Orthopedic Impairment": 1,
    "Visual Impairment": 0.5,
    "Traumatic Brain Injury": 0.5,
    "Deaf-Blindness": 0.2,
}

FIRST_NAMES = [
    "Liam", "Olivia", "Noah", "Emma", "Oliver", "Ava", "Elijah", "Sophia", "James", "Isabella",
    "William", "Mia", "Benjamin", "Charlotte", "Lucas", "Amelia", "Henry", "Harper", "Theodore",
    "Evelyn", "Mateo", "Abigail", "Jack", "Emily", "Levi", "Ella", "Sebastian", "Elizabeth",
    "Daniel", "Camila", "Michael", "Luna", "Alexander", "Sofia", "Owen", "Avery", "Asher", "Mila",
    "Samuel", "Aria", "Ethan", "Scarlett", "Leo", "Penelope", "Jackson", "Layla", "Ezra", "Chloe",
    "Aiden", "Victoria", "Muhammad", "Madison", "Luca", "Eleanor", "Isaiah", "Grace", "David",
    "Nora", "Joseph", "Riley", "Julian", "Zoey", "Gabriel", "Hannah", "Carter", "Lily", "Wyatt",
    "Aaliyah", "Diego", "Zara", "Malik", "Priya", "Andre", "Leah", "Santiago", "Maya", "Jayden",
    "Naomi", "Isaac", "Valentina", "Elias", "Ruby", "Josiah", "Stella", "Adrian", "Hazel",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
    "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez",
    "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Patel", "Kim", "Cohen", "Singh",
    "Chen", "Rossi", "Murphy", "Cooper", "Reyes", "Diaz", "Morales", "Ortiz", "Gutierrez",
    "Brooks", "Price", "Bennett", "Wood", "Ross", "Powell", "Jenkins", "Foster", "Reed",
]


def unique_names(rng, n):
    """n distinct 'Last, First' names."""
    names = set()
    while len(names) < n:
        names.add(f"{rng.choice(LAST_NAMES)}, {rng.choice(FIRST_NAMES)}")
    return list(names)


def caseload_sizes(rng):
    """Uneven caseload sizes, each in [MIN, MAX], summing to NUM_STUDENTS."""
    sizes = [MIN_CASELOAD] * NUM_CASE_MANAGERS
    weights = [rng.random() ** 2 + 0.02 for _ in sizes]   # skewed -> some big, some tiny
    for _ in range(NUM_STUDENTS - sum(sizes)):
        open_ = [i for i, s in enumerate(sizes) if s < MAX_CASELOAD]
        i = rng.choices(open_, weights=[weights[j] for j in open_])[0]
        sizes[i] += 1
    return sizes


def dob_for_grade(rng, grade):
    """Child is (grade + 5) years old on Sept 1 of the current school year."""
    age = 5 if grade == "K" else int(grade) + 5
    school_year_start = date(BASE_DATE.year if BASE_DATE.month >= 9 else BASE_DATE.year - 1, 9, 1)
    latest = school_year_start.replace(year=school_year_start.year - age)
    earliest = latest.replace(year=latest.year - 1) + timedelta(days=1)
    return earliest + timedelta(days=rng.randint(0, (latest - earliest).days))


def main():
    rng = random.Random(SEED)
    schools = list(SCHOOLS)

    # every school gets at least one case manager, the rest are assigned randomly
    cm_names = unique_names(rng, NUM_CASE_MANAGERS)
    cm_schools = schools + [rng.choice(schools) for _ in range(NUM_CASE_MANAGERS - len(schools))]
    rng.shuffle(cm_schools)

    student_names = unique_names(rng, NUM_STUDENTS)
    disabilities, dis_weights = list(DISABILITIES), list(DISABILITIES.values())

    rows = []
    for cm, school, size in zip(cm_names, cm_schools, caseload_sizes(rng)):
        for _ in range(size):
            grade = rng.choice(GRADES[SCHOOLS[school]])
            rows.append({
                "DOB": dob_for_grade(rng, grade),
                "Student Name": student_names[len(rows)],
                "Disability": rng.choices(disabilities, weights=dis_weights)[0],
                "IEP Due Date": BASE_DATE + timedelta(days=rng.randint(1, 365)),
                "IEP Reevaluation Date": BASE_DATE + timedelta(days=rng.randint(1, 3 * 365)),
                "School Name": school,
                "Grade Level": grade,
                "Case Manager": cm,
            })

    rng.shuffle(rows)
    df = pd.DataFrame(rows)
    for col in ["DOB", "IEP Due Date", "IEP Reevaluation Date"]:
        df[col] = pd.to_datetime(df[col])

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", date_format="MM/DD/YYYY",
                        datetime_format="MM/DD/YYYY") as writer:
        df.to_excel(writer, index=False, sheet_name="Students")
        ws = writer.sheets["Students"]
        for col, width in zip("ABCDEFGH", [12, 24, 30, 14, 20, 30, 11, 22]):
            ws.column_dimensions[col].width = width

    print(f"Wrote {len(df)} students, {df['School Name'].nunique()} schools, "
          f"{df['Case Manager'].nunique()} case managers -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
