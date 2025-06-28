// JavaScript for handling customer coordinate defaults in installation form
function initInstallationForm() {
    const customerSelect = document.getElementById('id_customer');
    const latInput = document.getElementById('id_latitude');
    const lngInput = document.getElementById('id_longitude');
    
    if (!customerSelect || !latInput || !lngInput) return;
    
    // Store customer coordinates data
    const customerCoordinates = {};
    
    // Fetch customer data when page loads
    fetchCustomerCoordinates();
    
    // Handle customer selection change
    customerSelect.addEventListener('change', function() {
        const customerId = this.value;
        if (customerId && customerCoordinates[customerId]) {
            const coords = customerCoordinates[customerId];
            
            // Update form fields
            latInput.value = coords.latitude || '';
            lngInput.value = coords.longitude || '';
            
            // Update map if it exists
            if (window.mapWidget && window.mapWidget.setLocation) {
                if (coords.latitude && coords.longitude) {
                    window.mapWidget.setLocation(
                        parseFloat(coords.latitude), 
                        parseFloat(coords.longitude),
                        'customer'
                    );
                }
            }
        }
    });
    
    function fetchCustomerCoordinates() {
        // Get all customer options
        const options = customerSelect.querySelectorAll('option');
        const customerIds = Array.from(options)
            .filter(opt => opt.value)
            .map(opt => opt.value);
        
        if (customerIds.length === 0) return;
        
        // Fetch coordinate data for all customers
        fetch('/customers/api/coordinates/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ customer_ids: customerIds })
        })
        .then(response => response.json())
        .then(data => {
            // Store coordinates for each customer
            data.forEach(customer => {
                customerCoordinates[customer.id] = {
                    latitude: customer.latitude,
                    longitude: customer.longitude,
                    location_notes: customer.location_notes
                };
            });
            
            // If a customer is already selected, update coordinates
            if (customerSelect.value) {
                customerSelect.dispatchEvent(new Event('change'));
            }
        })
        .catch(error => {
            console.error('Error fetching customer coordinates:', error);
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initInstallationForm);
