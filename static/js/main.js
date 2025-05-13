// Placeholder for future JavaScript enhancements 

// Animate cards and charts on load
window.addEventListener('DOMContentLoaded', () => {
    // Animate dashboard cards
    document.querySelectorAll('.card.stat-card').forEach((card, i) => {
        card.style.opacity = 0;
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s, transform 0.5s';
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, 150 + i * 120);
    });

    // Animate charts (if any)
    document.querySelectorAll('canvas').forEach((canvas, i) => {
        canvas.style.opacity = 0;
        setTimeout(() => {
            canvas.style.transition = 'opacity 0.7s';
            canvas.style.opacity = 1;
        }, 400 + i * 200);
    });

    // Animate dropdowns
    document.querySelectorAll('select').forEach(select => {
        select.addEventListener('focus', () => {
            select.style.boxShadow = '0 0 0 3px #b3c6f7';
        });
        select.addEventListener('blur', () => {
            select.style.boxShadow = '';
        });
    });

    // Table row hover effect (for touch devices)
    document.querySelectorAll('.leave-table tbody tr').forEach(row => {
        row.addEventListener('touchstart', () => {
            row.style.background = '#eaf1ff';
        });
        row.addEventListener('touchend', () => {
            row.style.background = '';
        });
    });
}); 