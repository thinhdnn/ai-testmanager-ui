// Dark Mode Toggle for Swagger UI

(function() {
    'use strict';

    // Helper function to get or create theme toggle button
    function createThemeToggle() {
        // Check if toggle already exists
        let existingToggle = document.querySelector('.theme-toggle');
        if (existingToggle) {
            return existingToggle;
        }

        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = '🌙 Dark Mode';
        toggle.id = 'theme-toggle';
        toggle.style.cssText = 'background: #00b4d8; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; margin-left: 10px; position: fixed; top: 20px; right: 20px; z-index: 9999;';
        
        // Add click event listener
        toggle.addEventListener('click', toggleTheme);
        
        return toggle;
    }

    // Toggle theme function
    function toggleTheme() {
        const toggle = document.getElementById('theme-toggle');
        const body = document.body;
        
        if (body.classList.contains('dark-mode')) {
            // Switch to light mode
            body.classList.remove('dark-mode');
            localStorage.setItem('swagger-ui-theme', 'light');
            toggle.innerHTML = '🌙 Dark Mode';
        } else {
            // Switch to dark mode
            body.classList.add('dark-mode');
            localStorage.setItem('swagger-ui-theme', 'dark');
            toggle.innerHTML = '☀️ Light Mode';
        }
    }

    // Initialize theme on page load
    function initializeTheme() {
        const body = document.body;
        const toggle = createThemeToggle();
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('swagger-ui-theme');
        
        if (savedTheme === 'dark') {
            body.classList.add('dark-mode');
            toggle.innerHTML = '☀️ Light Mode';
        } else {
            toggle.innerHTML = '🌙 Dark Mode';
        }

        // Add toggle to document body (fallback approach)
        document.body.appendChild(toggle);
        
        console.log('Dark mode toggle initialized');
    }

    // Wait for DOM to be ready
    function waitForSwaggerUI() {
        if (document.querySelector('.swagger-ui')) {
            initializeTheme();
        } else {
            // Retry after a short delay
            setTimeout(waitForSwaggerUI, 100);
        }
    }

    // Enhanced theme initialization with additional styling
    function enhanceDarkMode() {
        const body = document.body;
        
        if (body.classList.contains('dark-mode')) {
            // Add/update meta theme color for browser UI
            let metaTheme = document.querySelector('meta[name="theme-color"]');
            if (!metaTheme) {
                metaTheme = document.createElement('meta');
                metaTheme.name = 'theme-color';
                document.head.appendChild(metaTheme);
            }
            metaTheme.content = '#1a1a1a';

            // Ensure all Swagger UI elements inherit dark theme
            setTimeout(() => {
                const swaggerUI = document.querySelector('.swagger-ui');
                if (swaggerUI && !swaggerUI.classList.contains('dark-mode-ui')) {
                    swaggerUI.classList.add('dark-mode-ui');
                }
            }, 100);
        } else {
            // Light mode
            let metaTheme = document.querySelector('meta[name="theme-color"]');
            if (metaTheme) {
                metaTheme.content = '#ffffff';
            }

            setTimeout(() => {
                const swaggerUI = document.querySelector('.swagger-ui');
                if (swaggerUI) {
                    swaggerUI.classList.remove('dark-mode-ui');
                }
            }, 100);
        }
    }

    // Override toggle function to include enhancement
    const originalToggleTheme = toggleTheme;
    window.toggleTheme = function() {
        originalToggleTheme();
        enhanceDarkMode();
    };

    // Initialize when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForSwaggerUI);
    } else {
        waitForSwaggerUI();
    }

    // Re-initialize when Swagger UI content changes (for dynamic loading)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                timeoutId = setTimeout(function() {
                    if (!document.querySelector('.theme-toggle')) {
                        waitForSwaggerUI();
                        enhanceDarkMode();
                    }
                    clearTimeout(timeoutId);
                }, 300);
            }
        });
    });

    let timeoutId;
    observer.observe(document.body, {
        childList: true, 
        subtree: true
    });

    // Expose theme functions globally for debugging
    window.swaggerDarkMode = {
        toggle: toggleTheme,
        init: initializeTheme,
        enhance: enhanceDarkMode
    };

})();
