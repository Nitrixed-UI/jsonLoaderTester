import json
from typing import Optional
import csv
import os
from pathlib import Path

# Portable data file path: data.json resides next to this script.
DATA_FILE = Path(__file__).with_name("data.json")

# Initialize data structure: load if file exists, else start empty.
if DATA_FILE.exists():
    with DATA_FILE.open('r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            print(f"Warning: Corrupt JSON in {DATA_FILE}. Starting with empty dataset.")
            data = {"students": []}
else:
    data = {"students": []}

def load_data(filepath: str = str(DATA_FILE)):
    """Reload data from disk to pick up external edits.
    Creates a new empty file structure if the file is missing.
    """
    global data
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Data file missing; creating new structure.")
        data = {"students": []}
        save_data(filepath)
    except json.JSONDecodeError as e:
        print(f"JSON decode error while reloading: {e}. Keeping previous in-memory data.")

def make_new_student(name, age, full_time):
    new_student = {
        "id": len(data['students']) + 1,
        "name": name,
        "age": age,
        "full-time": full_time
    }
    data['students'].append(new_student)
    return new_student

def find_student(student_id):
    for student in data['students']:
        if student['id'] == student_id:
            return student
    return None

def remove_student(student_id):
    global data
    data['students'] = [student for student in data['students'] if student['id'] != student_id]

def change_student_info(student_id, name=None, age=None, full_time=None):
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
    """Persist current in-memory data back to the JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def clear_screen():
    """Clear the console in a cross-platform way."""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass  # fail silently if clearing not possible

def pause(msg: str = "Press Enter to continue..."):
    try:
        input(msg)
    except EOFError:
        pass

def export_csv(csv_path: str = "students.csv") -> str:
    """Export current students to a CSV file. Returns path written."""
    load_data()
    fieldnames = ["id", "name", "age", "full-time"]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in data['students']:
            writer.writerow({k: s[k] for k in fieldnames})
    return os.path.abspath(csv_path)

def _parse_bool(val: str) -> bool:
    v = val.strip().lower()
    return v in ("1", "true", "t", "yes", "y")

def import_csv(csv_path: str, mode: str = 'merge') -> int:
    """Import students from a CSV file.

    mode:
      'merge' (default): add rows; if ID collides or missing/invalid, assign next id.
      'replace': replace entire student list with file contents (reindex preserved from file; fix duplicates by renumbering sequentially starting at 1).
    Returns number of records imported (added or replaced count).
    """
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
    return (f"ID: {student['id']} | Name: {student['name']} | Age: {student['age']} | "
            f"Full-time: {'Yes' if student['full-time'] else 'No'}")

def student_menu(student_id: int):
    """Interactive menu to inspect and modify a single student record.
    Reloads data before every action so external JSON edits are seen."""
    while True:
        load_data()
        clear_screen()
        student = find_student(student_id)
        if not student:
            print("Student no longer exists (possibly removed externally). Exiting.")
            return
        print("\nSelected Student -> " + format_student(student))
        print("Actions: [v]iew  [n]ame  [a]ge  [t]oggle full-time  [d]elete  [s]ave  [r]eload  [q]uit")
        choice = input("> ").strip().lower()
        if choice in ("v", "view"):
            print(format_student(student))
            pause()
        elif choice in ("n", "name"):
            new_name = input("New name (blank = cancel): ").strip()
            if new_name:
                student['name'] = new_name
                print("Updated name.")
            pause()
        elif choice in ("a", "age"):
            new_age = input("New age (blank = cancel): ").strip()
            if new_age:
                if new_age.isdigit():
                    student['age'] = int(new_age)
                    print("Updated age.")
                else:
                    print("Invalid age; must be a number.")
            pause()
        elif choice in ("t", "toggle"):
            student['full-time'] = not student['full-time']
            print("Toggled full-time status.")
            pause()
        elif choice in ("d", "delete"):
            confirm = input("Type DELETE to confirm removal: ")
            if confirm == "DELETE":
                remove_student(student['id'])
                save_data()
                print("Student deleted.")
                pause()
                return
            else:
                print("Deletion cancelled.")
            pause()
        elif choice in ("s", "save"):
            save_data()
            print("Changes saved to disk.")
            pause()
        elif choice in ("r", "reload"):
            print("Reloaded from disk.")
            pause()
            continue
        elif choice in ("q", "quit", "exit"):
            return
        else:
            print("Unknown option.")
            pause()
        # After any mutating action (except delete which returns) we persist automatically
        if choice in ('n','name','a','age','t','toggle'):
            save_data()

def list_students(limit: Optional[int] = None):
    students = data['students']
    print(f"Total students: {len(students)}")
    shown = 0
    for s in students:
        print(format_student(s))
        shown += 1
        if limit and shown >= limit:
            break

def prompt_bool(prompt: str, default: bool = True) -> bool:
    raw = input(f"{prompt} ({'Y/n' if default else 'y/N'}): ").strip().lower()
    if raw == '':
        return default
    return raw in ('y', 'yes', 'true', '1')

def ensure_students():
    """Ensure there is at least one student; force CSV import if empty."""
    load_data()
    if data.get('students') and len(data['students']) > 0:
        return
    while True:
        clear_screen()
        print("No students found in data file.")
        default_csv = 'students.csv'
        path = input(f"Import required. CSV path (blank={default_csv}): ").strip() or default_csv
        mode_full = 'merge'
        count = import_csv(path, mode_full)
        if data.get('students') and len(data['students']) > 0:
            print(f"Imported {count} student record(s).")
            pause()
            return
        print("Import failed or produced zero records. Please try again.")
        pause("Press Enter to retry...")


def main_menu():
    while True:
        load_data()  # always refresh to see external edits
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
            mode = input("Mode: [m]erge (default) or [r]eplace? ").strip().lower()
            mode_full = 'replace' if mode in ('r','replace') else 'merge'
            count = import_csv(path, mode_full)
            print(f"Imported {count} record(s) using mode '{mode_full}'.")
            pause()
        elif choice in ('s', 'save'):
            save_data()
            print("Saved to disk.")
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
    ensure_students()
    main_menu()


if __name__ == "__main__":
    main()