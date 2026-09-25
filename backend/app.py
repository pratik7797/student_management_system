from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)  # Enables Cross-Origin Resource Sharing for frontend access

DB_FILE = "school_database.db"
SUBJECTS = ['Mathematics', 'Science', 'English', 'Social Studies', 'Computer Science']

def init_db():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    roll_no TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    marks TEXT NOT NULL,
                    total_marks REAL,
                    max_marks REAL,
                    percentage REAL,
                    grade TEXT
                )
            ''')
    except Exception as e:
        print(f"Database Initialization Error: {e}")

def load_data():
    students = {}
    if not os.path.exists(DB_FILE):
        return students
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT roll_no, name, marks, total_marks, max_marks, percentage, grade FROM students")
            rows = cursor.fetchall()
            
            for row in rows:
                roll_no, name, marks_json, total_marks, max_marks, percentage, grade = row
                try:
                    parsed_marks = json.loads(marks_json)
                except json.JSONDecodeError:
                    parsed_marks = {}
                
                students[roll_no] = {
                    'roll_no': roll_no,
                    'name': name,
                    'marks': parsed_marks,
                    'total_marks': total_marks,
                    'max_marks': max_marks,
                    'percentage': percentage,
                    'grade': grade
                }
    except Exception as e:
        print(f"Error loading data: {e}")
    return students

def calculate_and_save(roll_no, name, marks):
    total_marks = sum(marks.values())
    max_possible_marks = len(SUBJECTS) * 100
    percentage = (total_marks / max_possible_marks) * 100 if max_possible_marks > 0 else 0
    
    if percentage >= 90: grade = 'A+'
    elif percentage >= 80: grade = 'A'
    elif percentage >= 70: grade = 'B'
    elif percentage >= 60: grade = 'C'
    elif percentage >= 50: grade = 'D'
    else: grade = 'F'

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO students (roll_no, name, marks, total_marks, max_marks, percentage, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (roll_no, name, json.dumps(marks), total_marks, max_possible_marks, percentage, grade))

# API Routes

@app.route('/api/students', methods=['GET'])
def get_students():
    students = load_data()
    return jsonify(list(students.values()))

@app.route('/api/students/<roll_no>', methods=['GET'])
def get_student(roll_no):
    students = load_data()
    if roll_no in students:
        return jsonify(students[roll_no])
    return jsonify({'error': 'Student not found'}), 404

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    roll_no = data.get('roll_no')
    name = data.get('name')
    marks = data.get('marks', {})

    if not roll_no or not name:
        return jsonify({'error': 'Roll number and name are required'}), 400

    students = load_data()
    if roll_no in students:
        return jsonify({'error': 'Student with this roll number already exists'}), 400

    calculate_and_save(roll_no, name, marks)
    return jsonify({'message': 'Student added successfully'}), 201

@app.route('/api/students/<roll_no>', methods=['PUT'])
def update_student(roll_no):
    data = request.json
    students = load_data()
    if roll_no not in students:
        return jsonify({'error': 'Student not found'}), 404

    name = data.get('name', students[roll_no]['name'])
    marks = data.get('marks', students[roll_no]['marks'])

    calculate_and_save(roll_no, name, marks)
    return jsonify({'message': 'Student updated successfully'})

@app.route('/api/students/<roll_no>', methods=['DELETE'])
def delete_student(roll_no):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))
        return jsonify({'message': 'Student deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/reset', methods=['DELETE'])
def clear_all():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students")
        return jsonify({'message': 'All records cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    students = load_data()
    if not students:
        return jsonify({'total': 0, 'class_avg': 0, 'highest': None, 'lowest': None})
    
    total = len(students)
    percentages = [s['percentage'] for s in students.values()]
    class_avg = sum(percentages) / total
    highest_p = max(percentages)
    lowest_p = min(percentages)
    
    top_student = next(s for s in students.values() if s['percentage'] == highest_p)
    low_student = next(s for s in students.values() if s['percentage'] == lowest_p)
    
    return jsonify({
        'total': total,
        'class_avg': round(class_avg, 2),
        'highest': {'name': top_student['name'], 'percentage': round(highest_p, 2)},
        'lowest': {'name': low_student['name'], 'percentage': round(lowest_p, 2)}
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)