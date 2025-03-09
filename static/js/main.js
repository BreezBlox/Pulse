document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const dismissButton = alert.querySelector('.btn-close');
            if (dismissButton) {
                dismissButton.click();
            }
        }, 5000);
    });

    // Component selection progress tracking
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.getElementById('progressText');
        const componentChecks = orderForm.querySelectorAll('input[name="components"]');

        function updateProgress() {
            const total = componentChecks.length;
            const standardComponents = Array.from(componentChecks).filter(check => !check.dataset.optional).length;
            const selected = Array.from(componentChecks).filter(check => check.checked).length;
            const percentage = Math.round((selected / standardComponents) * 100);

            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            progressText.textContent = `${selected} of ${standardComponents} standard components selected`;

            // Update progress bar color based on completion
            if (percentage < 50) {
                progressBar.classList.remove('bg-success', 'bg-warning');
                progressBar.classList.add('bg-danger');
            } else if (percentage < 100) {
                progressBar.classList.remove('bg-success', 'bg-danger');
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.remove('bg-warning', 'bg-danger');
                progressBar.classList.add('bg-success');
            }
        }

        // Add animation class when selecting components
        componentChecks.forEach(check => {
            check.addEventListener('change', function() {
                const label = this.closest('.form-check');
                label.classList.add('pulse-animation');
                setTimeout(() => label.classList.remove('pulse-animation'), 500);
                updateProgress();
            });
        });

        // Initial progress calculation
        updateProgress();
    }
});