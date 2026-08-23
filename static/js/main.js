/**
 * MAIN LOGIC MODULE
 * Used for generic landing page logic and intersections (checking when items appear on screen).
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup Intersection Observer for scroll animations
    // We want elements to animate ONLY when they come into view.
    
    const observerOptions = {
        root: null, // use the viewport
        rootMargin: '0px',
        threshold: 0.1 // 10% of the element must be visible
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // If the element is on screen, ensure it triggers its animation
                entry.target.style.animationPlayState = 'running';
                
                // Stop observing once it has animated
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Select all elements that have an animation class
    const elementsToAnimate = document.querySelectorAll('.animate-slide-up, .animate-fade-in');
    
    elementsToAnimate.forEach(el => {
        // Pause the animation initially
        el.style.animationPlayState = 'paused';
        // Tell the observer to watch this element
        observer.observe(el);
    });
});
