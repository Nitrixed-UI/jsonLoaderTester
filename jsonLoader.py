import json
from typing import Optional
import csv
import os
from pathlib import Path

# File where student data is stored (next to this script)
DATA_FILE = Path(__file__).with_name("data.json")

# Load existing data or start with empty list
if DATA_FILE.exists():
    try:
        with DATA_FILE.open('r', encoding='utf-8') as file:
            data = json.load(file)
    except json.JSONDecodeError:
        data = {"students": []}
else:
    data = {"students": []}

def load_data(filepath: str = str(DATA_FILE)):
    """Load data from disk (create empty if missing)."""
    global data
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"students": []}
        save_data(filepath)
    except json.JSONDecodeError:
        pass  # keep old data if file is corrupt

def make_new_student(name, age, full_time):
    """Add a new student to memory."""
    new_student = {
        "id": len(data['students']) + 1,
        "name": name,
        "age": age,
        "full-time": full_time
    }
    data['students'].append(new_student)
    return new_student

def find_student(student_id):
    """Find a student by id."""
    for student in data['students']:
        if student['id'] == student_id:
            return student
    return None

def remove_student(student_id):
    """Delete a student by id."""
    global data
    data['students'] = [s for s in data['students'] if s['id'] != student_id]

def change_student_info(student_id, name=None, age=None, full_time=None):
    """Update fields for one student."""
    student = find_student(student_id)
    if student:
        if name is not None:
            student['name'] = name
        if age is not None:
            student['age'] = age
        if full_time is not None:
            student['full-time'] = full_time
        return student
    return None

def save_data(filepath: str = str(DATA_FILE)):
    """Write data to disk."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def clear_screen():
    """Clear console output."""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass

def pause(msg: str = "Press Enter to continue..."):  
    """Simple pause for user input."""
    try:
        input(msg)
    except EOFError:
        pass

def export_csv(csv_path: str = "students.csv") -> str:
    """Save students to CSV and return path."""
    load_data()
    fieldnames = ["id", "name", "age", "full-time"]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in data['students']:
            writer.writerow({k: s[k] for k in fieldnames})
    return os.path.abspath(csv_path)

def _parse_bool(val: str) -> bool:
    """Turn a text value into a bool."""
    v = val.strip().lower()
    return v in ("1", "true", "t", "yes", "y")

def import_csv(csv_path: str, mode: str = 'merge') -> int:
    """Read students from CSV (merge or replace)."""
    global data
    load_data()
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return 0
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        print("CSV empty.")
        return 0
    if mode == 'replace':
        new_list = []
        seen_ids = set()
        next_id = 1
        for r in rows:
            try:
                rid = int(r.get('id', ''))
            except ValueError:
                rid = None
            name = r.get('name', '').strip() or f"Student{next_id}"
            try:
                age = int(r.get('age', ''))
            except ValueError:
                age = 0
            full_time = _parse_bool(str(r.get('full-time', 'false')))
            if rid is None or rid in seen_ids:
                rid = next_id
            seen_ids.add(rid)
            next_id = max(next_id, rid + 1)
            new_list.append({"id": rid, "name": name, "age": age, "full-time": full_time})
        data['students'] = sorted(new_list, key=lambda s: s['id'])
        save_data()
        return len(new_list)
    # merge mode
    existing_ids = {s['id'] for s in data['students']}
    max_id = max(existing_ids) if existing_ids else 0
    added = 0
    for r in rows:
        try:
            rid = int(r.get('id', ''))
        except ValueError:
            rid = None
        if rid in existing_ids or rid is None:
            max_id += 1
            rid = max_id
        name = r.get('name', '').strip() or f"Student{rid}"
        try:
            age = int(r.get('age', ''))
        except ValueError:
            age = 0
        full_time = _parse_bool(str(r.get('full-time', 'false')))
        data['students'].append({"id": rid, "name": name, "age": age, "full-time": full_time})
        existing_ids.add(rid)
        added += 1
    save_data()
    return added

def format_student(student: dict) -> str:
    """Return a simple text line for a student."""
    return (f"ID: {student['id']} | Name: {student['name']} | Age: {student['age']} | "
            f"Full-time: {'Yes' if student['full-time'] else 'No'}")

def student_menu(student_id: int):
    """Menu for changing one student."""
    while True:
        load_data()
        clear_screen()
        student = find_student(student_id)
        if not student:
            print("Student removed.")
            return
        print("\nStudent -> " + format_student(student))
        print("[v]iew  [n]ame  [a]ge  [t]oggle full-time  [d]elete  [s]ave  [r]eload  [q]uit")
        choice = input("> ").strip().lower()
        if choice in ("v", "view"):
            print(format_student(student))
            pause()
        elif choice in ("n", "name"):
            new_name = input("New name: ").strip()
            if new_name:
                student['name'] = new_name
                print("Name updated.")
            pause()
        elif choice in ("a", "age"):
            new_age = input("New age: ").strip()
            if new_age and new_age.isdigit():
                student['age'] = int(new_age)
                print("Age updated.")
            else:
                print("Invalid age.")
            pause()
        elif choice in ("t", "toggle"):
            student['full-time'] = not student['full-time']
            print("Full-time toggled.")
            pause()
        elif choice in ("d", "delete"):
            confirm = input("Type DELETE to confirm: ")
            if confirm == "DELETE":
                remove_student(student['id'])
                save_data()
                print("Deleted.")
                pause()
                return
            else:
                print("Cancelled.")
            pause()
        elif choice in ("s", "save"):
            save_data()
            print("Saved.")
            pause()
        elif choice in ("r", "reload"):
            print("Reloaded.")
            pause()
            continue
        elif choice in ("q", "quit", "exit"):
            return
        else:
            print("Unknown option.")
            pause()
        if choice in ('n','name','a','age','t','toggle'):
            save_data()

def list_students(limit: Optional[int] = None):
    """Print all students (optionally limited)."""
    students = data['students']
    print(f"Total: {len(students)}")
    shown = 0
    for s in students:
        print(format_student(s))
        shown += 1
        if limit and shown >= limit:
            break

def prompt_bool(prompt: str, default: bool = True) -> bool:
    """Yes/No prompt returning bool."""
    raw = input(f"{prompt} ({'Y/n' if default else 'y/N'}): ").strip().lower()
    if raw == '':
        return default
    return raw in ('y', 'yes', 'true', '1')

def ensure_students():
    """If no students, force CSV import."""
    load_data()
    if data.get('students'):
        return
    while True:
        clear_screen()
        print("No students found.")
        default_csv = 'students.csv'
        path = input(f"Import CSV path (blank={default_csv}): ").strip() or default_csv
        count = import_csv(path, 'merge')
        if data.get('students'):
            print(f"Imported {count}.")
            pause()
            return
        print("Import failed. Try again.")
        pause()

def main_menu():
    """Main loop for the app."""
    while True:
        load_data()
        ensure_students()
        clear_screen()
        print("Main Menu")
        print("[l]ist  [e]dit  [a]dd  e[x]port  [i]mport  [s]ave  [q]uit")
        choice = input("> ").strip().lower()
        if choice in ('l', 'list'):
            list_students()
            pause()
        elif choice in ('e', 'edit'):
            raw_id = input("ID to edit: ").strip()
            if not raw_id.isdigit():
                print("Not a number.")
                pause()
                continue
            sid = int(raw_id)
            load_data()
            if not find_student(sid):
                print("No such student.")
                pause()
                continue
            student_menu(sid)
        elif choice in ('a', 'add'):
            name = input("Name: ").strip()
            age_raw = input("Age: ").strip()
            if not age_raw.isdigit():
                print("Age must be a number.")
                pause()
                continue
            ft = prompt_bool("Full-time?", True)
            load_data()
            student = make_new_student(name, int(age_raw), ft)
            save_data()
            print("Added -> " + format_student(student))
            pause()
        elif choice in ('x', 'export'):
            path = export_csv()
            print(f"Exported to {path}")
            pause()
        elif choice in ('i', 'import'):
            path = input("CSV path (blank=students.csv): ").strip() or 'students.csv'
            mode = input("Mode: [m]erge or [r]eplace? ").strip().lower()
            mode_full = 'replace' if mode in ('r','replace') else 'merge'
            count = import_csv(path, mode_full)
            print(f"Imported {count} ({mode_full}).")
            pause()
        elif choice in ('s', 'save'):
            save_data()
            print("Saved.")
            pause()
        elif choice in ('q', 'quit', 'exit'):
            if prompt_bool("Save before quitting?", False):
                save_data()
                print("Saved.")
                pause()
            print("Goodbye.")
            return
        else:
            print("Unknown option.")
            pause()

def main():
    """Start program."""
    ensure_students()
    main_menu()

if __name__ == "__main__":
    main()