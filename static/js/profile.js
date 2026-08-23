/**
 * PROFILE MODULE
 * Fetches user info from LocalStorage and populates the Profile Page
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Auth.protectRoute() is already called in dashboard.js, which runs before this.
    const session = Auth.getSession();

    if (session) {
        // Populate inputs
        document.getElementById('input-fname').value = session.firstName || '';
        document.getElementById('input-lname').value = session.lastName || '';
        document.getElementById('input-email').value = session.email || '';

        // Populate side card
        document.getElementById('profile-name').textContent = `${session.firstName} ${session.lastName}`;
        document.getElementById('profile-email').textContent = session.email;

        // Create Initials for Avatar
        const initials = (session.firstName.charAt(0) + session.lastName.charAt(0)).toUpperCase();
        document.getElementById('profile-initials').textContent = initials;
    }
});
