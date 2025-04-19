// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Automatically hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.remove();
                }, 500);
            });
        }, 5000);
    }
    
    // Form validation for send money form
    const sendMoneyForm = document.querySelector('.send-money-form');
    if (sendMoneyForm) {
        sendMoneyForm.addEventListener('submit', function(event) {
            const amountInput = document.getElementById('amount');
            const receiverInput = document.getElementById('receiver');
            
            // Validate amount
            if (parseFloat(amountInput.value) <= 0) {
                event.preventDefault();
                alert('Amount must be greater than zero.');
                return;
            }
            
            // Validate receiver
            if (receiverInput.value.trim() === '') {
                event.preventDefault();
                alert('Please enter a recipient username.');
                return;
            }
        });
    }
    
    // Toggle password visibility in login/register forms
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const wrapper = document.createElement('div');
        wrapper.className = 'password-wrapper';
        
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-toggle';
        toggleButton.textContent = 'Show';
        
        toggleButton.addEventListener('click', function() {
            if (input.type === 'password') {
                input.type = 'text';
                toggleButton.textContent = 'Hide';
            } else {
                input.type = 'password';
                toggleButton.textContent = 'Show';
            }
        });
        
        wrapper.appendChild(toggleButton);
    });
});