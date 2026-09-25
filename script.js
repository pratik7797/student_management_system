const API_BASE = "http://127.0.0.1:5000/api";

document.addEventListener("DOMContentLoaded", () => {
    fetchStudents();
    fetchAnalytics();

    document.getElementById("student-form").addEventListener("submit", handleFormSubmit);
    document.getElementById("cancel-btn").addEventListener("click", resetForm);
    document.getElementById("clear-all-btn").addEventListener("click", clearAllStudents);
    document.getElementById("export-btn").addEventListener("click", exportSummary);
});

let isEditing = false;

async function fetchStudents() {
    const res = await fetch(`${API_BASE}/students`);
    const students = await res.json();
    
    // Sort descending by percentage
    students.sort((a, b) => b.percentage - a.percentage);

    const tbody = document.getElementById("student-list");
    tbody.innerHTML = "";

    students.forEach((s, index) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${s.roll_no}</td>
            <td>${s.name}</td>
            <td>${s.percentage.toFixed(2)}%</td>
            <td>${s.grade}</td>
            <td>
                <button class="action-btn secondary-btn" onclick="editStudent('${s.roll_no}')">Edit</button>
                <button class="action-btn danger-btn" onclick="deleteStudent('${s.roll_no}')">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function fetchAnalytics() {
    const res = await fetch(`${API_BASE}/analytics`);
    const data = await res.json();

    document.getElementById("stat-total").innerText = data.total;
    document.getElementById("stat-avg").innerText = `${data.class_avg}%`;
    document.getElementById("stat-highest").innerText = data.highest ? `${data.highest.name} (${data.highest.percentage}%)` : "-";
    document.getElementById("stat-lowest").innerText = data.lowest ? `${data.lowest.name} (${data.lowest.percentage}%)` : "-";
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const roll_no = document.getElementById("roll_no").value.trim();
    const name = document.getElementById("name").value.trim();
    const marks = {
        "Mathematics": parseFloat(document.getElementById("m_math").value),
        "Science": parseFloat(document.getElementById("m_sci").value),
        "English": parseFloat(document.getElementById("m_eng").value),
        "Social Studies": parseFloat(document.getElementById("m_soc").value),
        "Computer Science": parseFloat(document.getElementById("m_cs").value)
    };

    const payload = { roll_no, name, marks };
    const url = isEditing ? `${API_BASE}/students/${roll_no}` : `${API_BASE}/students`;
    const method = isEditing ? "PUT" : "POST";

    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        resetForm();
        fetchStudents();
        fetchAnalytics();
    } else {
        const error = await res.json();
        alert(error.error || "Operation failed");
    }
}

async function editStudent(rollNo) {
    const res = await fetch(`${API_BASE}/students/${rollNo}`);
    if (!res.ok) return;
    
    const s = await res.json();

    document.getElementById("roll_no").value = s.roll_no;
    document.getElementById("roll_no").disabled = true;
    document.getElementById("name").value = s.name;
    document.getElementById("m_math").value = s.marks['Mathematics'] || 0;
    document.getElementById("m_sci").value = s.marks['Science'] || 0;
    document.getElementById("m_eng").value = s.marks['English'] || 0;
    document.getElementById("m_soc").value = s.marks['Social Studies'] || 0;
    document.getElementById("m_cs").value = s.marks['Computer Science'] || 0;

    isEditing = true;
    document.getElementById("form-title").innerText = "Edit Student";
    document.getElementById("submit-btn").innerText = "Update Student";
    document.getElementById("cancel-btn").style.display = "inline-block";
}

function resetForm() {
    isEditing = false;
    document.getElementById("student-form").reset();
    document.getElementById("roll_no").disabled = false;
    document.getElementById("form-title").innerText = "Add New Student";
    document.getElementById("submit-btn").innerText = "Save Student";
    document.getElementById("cancel-btn").style.display = "none";
}

async function deleteStudent(rollNo) {
    if (!confirm(`Are you sure you want to delete student ${rollNo}?`)) return;

    await fetch(`${API_BASE}/students/${rollNo}`, { method: "DELETE" });
    fetchStudents();
    fetchAnalytics();
}

async function clearAllStudents() {
    if (!confirm("WARNING: Type OK to clear all student records permanently.")) return;

    await fetch(`${API_BASE}/students/reset`, { method: "DELETE" });
    fetchStudents();
    fetchAnalytics();
}

async function exportSummary() {
    const res = await fetch(`${API_BASE}/students`);
    const students = await res.json();
    students.sort((a, b) => b.percentage - a.percentage);

    let text = "CLASS PERFORMANCE SUMMARY REPORT\n===================================\n";
    students.forEach((s, i) => {
        text += `Rank ${i + 1}: ${s.name} (Roll: ${s.roll_no}) - ${s.percentage.toFixed(2)}% [${s.grade}]\n`;
    });

    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "class_summary_report.txt";
    a.click();
}