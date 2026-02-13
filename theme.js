// how-well.art — theme toggle
// ◆ dark (default) ◇ light
(function() {
    var saved = localStorage.getItem('how-well-theme');
    var sys = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    var theme = saved || sys;

    if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }

    // Inject toggle after DOM ready
    function init() {
        var btn = document.createElement('button');
        btn.className = 'theme-toggle';
        btn.setAttribute('aria-label', 'Toggle light/dark mode');
        btn.setAttribute('title', 'Toggle light/dark mode');
        btn.textContent = theme === 'light' ? '\u25C7' : '\u25C6';

        btn.addEventListener('click', function() {
            var isLight = document.documentElement.getAttribute('data-theme') === 'light';
            if (isLight) {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('how-well-theme', 'dark');
                btn.textContent = '\u25C6';
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('how-well-theme', 'light');
                btn.textContent = '\u25C7';
            }
        });

        document.body.appendChild(btn);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
