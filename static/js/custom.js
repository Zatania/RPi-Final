$(document).ready(function() {
    $('#dataTable').DataTable();
  });


$(document).ready(function() {
  $('.view-image-btn').click(function() {
      var imageUrl = $(this).data('image');
      $('#imagePreview').attr('src', '/uploads/' + imageUrl);
      $('#imageViewModal').modal('show');
  });
});

$(document).ready(function() {
    $('.view-donateqr-btn').click(function() {
        var imageUrl = $(this).data('image');
        $('#imagePreview').attr('src', '/static/img/' + imageUrl);
        $('#imageViewModal').modal('show');
    });
  });

$(document).ready(function() {
  $('#assistance_type').change(function() {
      var assistanceType = $(this).val();

      // Make an AJAX request to fetch names based on the selected assistance type
      $.ajax({
          url: '/get_names',
          type: 'POST',
          data: { assistance_type: assistanceType },
          success: function(response) {
              // Clear existing options
              $('#name').empty();
              // Populate the dropdown with new options
              $.each(response.names, function(index, name) {
                  $('#name').append($('<option>', {
                      value: name.id,
                      text: name.full_name
                  }));
              });
              // Show the dropdown and button
              $('#names_dropdown').show();
              $('#need_assistance_btn').show();
          },
          error: function(xhr, status, error) {
              console.error(xhr.responseText);
              // Handle error
          }
      });
  });
});

document.getElementById('need_assistance_btn').addEventListener('click', function(event) {
    event.preventDefault();
    var assistanceType = document.getElementById('assistance_type').value;
    var beneficiaryId = document.getElementById('name').value;

    // AJAX call to add the beneficiary to the confirmation list
    $.ajax({
        url: '/add_to_confirmation',
        type: 'POST',
        data: { assistance_type: assistanceType, beneficiary_id: beneficiaryId },
        success: function(response) {
            alert('Beneficiary added to confirmation list successfully.');
            // You can perform additional actions if needed
            window.location.href = '/';
        },
        error: function(xhr, status, error) {
            if (xhr.status === 400) {
                // Beneficiary already in confirmation list
                alert(xhr.responseJSON.message);
                window.location.href = '/';
            } else {
                // Other errors
                console.error(xhr.responseText);
                alert('An error occurred while adding the beneficiary to the confirmation list.');
                window.location.href = '/';
            }
        }
    });
});