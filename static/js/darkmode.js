/**
 * DARK MODE MODULE
 * Manages the light/dark theme preference securely in LocalStorage.
 * Prevents the "white flash" by executing immediately.
 */

const ThemeManager = {
    // Determine initial theme based on local storage or OS settings
    init: () => {
        const storedTheme = localStorage.getItem('ecovision_theme');
        // If they have a saved theme, use it. Otherwise ask their operating system.
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        const initialTheme = storedTheme ? storedTheme : (prefersDark ? 'dark' : 'light');
        ThemeManager.applyTheme(initialTheme);
    },

    applyTheme: (theme) => {
        // Set an attribute on the <html> tag, which our variables.css listens for!
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('ecovision_theme', theme);

        // Update toggle icons if the buttons exist on this specific page
        const moonIcon = document.getElementById('theme-icon-moon');
        const sunIcon = document.getElementById('theme-icon-sun');
        if (moonIcon && sunIcon) {
            if (theme === 'dark') {
                moonIcon.style.display = 'none';
                sunIcon.style.display = 'block';
            } else {
                moonIcon.style.display = 'block';
                sunIcon.style.display = 'none';
            }
        }
    },

    toggle: () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        ThemeManager.applyTheme(newTheme);
    }
};

// Run as soon as the script loads to prevent white flash
ThemeManager.init();

// Wait for DOM to attach click listeners
document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', ThemeManager.toggle);
    }
});
