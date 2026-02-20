document.addEventListener('change', async (e) => {
    if (e.target && e.target.id === 'csvUpload') {
        const fileInput = e.target;
        const fileNameDisplay = document.getElementById('fileName');
        const fraudBody = document.getElementById('fraudBody'); 
        
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            
            fileNameDisplay.innerText = "Analyzing: " + file.name + " ⏳";
            fileNameDisplay.style.color = "#0ea5e9";
            if(fraudBody) fraudBody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Processing with Graph Engine...</td></tr>`;

            const formData = new FormData();
            formData.append('file', file);

            try {
                // Fetch request to backend
                const response = await fetch('http://127.0.0.1:8080/analyze', { 
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) throw new Error("Backend Error");
                
                // Parse the JSON data
                const text = await response.json();
                console.log("Received Data:", text);
                
                // Table ko update karne ka logic
                if(fraudBody && text.fraud_rings) {
                    fraudBody.innerHTML = ''; 
                    text.fraud_rings.forEach(ring => {
                        // Backend 'risk_score' number bhejta hai, use high/med me convert kar rahe hain
                        let riskLevel = ring.risk_score >= 90 ? 'High' : 'Med';
                        let riskClass = ring.risk_score >= 90 ? 'risk high' : 'risk med';
                        
                        fraudBody.innerHTML += `
                            <tr>
                                <td>${ring.ring_id}</td>
                                <td>${ring.member_accounts.length} Members</td>
                                <td>${ring.pattern_type.replace('_', ' ').toUpperCase()}</td>
                                <td><span class="${riskClass}">${riskLevel} (${ring.risk_score})</span></td>
                            </tr>
                        `;
                    });
                }

                fileNameDisplay.innerText = "Scan Complete: " + file.name + " ✔️";
                fileNameDisplay.style.color = "#10b981"; 
                
                // Agar tumne updateDashboard func alag se banaya hai, toh use call karo
                if (typeof updateDashboard === 'function') {
                    updateDashboard(text);
                }

            } catch (error) {
                console.error('Error:', error);
                if(fraudBody) fraudBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#ef4444;">Backend Error or Server Down ❌</td></tr>`;
                fileNameDisplay.innerText = "Connection Failed.";
                fileNameDisplay.style.color = "#ef4444"; 
            }
        }
    }
});

// Charts Code (No errors here)
document.addEventListener('DOMContentLoaded', () => {
    const miniChartCanvas = document.getElementById('miniChart');
    if (miniChartCanvas) {
        const ctx1 = miniChartCanvas.getContext('2d');
        new Chart(ctx1, {
            type: 'line',
            data: { labels: [1,2,3,4,5], datasets: [{ data: [5,20,10,30,15], borderColor: '#0ea5e9', tension: 0.4, pointRadius: 0 }] },
            options: { plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
        });
    }
    
    const mainChartCanvas = document.getElementById('mainDashboardChart');
    if (mainChartCanvas) {
        const ctx2 = mainChartCanvas.getContext('2d');
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: ['Node A', 'Node B', 'Node C', 'Node D', 'Node E'],
                datasets: [{ label: 'Anomaly Score', data: [45, 80, 20, 95, 55], backgroundColor: '#0ea5e9' }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: '#27272a' } } } }
        });
    }
});