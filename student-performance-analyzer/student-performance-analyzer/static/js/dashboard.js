document.addEventListener("DOMContentLoaded", function () {
  const el = document.getElementById("chart-data");
  if (!el || typeof Chart === "undefined") return;
  let data;
  try { data = JSON.parse(el.textContent); } catch (_) { return; }
  const subjectCanvas = document.getElementById("subjectChart");
  if (subjectCanvas) new Chart(subjectCanvas, {type:"bar",data:{labels:data.subject_labels,datasets:[{label:"Average marks (%)",data:data.subject_values,backgroundColor:"#11a6a0",borderRadius:6}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:100}}}});
  const attendanceCanvas = document.getElementById("attendanceChart");
  if (attendanceCanvas) new Chart(attendanceCanvas, {type:"doughnut",data:{labels:data.attendance_labels,datasets:[{data:data.attendance_values,backgroundColor:["#d85a68","#f1b84b","#11a6a0","#456f9d"]}]},options:{responsive:true,plugins:{legend:{position:"bottom"}}}});
  const riskCanvas = document.getElementById("riskChart");
  if (riskCanvas) new Chart(riskCanvas, {type:"doughnut",data:{labels:["Needs review","Low risk flags"],datasets:[{data:[data.risk_count,data.safe_count],backgroundColor:["#e8a044","#11a6a0"]}]},options:{responsive:true,plugins:{legend:{position:"bottom"}}}});
});
