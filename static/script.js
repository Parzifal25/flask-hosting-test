// scripts.js

function openCategory(category) {
    // Show loading spinner
    document.getElementById('loadingSpinner').style.display = 'block';

    // Simulate loading time
    setTimeout(() => {
        // Hide loading spinner
        document.getElementById('loadingSpinner').style.display = 'none';

        // Open the category page (or perform another action)
        window.location.href = `${category.toLowerCase().replace(/ /g, '-')}.html`;
    }, 500); // Adjust delay as needed
}

function openDetailsModal(details) {
    document.getElementById('detailsTitle').innerText = details.title;
    document.getElementById('detailsContent').innerHTML = details.content;
    document.getElementById('detailsModal').style.display = 'flex';
}

function closeDetailsModal() {
    document.getElementById('detailsModal').style.display = 'none';
}

function openBookingModal() {
    document.getElementById('bookingModal').style.display = 'flex';
}

function closeBookingModal() {
    document.getElementById('bookingModal').style.display = 'none';
}

function confirmBooking() {
    // Handle booking confirmation logic here
    alert('Booking confirmed!');
    closeBookingModal();
}
