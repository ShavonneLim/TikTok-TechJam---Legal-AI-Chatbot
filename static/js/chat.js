async function fetchHistory() {
  const res = await fetch('/chat/history');
  const data = await res.json();
  const container = document.getElementById('chatWindow');
  container.innerHTML = '';
  data.forEach(m => appendMessage(m.role, m.text, m.files));
  container.scrollTop = container.scrollHeight;
}

function getFileIcon(extension) {
  const iconMap = {
    'pdf': '<svg style="width: 20px; height: 20px; margin-right: 0.5rem;" fill="currentColor" viewBox="0 0 24 24"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/></svg>',
    'txt': '<svg style="width: 20px; height: 20px; margin-right: 0.5rem;" fill="currentColor" viewBox="0 0 24 24"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/></svg>',
    'default': '<svg style="width: 20px; height: 20px; margin-right: 0.5rem;" fill="currentColor" viewBox="0 0 24 24"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/></svg>'
  };
  
  return iconMap[extension] || iconMap['default'];
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function appendMessage(role, text, files) {
  const container = document.getElementById('chatWindow');
  const wrap = document.createElement('div');
  wrap.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;

  // Text
  if (text) {
    const p = document.createElement('div');
    p.innerText = text;
    wrap.appendChild(p);
  }

  if (files && files.length) {
    const fileList = document.createElement('div');
    fileList.className = 'file-list mt-2 d-flex flex-wrap gap-2';

    files.forEach(fn => {
      const fileExt = fn.split('.').pop().toLowerCase();
      const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(fileExt);

      if (isImage) {
        // Enhanced image display
        const imageContainer = document.createElement('div');
        imageContainer.style.cssText = `
          position: relative;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          border: 2px solid rgba(66, 153, 225, 0.3);
          transition: all 0.3s ease;
          cursor: pointer;
        `;
        
        const img = document.createElement('img');
        img.src = `/uploads/${encodeURIComponent(fn)}`;
        img.alt = fn;
        img.style.cssText = `
          max-width: 200px;
          max-height: 200px;
          object-fit: cover;
          display: block;
          width: 100%;
        `;
        
        // Image overlay with filename
        const overlay = document.createElement('div');
        overlay.style.cssText = `
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
          color: white;
          padding: 0.5rem;
          font-size: 0.8rem;
          font-weight: 500;
          text-align: center;
          opacity: 0;
          transition: opacity 0.3s ease;
        `;
        overlay.textContent = fn;
        
        imageContainer.appendChild(img);
        imageContainer.appendChild(overlay);
        
        // Hover effects
        imageContainer.addEventListener('mouseenter', () => {
          imageContainer.style.transform = 'translateY(-2px)';
          imageContainer.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.2)';
          overlay.style.opacity = '1';
        });
        
        imageContainer.addEventListener('mouseleave', () => {
          imageContainer.style.transform = 'translateY(0)';
          imageContainer.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
          overlay.style.opacity = '0';
        });
        
        // Click to open full size
        imageContainer.addEventListener('click', () => {
          window.open(`/uploads/${encodeURIComponent(fn)}`, '_blank');
        });
        
        fileList.appendChild(imageContainer);
      } else {
        // Enhanced document display
        const fileItem = document.createElement('a');
        fileItem.href = `/uploads/${encodeURIComponent(fn)}`;
        fileItem.target = '_blank';
        fileItem.style.cssText = `
          display: flex;
          align-items: center;
          padding: 0.75rem 1rem;
          background: linear-gradient(135deg, #f0fbfeff 0%, #589ffdff 100%);
          border: 2px solid rgba(60, 190, 251, 0.3);
          border-radius: 12px;
          color: #0c46c2ff;
          text-decoration: none;
          min-width: 200px;
          max-width: 300px;
          transition: all 0.3s ease;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        `;
        
        // File icon
        fileItem.innerHTML = getFileIcon(fileExt);
        
        // File info container
        const fileInfo = document.createElement('div');
        fileInfo.style.cssText = `
          flex: 1;
          min-width: 0;
        `;
        
        // File name
        const fileName = document.createElement('div');
        fileName.style.cssText = `
          font-weight: 500;
          font-size: 0.9rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        `;
        fileName.textContent = fn;
        
        // File type indicator
        const fileType = document.createElement('div');
        fileType.style.cssText = `
          font-size: 0.75rem;
          opacity: 0.7;
          margin-top: 0.25rem;
          font-weight: 400;
        `;
        fileType.textContent = fileExt.toUpperCase() + ' Document';
        
        fileInfo.appendChild(fileName);
        fileInfo.appendChild(fileType);
        fileItem.appendChild(fileInfo);
        
        // Hover effects
        fileItem.addEventListener('mouseenter', () => {
          fileItem.style.transform = 'translateY(-2px)';
          fileItem.style.boxShadow = '0 4px 16px rgba(60, 127, 251, 0.2)';
          fileItem.style.borderColor = 'rgba(60, 181, 251, 0.5)';
        });
        
        fileItem.addEventListener('mouseleave', () => {
          fileItem.style.transform = 'translateY(0)';
          fileItem.style.boxShadow = '0 2px 8px rgba(60, 127, 251, 0.2)';
          fileItem.style.borderColor = 'rgba(60, 181, 251, 0.5)';
        });
        
        fileList.appendChild(fileItem);
      }
    });

    wrap.appendChild(fileList);
  }

  container.appendChild(wrap);
  container.scrollTop = container.scrollHeight;
}

// --- ENHANCED FILE PREVIEW FUNCTIONALITY ---
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
let selectedFiles = [];

fileInput.addEventListener('change', () => {
  selectedFiles = Array.from(fileInput.files);
  renderFilePreview();
});

function renderFilePreview() {
  filePreview.innerHTML = '';
  selectedFiles.forEach((file, index) => {
    const wrap = document.createElement('div');
    wrap.className = 'file-preview-item mb-1 d-flex align-items-center';
    wrap.style.cssText = `
      background: rgba(255, 255, 255, 0.9);
      border: 2px solid rgba(66, 153, 225, 0.3);
      border-radius: 12px;
      padding: 0.75rem;
      transition: all 0.3s ease;
      backdrop-filter: blur(10px);
    `;

    // Image preview or document icon
    if (file.type.startsWith('image/')) {
      const reader = new FileReader(); // Create a FileReader
      reader.onload = (e) => { // Set up the onload event handler
        img.src = e.target.result; // Set the src to the Base64 data
      };
      reader.readAsDataURL(file); // Read the file as a data URL

      const img = document.createElement('img');
      img.style.cssText = `
        width: 60px;
        height: 60px;
        object-fit: cover;
        border-radius: 8px;
        margin-right: 0.75rem;
        border: 2px solid rgba(66, 153, 225, 0.2);
      `;
      img.alt = file.name;
      wrap.appendChild(img);
    } else {
      // Document icon
      const iconDiv = document.createElement('div');
      iconDiv.style.cssText = `
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.7rem;
        margin-right: 0.75rem;
        flex-shrink: 0;
      `;
      const ext = file.name.split('.').pop().toLowerCase();
      iconDiv.textContent = ext.toUpperCase();
      wrap.appendChild(iconDiv);
    }

    // File info
    const fileInfo = document.createElement('div');
    fileInfo.style.cssText = `
      flex: 1;
      min-width: 0;
    `;
    
    const fileName = document.createElement('div');
    fileName.style.cssText = `
      font-weight: 500;
      font-size: 0.9rem;
      color: #374151;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 0.25rem;
    `;
    fileName.textContent = file.name;
    fileName.title = file.name; // Tooltip for full name
    
    const fileSize = document.createElement('div');
    fileSize.style.cssText = `
      font-size: 0.75rem;
      color: #6b7280;
    `;
    fileSize.textContent = formatFileSize(file.size);
    
    fileInfo.appendChild(fileName);
    fileInfo.appendChild(fileSize);
    wrap.appendChild(fileInfo);

    // Remove button
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-danger ms-2';
    btn.style.cssText = `
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      border: none;
      border-radius: 50%;
      width: 28px;
      height: 28px;
      color: white;
      font-size: 0.8rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    `;
    btn.innerHTML = '×';
    btn.addEventListener('click', () => {
      selectedFiles.splice(index, 1);
      updateFileInput();
      renderFilePreview();
    });
    
    // Hover effect for remove button
    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'scale(1.1)';
      btn.style.boxShadow = '0 2px 8px rgba(239, 68, 68, 0.3)';
    });
    
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'scale(1)';
      btn.style.boxShadow = 'none';
    });
    
    wrap.appendChild(btn);

    // Hover effect for entire preview item
    wrap.addEventListener('mouseenter', () => {
      wrap.style.borderColor = 'rgba(66, 153, 225, 0.5)';
      wrap.style.boxShadow = '0 2px 8px rgba(66, 153, 225, 0.2)';
    });
    
    wrap.addEventListener('mouseleave', () => {
      wrap.style.borderColor = 'rgba(66, 153, 225, 0.3)';
      wrap.style.boxShadow = 'none';
    });

    filePreview.appendChild(wrap);
  });
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Update the actual file input after removing a file
function updateFileInput() {
  const dataTransfer = new DataTransfer();
  selectedFiles.forEach(file => dataTransfer.items.add(file));
  fileInput.files = dataTransfer.files;
}

// --- FORM SUBMIT ---
document.getElementById('chatForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const fd = new FormData(form);
  const message = fd.get('message');

  if ((message && message.trim()) || selectedFiles.length) {
    document.getElementById('messageInput').value = '';
    selectedFiles = [];
    renderFilePreview();
  }

  const token = document.querySelector('meta[name="csrf-token"]').content;
  const res = await fetch('/chat/send', { method: 'POST', body: fd , headers: { 'X-CSRFToken': token }});
  if (res.ok) {
    const data = await res.json();
    data.messages.forEach(m => appendMessage(m.role, m.text, m.files));
    const container = document.getElementById('chatWindow');
    container.scrollTop = container.scrollHeight;
  } else {
    alert('Error sending message.');
  }
});

fetchHistory();