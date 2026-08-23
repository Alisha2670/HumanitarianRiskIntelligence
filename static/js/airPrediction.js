/**
 * AIR PREDICTION MODULE
 * Mocks the prediction workflow. Built to easily plug into `fetch()` for Flask later.
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('air-form');

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault(); // Stop normal form submission

            // 1. Show Loading State
            document.getElementById('result-placeholder').style.display = 'none';
            document.getElementById('result-content').style.display = 'none';
            document.getElementById('loading-overlay').style.display = 'flex';

            // 2. Gather data (For future fetch Call)
            const formData = new FormData(form);
            const payload = Object.fromEntries(formData.entries());

            // FUTURE FLASK API CALL LOOKS LIKE THIS:
            /*
            fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(res => res.json()).then(data => {
                // update UI based on data
            });
            */

            // 3. Mock Network Delay (1.5 seconds)
            setTimeout(() => {
                document.getElementById('loading-overlay').style.display = 'none';

                // MOCK ML RESULTS:
                // We use a simple point system to simulate the real Python model.
                let riskScore = 0;
                if (payload.traffic_level === 'high') riskScore += 2;
                if (payload.visible_haze === 'dense') riskScore += 3;
                if (payload.smell_of_smoke === 'strong') riskScore += 2;
                if (payload.open_burning_nearby === 'yes') riskScore += 3;
                if (payload.nearby_industry === 'heavy') riskScore += 2;
                if (payload.indoor_cooking_fuel === 'biomass') riskScore += 2;
                if (payload.season === 'winter') riskScore += 1;

                if (riskScore >= 6) {
                    document.getElementById('val-quality').textContent = 'Poor';
                    document.getElementById('val-quality').style.color = 'var(--risk-high)';
                    document.getElementById('val-badge').className = 'risk-badge poor';
                    document.getElementById('val-badge').textContent = 'High Risk';

                    document.getElementById('val-pm25').textContent = (110 + (riskScore * 5)) + ' µg/m³';
                    document.getElementById('val-pm10').textContent = '220 µg/m³';
                    document.getElementById('val-no2').textContent = '90 µg/m³';
                    document.getElementById('val-co').textContent = '2.5 mg/m³';

                    document.getElementById('val-diseases').innerHTML = `
                        <li>Severe Asthma exacerbation</li>
                        <li>Lung inflammation & reduced function</li>
                        <li>Elevated Cardiovascular risk</li>
                        <li>Hypoxia risk (due to CO/Smoke)</li>
                    `;
                    document.getElementById('val-precautions').innerHTML = `
                        <li>Stay absolutely indoors with windows sealed</li>
                        <li>Wear an N95 mask if outdoor travel is mandatory</li>
                        <li>Run HEPA air purifiers at maximum setting</li>
                        <li>Consult physician for heavy breathing symptoms</li>
                    `;
                } else if (riskScore >= 3) {
                    document.getElementById('val-quality').textContent = 'Moderate';
                    document.getElementById('val-quality').style.color = 'var(--risk-med)';
                    document.getElementById('val-badge').className = 'risk-badge moderate';
                    document.getElementById('val-badge').textContent = 'Moderate Risk';

                    document.getElementById('val-pm25').textContent = '75 µg/m³';
                    document.getElementById('val-pm10').textContent = '120 µg/m³';
                    document.getElementById('val-no2').textContent = '45 µg/m³';
                    document.getElementById('val-co').textContent = '1.1 mg/m³';

                    document.getElementById('val-diseases').innerHTML = `
                        <li>Mild Asthma flare-ups</li>
                        <li>General Allergies and Eye Irritation</li>
                        <li>Bronchitis susceptibility</li>
                    `;
                    document.getElementById('val-precautions').innerHTML = `
                        <li>Limit intense outdoor exposure</li>
                        <li>Avoid traffic-heavy zones</li>
                        <li>Keep vulnerable groups (children/elderly) indoors</li>
                    `;
                } else {
                    document.getElementById('val-quality').textContent = 'Good';
                    document.getElementById('val-quality').style.color = 'var(--risk-low)';
                    document.getElementById('val-badge').className = 'risk-badge good';
                    document.getElementById('val-badge').textContent = 'Low Risk';

                    document.getElementById('val-pm25').textContent = '28 µg/m³';
                    document.getElementById('val-pm10').textContent = '55 µg/m³';
                    document.getElementById('val-no2').textContent = '18 µg/m³';
                    document.getElementById('val-co').textContent = '0.4 mg/m³';

                    document.getElementById('val-diseases').innerHTML = `
                        <li>No major disease stress currently</li>
                    `;
                    document.getElementById('val-precautions').innerHTML = `
                        <li>Maintain routine respiratory care</li>
                        <li>Enjoy outdoor activities freely</li>
                        <li>Keep indoor spaces ventilated normally</li>
                    `;
                }

                // Show the result
                document.getElementById('result-content').style.display = 'block';

                // --- SAVE TO HISTORY ---
                const history = JSON.parse(localStorage.getItem('ecovision_history')) || [];
                const newRecord = {
                    id: Date.now(),
                    timestamp: new Date().toISOString(),
                    module: 'Air Quality',
                    location: payload.State || payload.Region,
                    riskLevel: document.getElementById('val-badge').textContent
                };
                history.push(newRecord);
                localStorage.setItem('ecovision_history', JSON.stringify(history));

            }, 1500); // 1500m delay
        });
    }
});
