document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();

        if (data.user) {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('exam-container').style.display = 'block';
            loadAvailableExams(data.user[0]);
        }
    } catch (error) {
        console.error('שגיאה בהתחברות:', error);
        alert('שם משתמש או סיסמה שגויים');
    }
});

async function loadAvailableExams(userId) {
    const response = await fetch(`/api/exams/${userId}/available`);
    const exams = await response.json();

    const examsList = document.createElement('div');
    examsList.innerHTML = '<h2>מבחנים זמינים</h2>';

    exams.forEach(exam => {
        const examElement = document.createElement('div');
        examElement.innerHTML = `
            <h3>${exam.name}</h3>
            <p>${exam.description}</p>
            <button onclick="startExam(${exam.exam_id}, ${userId})">התחל מבחן</button>
        `;
        examsList.appendChild(examElement);
    });

    document.getElementById('questions-container').appendChild(examsList);
}

async function startExam(examId, userId) {
    const response = await fetch(`/api/exams/${examId}/questions`);
    const questions = await response.json();

    const questionsContainer = document.getElementById('questions-container');
    questionsContainer.innerHTML = '';

    questions.forEach(question => {
        const questionElement = document.createElement('div');
        questionElement.innerHTML = `
            <h3>שאלה ${question[0]} (${question[2]})</h3>
            <p>${question[1]}</p>
            ${renderQuestionOptions(question)}
        `;
        questionsContainer.appendChild(questionElement);
    });

    document.getElementById('submit-exam').style.display = 'block';
}

function renderQuestionOptions(question) {
    if (question[2] === 'multiple_choice') {
        return question[3].map(option => `
            <div>
                <input type="radio" name="q${question[0]}" value="${option[0]}">
                <label>${option[1]}</label>
            </div>
        `).join('');
    } else {
        return '<textarea placeholder="הכנס את התשובה שלך כאן"></textarea>';
    }
}

document.getElementById('submit-exam').addEventListener('click', async () => {
    const answers = [];
    const questionsContainer = document.getElementById('questions-container');

    questionsContainer.querySelectorAll('div').forEach((questionDiv, index) => {
        const questionId = index + 1;
        const answer = questionDiv.querySelector('input[type="radio"]:checked')?.value ||
                      questionDiv.querySelector('textarea')?.value;
        answers.push([questionId, answer]);
    });

    const response = await fetch('/api/exams/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ answers })
    });

    const result = await response.json();
    alert(`ציון: ${result.score}/${result.max_score}`);
});
