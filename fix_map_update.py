"""
FIX for Map Not Updating When Coordinates Change

The issue is that when JavaScript updates the input values directly:
document.getElementById('id_latitude').value = customer.latitude;

This doesn't trigger Alpine.js's x-model binding, so the map doesn't update.

SOLUTION: Dispatch 'input' event instead of 'change' event
"""

# In templates/customer_installations/installation_form.html, replace this section:

# OLD CODE (around line 225-232):
"""
document.getElementById('id_latitude').value = customer.latitude;
document.getElementById('id_longitude').value = customer.longitude;
// Trigger change event to update map
document.getElementById('id_latitude').dispatchEvent(new Event('change'));
"""

# NEW CODE:
"""
const latInput = document.getElementById('id_latitude');
const lngInput = document.getElementById('id_longitude');

if (latInput && lngInput) {
    latInput.value = customer.latitude;
    lngInput.value = customer.longitude;
    
    // Trigger input event for Alpine.js x-model binding
    latInput.dispatchEvent(new Event('input', { bubbles: true }));
    lngInput.dispatchEvent(new Event('input', { bubbles: true }));
}
"""

# EXPLANATION:
# 1. Alpine.js x-model listens to 'input' events, not 'change' events
# 2. The 'input' event with bubbles:true ensures Alpine.js picks up the change
# 3. This will trigger the map update through the existing @change handler
