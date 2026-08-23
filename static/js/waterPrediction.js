/**
 * WATER PREDICTION MODULE
 * Mocks the prediction workflow. Built to easily plug into `fetch()` for Flask later.
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('water-form');
    
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault(); 

            // 1. Show Loading State
            document.getElementById('result-placeholder').style.display = 'none';
            document.getElementById('result-content').style.display = 'none';
            document.getElementById('loading-overlay').style.display = 'flex';

            const formData = new FormData(form);
            const payload = Object.fromEntries(formData.entries());

            // 2. Mock Network Delay (1.5 seconds)
            setTimeout(() => {
                document.getElementById('loading-overlay').style.display = 'none';
                
                // MOCK ML RESULTS:
                let riskScore = 0;
                if (payload.water_appearance === 'muddy') riskScore += 3;
                if (payload.sewage_smell === 'strong') riskScore += 3;
                if (payload.sewage_smell === 'mild') riskScore += 1;
                if (payload.recent_flood === 'yes') riskScore += 2;
                if (payload.dead_fish_reported === 'yes') riskScore += 4;
                if (payload.nearby_industry === 'heavy') riskScore += 2;
                if (payload.water_source === 'lake' || payload.water_source === 'river') riskScore += 1;
                if (payload.season === 'monsoon') riskScore += 1;

                if (riskScore >= 6) {
                    document.getElementById('val-risk').textContent = 'High';
                    document.getElementById('val-risk').style.color = 'var(--risk-high)';
                    document.getElementById('val-badge').className = 'risk-badge high';
                    document.getElementById('val-badge').textContent = 'Critical Risk';
                    
                    document.getElementById('val-ph').textContent = '5.4';
                    document.getElementById('val-coliform').textContent = (500 + riskScore * 30) + ' MPN';
                    document.getElementById('val-nitrate').textContent = '55 mg/L';
                    document.getElementById('val-bod').textContent = '8.2 mg/L';
                    
                    document.getElementById('val-diseases').innerHTML = `
                        <li>Cholera</li>
                        <li>Dysentery</li>
                        <li>Typhoid</li>
                        <li>Methemoglobinemia (Blue Baby Syndrome)</li>
                    `;
                    document.getElementById('val-precautions').innerHTML = `
                        <li>Boil water thoroughly</li>
                        <li>Avoid direct consumption for infants</li>
                        <li>High-grade UV/RO treatment required</li>
                    `;
                } else if (riskScore >= 3) {
                    document.getElementById('val-risk').textContent = 'Medium';
                    document.getElementById('val-risk').style.color = 'var(--risk-med)';
                    // We can reuse the "moderate" css class from air for the yellow badge
                    document.getElementById('val-badge').className = 'risk-badge moderate'; 
                    document.getElementById('val-badge').textContent = 'Moderate Risk';
                    
                    document.getElementById('val-ph').textContent = '6.5';
                    document.getElementById('val-coliform').textContent = '120 MPN';
                    document.getElementById('val-nitrate').textContent = '25 mg/L';
                    document.getElementById('val-bod').textContent = '4.5 mg/L';
                    
                    document.getElementById('val-diseases').innerHTML = `
                        <li>Gastrointestinal infections</li>
                        <li>Mild Skin / Eye Irritation</li>
                    `;
                    document.getElementById('val-precautions').innerHTML = `
                        <li>Use standard carbon/sediment filtration</li>
                        <li>Avoid direct contact if skin is sensitive</li>
                    `;
                } else {
                    document.getElementById('val-risk').textContent = 'Low';
                    document.getElementById('val-risk').style.color = 'var(--risk-low)';
                    document.getElementById('val-badge').className = 'risk-badge low';
                    document.getElementById('val-badge').textContent = 'Safe';
                    
                    document.getElementById('val-ph').textContent = '7.2';
                    document.getElementById('val-coliform').textContent = '15 MPN';
                    document.getElementById('val-nitrate').textContent = '10 mg/L';
                    document.getElementById('val-bod').textContent = '1.2 mg/L';
                    
                    document.getElementById('val-diseases').innerHTML = `
                        <li>No major disease stress currently</li>
                    `;
                    document.getElementById('val-precautions').innerHTML = `
                        <li>Continue routine water hygiene practices</li>
                        <li>Monitor quality periodically</li>
                    `;
                }

                // Show the result
                document.getElementById('result-content').style.display = 'block';

                // --- SAVE TO HISTORY ---
                const history = JSON.parse(localStorage.getItem('ecovision_history')) || [];
                const newRecord = {
                    id: Date.now(),
                    timestamp: new Date().toISOString(),
                    module: 'Water Contamination',
                    location: payload.State || payload.Region,
                    riskLevel: document.getElementById('val-badge').textContent
                };
                history.push(newRecord);
                localStorage.setItem('ecovision_history', JSON.stringify(history));

            }, 1500); 
        });
    }
});
