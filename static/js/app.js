/**
 * ReturnLess - Main JavaScript
 * HTMX + Alpine.js integration
 */

// HTMX event handlers
document.addEventListener('htmx:beforeRequest', function(event) {
    // Show loading state
    const target = event.detail.target;
    if (target && target.id === 'product-grid') {
        target.classList.add('opacity-50');
    }
});

document.addEventListener('htmx:afterRequest', function(event) {
    // Remove loading state
    const target = event.detail.target;
    if (target && target.id === 'product-grid') {
        target.classList.remove('opacity-50');
    }
});

// Search results handling
document.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'search-results') {
        const results = event.detail.target;
        if (results.innerHTML.trim()) {
            results.classList.remove('hidden');
        } else {
            results.classList.add('hidden');
        }
    }
});

// Close search results on click outside
document.addEventListener('click', function(event) {
    const searchResults = document.getElementById('search-results');
    if (searchResults && !event.target.closest('.input-group')) {
        searchResults.classList.add('hidden');
    }
});

// Toast auto-dismiss
document.querySelectorAll('.toast .alert').forEach(toast => {
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
});

console.log('♻️ ReturnLess loaded');
