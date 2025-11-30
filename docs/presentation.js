// Override window.open to make speaker console open in a popup window
// and inject refresh protection
var originalWindowOpen = window.open;
window.open = function(url, target, features) {
    if (target === 'impressConsole' && !features) {
        features = 'width=1024,height=768';
    }
    var win = originalWindowOpen.call(window, url, target, features);

    // Inject refresh protection for the speaker console
    if (target === 'impressConsole' && win) {
        var checkReady = setInterval(function() {
            try {
                // Wait until impress.js has populated the window
                if (win.document && win.document.body && win.document.body.innerHTML.length > 100) {
                    clearInterval(checkReady);

                    // Inject refresh prevention script
                    var script = win.document.createElement('script');
                    script.textContent = '(' + function() {
                        function showMessage(text) {
                            var msg = document.createElement('div');
                            msg.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);' +
                                'background:#333;color:#fff;padding:8px 16px;border-radius:4px;' +
                                'font-size:14px;z-index:99999;opacity:1;transition:opacity 0.5s';
                            msg.textContent = text;
                            document.body.appendChild(msg);
                            setTimeout(function() { msg.style.opacity = '0'; }, 1500);
                            setTimeout(function() { msg.remove(); }, 2000);
                        }

                        document.addEventListener('keydown', function(e) {
                            // Shift+R: refresh the deck from console
                            if (e.shiftKey && e.key === 'R' && !e.ctrlKey && !e.metaKey) {
                                e.preventDefault();
                                if (window.opener && !window.opener.closed) {
                                    sessionStorage.setItem('reopenConsole', 'true');
                                    showMessage('Refreshing deck...');
                                    setTimeout(function() {
                                        window.opener.location.reload();
                                    }, 300);
                                }
                                return;
                            }

                            // Block normal refresh keys
                            var isRefresh = e.key === 'F5' ||
                                ((e.ctrlKey || e.metaKey) && e.key === 'r');
                            if (isRefresh) {
                                e.preventDefault();
                                e.stopPropagation();
                                showMessage('Refresh disabled - use Shift+R to refresh deck');
                            }
                        }, true);

                        // Home/End key navigation
                        document.addEventListener('keyup', function(e) {
                            if (window.opener && !window.opener.closed && window.opener.impress) {
                                var api = window.opener.impress();
                                if (e.key === 'Home') {
                                    api.goto(0);
                                } else if (e.key === 'End') {
                                    var steps = window.opener.document.querySelectorAll('.step');
                                    api.goto(steps.length - 1);
                                }
                            }
                        });

                        // Fallback: beforeunload warning
                        window.addEventListener('beforeunload', function(e) {
                            e.preventDefault();
                            e.returnValue = '';
                        });
                    }.toString() + ')();';
                    win.document.body.appendChild(script);

                    // Inject style override for larger notes text
                    var style = win.document.createElement('style');
                    style.textContent = '#notes { font-size: 1.5em; }';
                    win.document.head.appendChild(style);
                }
            } catch (e) {
                // Window closed or cross-origin, stop polling
                clearInterval(checkReady);
            }
        }, 100);
    }

    return win;
};

var api = impress();
api.init();

// Store original next/prev functions
var originalNext = api.next;
var originalPrev = api.prev;

// Override next to stop at the end
api.next = function() {
    var steps = document.querySelectorAll('.step');
    var currentStep = document.querySelector('.step.active');
    var currentIndex = Array.from(steps).indexOf(currentStep);

    // Only advance if not at the last slide
    if (currentIndex < steps.length - 1) {
        return originalNext.apply(this, arguments);
    }
    return false;
};

// Override prev to stop at the beginning
api.prev = function() {
    var steps = document.querySelectorAll('.step');
    var currentStep = document.querySelector('.step.active');
    var currentIndex = Array.from(steps).indexOf(currentStep);

    // Only go back if not at the first slide
    if (currentIndex > 0) {
        return originalPrev.apply(this, arguments);
    }
    return false;
};

// Prevent Tab from advancing slides while maintaining focus on the page
document.addEventListener('keydown', function(event) {
    if (event.keyCode === 9) {
        event.preventDefault();
    }
}, true);

document.addEventListener('keyup', function(event) {
    if (event.keyCode === 9) {
        event.preventDefault();
        event.stopImmediatePropagation();
    }
}, true);

// Dynamic gradient system: sunset -> night -> sunrise
function updateGradient() {
    var steps = document.querySelectorAll('.step');
    var currentStep = document.querySelector('.step.active');
    var currentIndex = Array.from(steps).indexOf(currentStep);
    var totalSteps = steps.length;

    // Calculate progression (0.0 to 1.0)
    var progression = currentIndex / (totalSteps - 1);

    var gradient;

    if (progression <= 0.25) {
        // Sunset phase (0-25%)
        var phase = progression / 0.25;
        gradient = interpolateGradient(
            ['#FF6B35', '#F7931E', '#764BA2'],
            ['#F7931E', '#764BA2', '#2E1760'],
            phase
        );
    } else if (progression <= 0.5) {
        // Dusk to night (25-50%)
        var phase = (progression - 0.25) / 0.25;
        gradient = interpolateGradient(
            ['#F7931E', '#764BA2', '#2E1760'],
            ['#2E1760', '#1A0B33', '#050510'],
            phase
        );
    } else if (progression <= 0.75) {
        // Night to dawn (50-75%)
        var phase = (progression - 0.5) / 0.25;
        gradient = interpolateGradient(
            ['#2E1760', '#1A0B33', '#050510'],
            ['#1A0B33', '#2E1760', '#667EEA'],
            phase
        );
    } else {
        // Sunrise (75-100%)
        var phase = (progression - 0.75) / 0.25;
        gradient = interpolateGradient(
            ['#1A0B33', '#2E1760', '#667EEA'],
            ['#FDC830', '#F7931E', '#89ABE3'],
            phase
        );
    }

    // Set CSS custom properties for smooth transitions
    var rgb1 = hexToRgb(gradient[0]);
    var rgb2 = hexToRgb(gradient[1]);
    var rgb3 = hexToRgb(gradient[2]);

    document.body.style.setProperty('--bg-r1', rgb1.r);
    document.body.style.setProperty('--bg-g1', rgb1.g);
    document.body.style.setProperty('--bg-b1', rgb1.b);
    document.body.style.setProperty('--bg-r2', rgb2.r);
    document.body.style.setProperty('--bg-g2', rgb2.g);
    document.body.style.setProperty('--bg-b2', rgb2.b);
    document.body.style.setProperty('--bg-r3', rgb3.r);
    document.body.style.setProperty('--bg-g3', rgb3.g);
    document.body.style.setProperty('--bg-b3', rgb3.b);

    // Use the middle gradient color for the border (creates nice reflection effect)
    document.body.style.setProperty('--border-r', rgb2.r);
    document.body.style.setProperty('--border-g', rgb2.g);
    document.body.style.setProperty('--border-b', rgb2.b);
}

function interpolateGradient(startColors, endColors, phase) {
    var result = [];
    for (var i = 0; i < startColors.length; i++) {
        result.push(interpolateColor(startColors[i], endColors[i], phase));
    }
    return result;
}

function interpolateColor(color1, color2, phase) {
    var c1 = hexToRgb(color1);
    var c2 = hexToRgb(color2);

    var r = Math.round(c1.r + (c2.r - c1.r) * phase);
    var g = Math.round(c1.g + (c2.g - c1.g) * phase);
    var b = Math.round(c1.b + (c2.b - c1.b) * phase);

    return rgbToHex(r, g, b);
}

function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

// Update gradient on slide change
document.addEventListener('impress:stepenter', updateGradient);

// Set initial gradient
updateGradient();

// Create stars
function createStars() {
    var starsContainer = document.getElementById('stars');
    var numStars = 100;

    for (var i = 0; i < numStars; i++) {
        var star = document.createElement('div');
        star.className = 'star';

        // Random position
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';

        // Random size (1-3px)
        var size = Math.random() * 2 + 1;
        star.style.width = size + 'px';
        star.style.height = size + 'px';

        // Random animation delay for twinkle effect
        star.style.animationDelay = Math.random() * 3 + 's';

        starsContainer.appendChild(star);
    }
}

// Update star visibility based on progression
function updateStars(progression) {
    var starsContainer = document.getElementById('stars');

    // Stars visible during night phase (25-75%)
    if (progression >= 0.25 && progression <= 0.75) {
        starsContainer.classList.add('visible');
    } else {
        starsContainer.classList.remove('visible');
    }
}

// Update both gradient and stars
function updateBackground() {
    var steps = document.querySelectorAll('.step');
    var currentStep = document.querySelector('.step.active');
    var currentIndex = Array.from(steps).indexOf(currentStep);
    var totalSteps = steps.length;
    var progression = currentIndex / (totalSteps - 1);

    updateGradient();
    updateStars(progression);
}

// Replace single updateGradient call with updateBackground
document.removeEventListener('impress:stepenter', updateGradient);
document.addEventListener('impress:stepenter', updateBackground);

// Initialize
createStars();
updateBackground();

// Home/End key navigation
document.addEventListener('keyup', function(event) {
    if (event.key === 'Home') {
        api.goto(0);
    } else if (event.key === 'End') {
        var steps = document.querySelectorAll('.step');
        api.goto(steps.length - 1);
    }
});

// Reopen console if it was open before refresh (triggered by Shift+R in console)
if (sessionStorage.getItem('reopenConsole') === 'true') {
    sessionStorage.removeItem('reopenConsole');
    // Small delay to let impress.js fully initialize
    setTimeout(function() {
        document.getElementById('impress').dispatchEvent(
            new CustomEvent('impress:console:open', { bubbles: true })
        );
    }, 500);
}
