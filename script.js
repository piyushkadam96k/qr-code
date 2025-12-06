// Theme Handling
const themeToggle = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;
const themeIcon = themeToggle.querySelector('.icon');

// Check local storage or system preference
const savedTheme = localStorage.getItem('theme');
const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

if (savedTheme) {
    htmlElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
} else {
    htmlElement.setAttribute('data-theme', systemTheme);
    updateThemeIcon(systemTheme);
}

themeToggle.addEventListener('click', () => {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// QR Code Initialization
const qrCode = new QRCodeStyling({
    width: 300,
    height: 300,
    type: "canvas",
    data: "https://www.instagram.com/piyush_kadam96k",
    image: "",
    dotsOptions: {
        color: "#000000",
        type: "square"
    },
    backgroundOptions: {
        color: "#ffffff",
    },
    imageOptions: {
        crossOrigin: "anonymous",
        margin: 10
    }
});

let currentType = 'url';
let currentShape = 'square';
let currentDotsColor = '#000000';
let currentBgColor = '#ffffff';

// Render Initial QR
qrCode.append(document.getElementById("qr-code-container"));

// Data Handlers
function getQRData() {
    switch (currentType) {
        case 'url':
            return document.getElementById('text').value.trim();
        case 'text':
            return document.getElementById('text_content').value.trim();
        case 'wifi':
            const ssid = document.getElementById('wifi_ssid').value.trim();
            const pass = document.getElementById('wifi_password').value.trim();
            return ssid ? `WIFI:S:${ssid};T:WPA;P:${pass};;` : '';
        case 'contact':
            const n = document.getElementById('contact_name').value.trim();
            const p = document.getElementById('contact_phone').value.trim();
            const e = document.getElementById('contact_email').value.trim();
            return (n || p || e) ? `BEGIN:VCARD\nVERSION:3.0\nN:${n}\nTEL:${p}\nEMAIL:${e}\nEND:VCARD` : '';
        case 'email':
            const mail = document.getElementById('email_to').value.trim();
            const subj = document.getElementById('email_subject').value.trim();
            return mail ? `mailto:${mail}?subject=${encodeURIComponent(subj)}` : '';
        case 'phone':
            const tel = document.getElementById('phone_number').value.trim();
            return tel ? `tel:${tel}` : '';
        default:
            return '';
    }
}

function getShapeOptions(shape) {
    const map = {
        'square': 'square',
        'rounded': 'rounded',
        'circle': 'dots',
        'classy': 'classy',
        'diamond': 'classy-rounded',
        'dot': 'extra-rounded'
    };
    return { type: map[shape] || 'square' };
}

function updateQR() {
    const data = getQRData();
    if (!data) return;

    const dotsOptions = getShapeOptions(currentShape);
    dotsOptions.color = currentDotsColor;

    qrCode.update({
        data: data,
        dotsOptions: dotsOptions,
        backgroundOptions: {
            color: currentBgColor
        }
    });
}

// Event Listeners

// Type Tabs
document.querySelectorAll('.qr-type-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Toggle Active Classes
        document.querySelectorAll('.qr-type-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Show/Hide Sections
        document.querySelectorAll('.qr-section').forEach(s => s.classList.add('hidden'));
        currentType = tab.dataset.type;
        const section = document.getElementById(`${currentType}-section`);
        if (section) section.classList.remove('hidden');

        updateQR();
    });
});

// Design Tabs
document.querySelectorAll('.design-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.design-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        document.querySelectorAll('.design-section').forEach(s => s.classList.add('hidden'));
        const target = document.getElementById(`${tab.dataset.tab}-section`);
        if (target) target.classList.remove('hidden');
    });
});

// Shape Options
document.querySelectorAll('.shape-option').forEach(opt => {
    opt.addEventListener('click', () => {
        document.querySelectorAll('.shape-option').forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
        currentShape = opt.dataset.shape;
        updateQR();
    });
});

// Color Inputs
function handleColorUpdate(id, isBg) {
    const input = document.getElementById(id);
    const val = input.value;
    document.getElementById(id.replace('color', 'hex')).textContent = val.toUpperCase();

    if (isBg) currentBgColor = val;
    else currentDotsColor = val;

    updateQR();
}

document.getElementById('border-color').addEventListener('input', () => handleColorUpdate('border-color', false));
document.getElementById('background-color').addEventListener('input', () => handleColorUpdate('background-color', true));

// Text Inputs
document.querySelectorAll('input, textarea').forEach(el => {
    el.addEventListener('input', updateQR);
});

// Download
window.downloadQR = () => {
    qrCode.download({ name: "qr-code-pro", extension: "png" });
};

// Initial run
updateQR();

// Visitor Counter
function updateVisitorCount() {
    const counterElement = document.getElementById('visitor-count');
    if (!counterElement) return;

    // Get current count from local storage or start at 500
    let count = parseInt(localStorage.getItem('visitorCount')) || 500;

    // Increment count
    count++;

    // Save new count
    localStorage.setItem('visitorCount', count);

    // Update display with comma formatting
    // Update display with formatting
    if (count >= 1000) {
        counterElement.textContent = (count / 1000).toFixed(1) + 'k';
    } else {
        counterElement.textContent = count.toLocaleString();
    }
}

// Initialize counter
document.addEventListener('DOMContentLoaded', updateVisitorCount);


