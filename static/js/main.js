document.addEventListener('DOMContentLoaded', function() {
    // URL validation
    const urlInput = document.getElementById('url-input');
    const urlFeedback = document.getElementById('url-feedback');
    const crawlForm = document.getElementById('crawl-form');
    const submitButton = document.getElementById('submit-button');

    if (urlInput) {
        urlInput.addEventListener('input', debounce(validateURL, 500));
        
        // Form submission validation
        if (crawlForm) {
            crawlForm.addEventListener('submit', function(e) {
                if (!validateURL()) {
                    e.preventDefault();
                    showMessage('Please enter a valid URL', 'danger');
                    return false;
                }
                
                // Show loading state
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Crawling...';
                }
                
                return true;
            });
        }
    }
    
    // Toggle instruction help
    const instructionHelp = document.getElementById('instruction-help');
    const instructionHelpButton = document.getElementById('instruction-help-button');
    
    if (instructionHelpButton && instructionHelp) {
        instructionHelpButton.addEventListener('click', function() {
            instructionHelp.classList.toggle('d-none');
        });
    }
    
    // Expandable sections in results
    const expandButtons = document.querySelectorAll('.expand-button');
    expandButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = document.getElementById(this.dataset.target);
            if (target) {
                target.classList.toggle('d-none');
                this.innerHTML = target.classList.contains('d-none') ? 
                    '<i class="fas fa-chevron-down"></i> Show' : 
                    '<i class="fas fa-chevron-up"></i> Hide';
            }
        });
    });
    
    // Copy URL from history
    const historyLinks = document.querySelectorAll('.history-link');
    historyLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;
            const instructions = this.dataset.instructions || '';
            
            if (urlInput) {
                urlInput.value = url;
                validateURL();
            }
            
            const instructionsInput = document.getElementById('instructions-input');
            if (instructionsInput) {
                instructionsInput.value = instructions;
            }
            
            // Scroll to form
            document.getElementById('crawl-form').scrollIntoView({ behavior: 'smooth' });
        });
    });
    
    // Function to validate URL
    function validateURL() {
        const url = urlInput.value.trim();
        
        if (!url) {
            setValidationState(false, 'Please enter a URL');
            return false;
        }
        
        // Basic URL validation
        const pattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
        if (!pattern.test(url)) {
            setValidationState(false, 'Invalid URL format');
            return false;
        }
        
        // Advanced validation via API
        fetch('/api/check-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            setValidationState(data.valid, data.valid ? 'URL is valid' : 'Invalid URL format');
        })
        .catch(error => {
            console.error('Error validating URL:', error);
            setValidationState(true, ''); // Default to valid if API fails
        });
        
        return true;
    }
    
    // Set validation state UI
    function setValidationState(isValid, message) {
        if (isValid) {
            urlInput.classList.remove('is-invalid');
            urlInput.classList.add('is-valid');
            if (urlFeedback) {
                urlFeedback.textContent = message;
                urlFeedback.classList.remove('invalid-feedback');
                urlFeedback.classList.add('valid-feedback');
                urlFeedback.style.display = message ? 'block' : 'none';
            }
            if (submitButton) {
                submitButton.disabled = false;
            }
        } else {
            urlInput.classList.remove('is-valid');
            urlInput.classList.add('is-invalid');
            if (urlFeedback) {
                urlFeedback.textContent = message;
                urlFeedback.classList.remove('valid-feedback');
                urlFeedback.classList.add('invalid-feedback');
                urlFeedback.style.display = 'block';
            }
            if (submitButton) {
                submitButton.disabled = true;
            }
        }
    }
    
    // Utility function to debounce input events
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
    
    // Show alert message
    function showMessage(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertsContainer.appendChild(alert);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                alert.remove();
            }, 150);
        }, 5000);
    }
});
