// dragAndDrop.js - Updated for Python Backend (FastAPI)
// Provides drag & drop UI and uploadFile() to send files to backend

// --- CONFIGURATION ---
const BACKEND_URL = 'https://campus-print-2-0.onrender.com'; // Change to your deployed backend URL later

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const dropMessage = document.getElementById('drop-message');
const fileNameDisplay = document.getElementById('file-name');
const statusMsg = document.getElementById('status-message');
const fileList = document.getElementById('file-list');

let selectedFiles = [];
let totalPages = 0;

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '#dbeafe';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.backgroundColor = '#eff6ff';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '#eff6ff';
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    dropZone.addEventListener('click', () => fileInput && fileInput.click());
}

if (fileInput) {
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
            fileInput.value = '';
        }
    });
}

function handleFile(file) {
    selectedFiles.push(file);
    
    dropMessage.innerText = "✅ Files Selected:";
    fileNameDisplay.innerText = selectedFiles.length + " file(s)";
    fileList.innerHTML = selectedFiles.map(f => `<p>${f.name}</p>`).join('');
    dropZone.style.borderColor = "#16a34a";

    if (file.type === "application/pdf") {
        statusMsg.innerText = "📄 Counting pages for " + file.name;
        statusMsg.style.color = "blue";
        
        const reader = new FileReader();
        reader.readAsArrayBuffer(file);
        
        reader.onload = function() {
            const typedarray = new Uint8Array(this.result);
            pdfjsLib.getDocument(typedarray).promise.then(function(pdf) {
                totalPages += pdf.numPages;
                document.getElementById('pages').value = totalPages;
                calculateTotal();
                statusMsg.innerText = "✅ Pages updated: " + totalPages;
                statusMsg.style.color = "green";
            });
        };
    } else if (file.type.includes("image")) {
        totalPages += 1;
        document.getElementById('pages').value = totalPages;
        calculateTotal();
        statusMsg.innerText = "✅ Image added (1 Page), Total Pages: " + totalPages;
        statusMsg.style.color = "green";
    } else {
        statusMsg.innerText = "⚠️ Word file added. Please adjust page count manually.";
        statusMsg.style.color = "#d97706";
        document.getElementById('pages').focus();
    }
}

async function uploadFile() {
    // 1. Validate login token
    const token = localStorage.getItem('token');
    if (!token) {
        alert("You are not logged in. Please login first.");
        window.location.href = 'index.html';
        return;
    }

    // 2. Validate Files
    if (selectedFiles.length === 0) {
        alert("Please select files first!");
        return;
    }

    // 3. Validate Student Details
    const sName = document.getElementById('student-name').value;
    const sYear = document.getElementById('student-year').value;
    const sBranch = document.getElementById('student-branch').value;
    const sSection = document.getElementById('student-section').value;
    const sRoll = document.getElementById('student-roll').value;
    const sDesc = document.getElementById('order-desc').value;
    
    if (!sName || !sYear || !sBranch || !sRoll) {
        alert("Please fill in your Name, Year, Branch, and Roll Number!");
        document.getElementById('student-name').focus();
        return;
    }

    // 4. Get Print Settings (values, not display text)
    const printType = document.getElementById('type').value;  // 'bw', 'color', 'glossy'
    const binding = document.getElementById('binding').value; // 'none', 'spiral', 'hardcover'
    const copies = parseInt(document.getElementById('copies').value) || 1;
    const paymentMethod = document.querySelector('input[name="paymethod"]:checked').value;

    // 5. Prepare FormData (multipart/form-data)
    const formData = new FormData();
    formData.append('student_name', sName);
    formData.append('year', sYear);
    formData.append('branch', sBranch);
    formData.append('section', sSection || '');
    formData.append('roll_number', sRoll);
    formData.append('order_description', sDesc || '');
    formData.append('total_pages', totalPages);
    formData.append('copies', copies);
    formData.append('print_type', printType);
    formData.append('binding', binding);
    formData.append('payment_method', paymentMethod);
    
    // Append all selected files
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    // 6. UI update
    if (statusMsg) {
        statusMsg.innerText = "⏳ Uploading... Please wait.";
        statusMsg.style.color = "blue";
    }

    try {
        const response = await fetch(`${BACKEND_URL}/api/orders`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
                // Do NOT set Content-Type; browser sets it with boundary for FormData
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        // Success
        if (statusMsg) statusMsg.innerText = "";
        
        // Show success modal
        const studentName = document.getElementById('student-name').value;
        document.getElementById('modal-message').innerText = `Thank you, ${studentName}! Your order is being processed.`;
        document.getElementById('success-modal').style.display = 'flex';

        // Reset form
        selectedFiles = [];
        totalPages = 0;
        if (fileNameDisplay) fileNameDisplay.innerText = '';
        if (fileList) fileList.innerHTML = '';
        if (dropMessage) dropMessage.innerText = "📂 Drag & Drop files here";
        if (dropZone) dropZone.style.borderColor = '';
        
        document.getElementById('student-name').value = "";
        document.getElementById('student-roll').value = "";
        document.getElementById('order-desc').value = "";
        document.getElementById('pages').value = 1;
        calculateTotal();

    } catch (error) {
        console.error('Upload error:', error);
        if (statusMsg) {
            statusMsg.innerText = "❌ Upload Failed: " + error.message;
            statusMsg.style.color = "red";
        }
        // If token invalid, redirect to login
        if (error.message.includes("401") || error.message.includes("Invalid token")) {
            localStorage.removeItem('token');
            localStorage.removeItem('campusUser');
            alert("Session expired. Please login again.");
            window.location.href = 'index.html';
        }
    }
}

function closeModal() {
    document.getElementById('success-modal').style.display = 'none';
}

window.closeModal = closeModal;
window.uploadFile = uploadFile;