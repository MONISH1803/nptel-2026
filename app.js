let allQuestions = [];
let activeQuestions = [];
let currentMode = "week";
let currentWeek = 1;
let shuffleOptions = true;

const modeSelect = document.getElementById("modeSelect");
const weekSelect = document.getElementById("weekSelect");
const weekWrap = document.getElementById("weekWrap");
const shuffleCheckbox = document.getElementById("shuffleOptions");
const startBtn = document.getElementById("startBtn");
const submitBtn = document.getElementById("submitBtn");
const retakeBtn = document.getElementById("retakeBtn");
const resetBtn = document.getElementById("resetBtn");

const setupCard = document.getElementById("setupCard");
const quizCard = document.getElementById("quizCard");
const resultCard = document.getElementById("resultCard");
const quizTitle = document.getElementById("quizTitle");
const quizForm = document.getElementById("quizForm");
const scoreText = document.getElementById("scoreText");

function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function buildWeeks() {
  const weeks = [...new Set(allQuestions.map((q) => Number(q.week)))].sort((a, b) => a - b);
  weekSelect.innerHTML = weeks.map((w) => `<option value="${w}">Week ${w}</option>`).join("");
}

function prepQuestions(questions) {
  return questions.map((q) => {
    const options = [...q.options];
    const order = [0, 1, 2, 3];
    const finalOrder = shuffleOptions ? shuffleArray(order) : order;
    const displayOptions = finalOrder.map((i) => options[i]);
    const displayCorrect = finalOrder.indexOf(Number(q.answer_index));
    return { ...q, displayOptions, displayCorrect };
  });
}

function renderQuiz() {
  quizForm.innerHTML = "";
  activeQuestions.forEach((q, idx) => {
    const div = document.createElement("div");
    div.className = "qcard";
    const opts = q.displayOptions
      .map(
        (o, i) =>
          `<label class="opt" data-q="${idx}" data-opt="${i}"><input type="radio" name="q_${idx}" value="${i}" /> <span class="opt-text">${o}</span></label>`
      )
      .join("");
    div.innerHTML = `<p><strong>Q${idx + 1}.</strong> ${q.question}</p>${opts}<p class="muted q-mark" id="mark_${idx}"></p>`;
    quizForm.appendChild(div);
  });
}

function collectAnswers() {
  const answers = {};
  activeQuestions.forEach((_, idx) => {
    const selected = document.querySelector(`input[name="q_${idx}"]:checked`);
    answers[idx] = selected ? Number(selected.value) : -1;
  });
  return answers;
}

function showResults(answers) {
  let score = 0;
  activeQuestions.forEach((q, idx) => {
    const selected = answers[idx];
    const correct = q.displayCorrect;
    if (selected === correct) score += 1;

    q.displayOptions.forEach((_, i) => {
      const optEl = document.querySelector(`label[data-q="${idx}"][data-opt="${i}"]`);
      if (!optEl) return;
      optEl.classList.remove("correct", "wrong");
      const textEl = optEl.querySelector(".opt-text");
      if (!textEl) return;
      textEl.textContent = `${q.displayOptions[i]}`;

      if (i === correct) {
        optEl.classList.add("correct");
        textEl.textContent = `${q.displayOptions[i]} ✅ Correct`;
      } else if (i === selected && selected !== correct) {
        optEl.classList.add("wrong");
        textEl.textContent = `${q.displayOptions[i]} ❌ Your answer`;
      }
    });

    const markEl = document.getElementById(`mark_${idx}`);
    if (markEl) {
      markEl.textContent = `Marks: ${selected === correct ? 1 : 0}/1`;
    }
  });

  quizForm.querySelectorAll('input[type="radio"]').forEach((inp) => {
    inp.disabled = true;
  });
  submitBtn.disabled = true;
  submitBtn.textContent = "Submitted";

  scoreText.textContent = `Marks: ${score}/${activeQuestions.length} (1 for correct, 0 for wrong)`;
  resultCard.classList.remove("hidden");
}

function startTest() {
  currentMode = modeSelect.value;
  currentWeek = Number(weekSelect.value || "1");
  shuffleOptions = shuffleCheckbox.checked;

  if (currentMode === "week") {
    activeQuestions = prepQuestions(allQuestions.filter((q) => Number(q.week) === currentWeek));
    quizTitle.textContent = `Week ${currentWeek} Test (Out of ${activeQuestions.length})`;
  } else {
    activeQuestions = prepQuestions(allQuestions);
    activeQuestions = shuffleArray(activeQuestions);
    quizTitle.textContent = `Random Test - Full Bank (Out of ${activeQuestions.length})`;
  }

  renderQuiz();
  setupCard.classList.add("hidden");
  resultCard.classList.add("hidden");
  quizCard.classList.remove("hidden");
  submitBtn.disabled = false;
  submitBtn.textContent = "Submit Test";
}

function resetAll() {
  quizCard.classList.add("hidden");
  resultCard.classList.add("hidden");
  setupCard.classList.remove("hidden");
}

modeSelect.addEventListener("change", () => {
  weekWrap.style.display = modeSelect.value === "week" ? "block" : "none";
});
startBtn.addEventListener("click", startTest);
submitBtn.addEventListener("click", () => showResults(collectAnswers()));
retakeBtn.addEventListener("click", startTest);
resetBtn.addEventListener("click", resetAll);

fetch("/data/questions.json")
  .then((r) => r.json())
  .then((data) => {
    allQuestions = data;
    buildWeeks();
    weekWrap.style.display = "block";
  })
  .catch(() => {
    alert("Failed to load questions.json");
  });
