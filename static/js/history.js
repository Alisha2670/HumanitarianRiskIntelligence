/**
 * HISTORY MODULE
 * Retrieves, formats, and filters local storage prediction records.
 */

document.addEventListener('DOMContentLoaded', () => {
    const historyTbody = document.getElementById('history-tbody');
    const emptyState = document.getElementById('empty-state');
    const searchInput = document.getElementById('search-input');
    
    let rawHistory = JSON.parse(localStorage.getItem('ecovision_history')) || [];
    let isSortDesc = true;

    // --- Helper to format Date ---
    const formatDate = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleString('en-IN', { 
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' 
        });
    };

    // --- Helper for Badges ---
    const getBadgeClass = (risk) => {
        const lowerRisk = risk.toLowerCase();
        if (lowerRisk.includes('high') || lowerRisk.includes('critical') || lowerRisk.includes('poor')) return 'risk-badge poor';
        if (lowerRisk.includes('moderate') || lowerRisk.includes('medium')) return 'risk-badge moderate';
        return 'risk-badge good';
    };

    // --- Main Render Function ---
    const renderHistory = (data) => {
        historyTbody.innerHTML = ''; // clear table
        
        if (data.length === 0) {
            emptyState.style.display = 'block';
            historyTbody.parentElement.style.display = 'none';
            return;
        }

        emptyState.style.display = 'none';
        historyTbody.parentElement.style.display = 'table';

        data.forEach((entry, index) => {
            const tr = document.createElement('tr');
            
            // Format Icon based on module
            const iconType = entry.module === 'Air Quality' ? 'wind' : 'droplet';
            
            tr.innerHTML = `
                <td style="color: var(--text-muted); font-size: 0.9rem;">${formatDate(entry.timestamp)}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i data-feather="${iconType}" style="width:16px; height:16px; color: var(--accent)"></i> 
                        ${entry.module}
                    </div>
                </td>
                <td style="font-weight: 500;">${entry.location}</td>
                <td><span class="${getBadgeClass(entry.riskLevel)}">${entry.riskLevel}</span></td>
                <td>
                    <button class="icon-btn" onclick="deleteEntry(${entry.id})" title="Delete Record" style="width: 32px; height:32px;">
                        <i data-feather="trash-2" style="width: 14px; height: 14px; color: var(--risk-high)"></i>
                    </button>
                </td>
            `;
            historyTbody.appendChild(tr);
        });

        // Re-init feather icons for the new dynamic elements
        if (window.feather) { feather.replace(); }
    };

    // --- Initial Render ---
    // Sort descending by default
    rawHistory.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    renderHistory(rawHistory);

    // --- Event Listeners ---
    
    // Search
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = rawHistory.filter(item => 
                item.location.toLowerCase().includes(term) ||
                item.module.toLowerCase().includes(term) ||
                item.riskLevel.toLowerCase().includes(term)
            );
            renderHistory(filtered);
        });
    }

    // Sort
    const sortBtn = document.getElementById('sort-btn');
    if (sortBtn) {
        sortBtn.addEventListener('click', () => {
            isSortDesc = !isSortDesc;
            rawHistory.sort((a, b) => {
                const dateA = new Date(a.timestamp);
                const dateB = new Date(b.timestamp);
                return isSortDesc ? dateB - dateA : dateA - dateB;
            });
            renderHistory(rawHistory);
            sortBtn.innerHTML = `<i data-feather="filter"></i> Sort ${isSortDesc ? 'Latest' : 'Oldest'}`;
            feather.replace();
        });
    }

    // Export CSV
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            if (rawHistory.length === 0) return alert('No data to export.');
            
            let csv = 'Timestamp,Module,Location,Risk Level\n';
            rawHistory.forEach(row => {
                csv += `"${row.timestamp}","${row.module}","${row.location}","${row.riskLevel}"\n`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('href', url);
            a.setAttribute('download', 'ecovision_history.csv');
            a.click();
        });
    }

    // Global Delete Function (attached to window so onclick works)
    window.deleteEntry = (id) => {
        if(confirm("Delete this prediction record?")){
            rawHistory = rawHistory.filter(item => item.id !== id);
            localStorage.setItem('ecovision_history', JSON.stringify(rawHistory));
            renderHistory(rawHistory);
        }
    };
});
