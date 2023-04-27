
$(document).ready(function() {
    $('#new-movie-form').submit(function(event) {
        event.preventDefault();
        $.ajax({
            type: 'POST',
            url: publish_post_url, // access the variable here
            data: $('#new-movie-form').serialize(),
            dataType: 'json',
            success: function(data) {
                if (data.error) {
                    $('#errorMessage').text(data.error);
                    $('#errorAlert').removeClass('d-none');
                    $('#successAlert').addClass('d-none');
                } else {
                    $('#successMessage').text(data.success);
                    $('#successAlert').removeClass('d-none');
                    $('#errorAlert').addClass('d-none');
                }
            },
            error: function() {
                $('#errorMessage').text('An error occurred while publishing the post. Please try again later.');
                $('#errorAlert').removeClass('d-none');
                $('#successAlert').addClass('d-none');
            }
        });
    });
});
