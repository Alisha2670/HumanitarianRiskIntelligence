/**
 * NAVBAR MODULE 
 * Handles the scroll effect (glassmorphism on scroll) and mobile menu toggle.
 */

document.addEventListener('DOMContentLoaded', () => {
    const navbar = document.getElementById('main-nav');
    
    // Check if navbar exists before adding listeners to avoid errors on pages without it
    if (!navbar) return;

    // 1. Scroll Effect
    window.addEventListener('scroll', () => {
        // If we scrolled down more than 20 pixels, add the "scrolled" class
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 2. Mobile Menu Toggle (Basic Alert for Phase 1)
    const mobileBtn = document.getElementById('menu-btn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', () => {
            // For now, let's just log or alert. 
            // In a future phase, we'll slide out a mobile menu drawer.
            alert('Mobile menu clicked! (Drawer UI coming in a later phase)');
        });
    }
});
