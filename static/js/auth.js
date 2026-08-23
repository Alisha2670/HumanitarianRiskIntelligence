/**
 * AUTHENTICATION MODULE (Frontend Only)
 * 
 * Handles registering users and managing sessions purely via LocalStorage 
 * so the frontend behaves like it's connected to a backend.
 */

const Auth = {
    /**
     * Registers a new user.
     * @param {Object} userData - Expected to have {firstName, lastName, email, password}
     * @returns {Object} {success: boolean, message: string}
     */
    signup: (userData) => {
        // 1. Get existing users list, or start an empty array if none exist
        const users = JSON.parse(localStorage.getItem('ecovision_users')) || [];
        
        // 2. See if the email is already taken
        const userExists = users.some(u => u.email === userData.email);
        if (userExists) {
            return { success: false, message: 'Email already exists.' };
        }

        // 3. Save new user & update LocalStorage
        users.push(userData);
        localStorage.setItem('ecovision_users', JSON.stringify(users));
        
        return { success: true, message: 'Account created successfully!' };
    },

    /**
     * Logs in a user by creating a session.
     * @param {string} email
     * @param {string} password
     * @returns {boolean} Was login successful?
     */
    login: (email, password) => {
        const users = JSON.parse(localStorage.getItem('ecovision_users')) || [];
        const user = users.find(u => u.email === email && u.password === password);
        
        if (user) {
            // Save active session. We only save safe data (no passwords).
            const sessionData = {
                email: user.email,
                firstName: user.firstName,
                lastName: user.lastName
            };
            localStorage.setItem('ecovision_session', JSON.stringify(sessionData));
            return true;
        }
        return false;
    },

    /**
     * Logs the user out by deleting their session.
     */
    logout: () => {
        localStorage.removeItem('ecovision_session');
        window.location.href = '/templates/login.html';
    },

    /**
     * Reads the current session.
     * @returns {Object|null} Session data or null if not logged in
     */
    getSession: () => {
        return JSON.parse(localStorage.getItem('ecovision_session'));
    },

    /**
     * Automatically kicks the user out if they try to view a protected page without logging in.
     */
    protectRoute: () => {
        if (!Auth.getSession()) {
            window.location.href = '/templates/login.html';
        }
    }
};

// Expose to window so other scripts can use it
window.Auth = Auth;
