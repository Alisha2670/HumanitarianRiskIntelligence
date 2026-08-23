/**
 * DASHBOARD MODULE
 * Runs every time the user loads the dashboard.
 */

// 1. Immediately secure the page!
// If this returns false or kicks the user, the rest of the code doesn't matter.
Auth.protectRoute();

document.addEventListener('DOMContentLoaded', () => {
    // 2. Personalize the Dashboard
    const session = Auth.getSession();
    const nameDisplay = document.getElementById('user-name-display');
    
    if (nameDisplay && session) {
        // Output the user's first name
        nameDisplay.textContent = session.firstName;
    }

    // 3. Logout functionality
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Stop the link from acting normally
            Auth.logout();      // Call our Auth module to clear local storage
        });
    }

    // Initialize Feather Icons
    feather.replace();
});
