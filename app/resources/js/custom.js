// Create Toast
function flashMessage(message, type="success", time="", img=""){
    var toast  = $('.toast_template').clone()
    $(toast).removeClass('toast_template').addClass('toast')
    $(toast).removeAttr('style')
    if (type == "success") {
        var role = "status";
        var arialive = "polite";
    } else {
        var role = "alert";
        var arialive = "assertive";
    }
    $(toast).attr("role",role);
    $(toast).attr("aria-live",arialive);
    $(toast).find('.toast-body').text(message);
    $('.toast-container').append(toast);
}

// Button collaped sidebar
$('#sidebarCollapse').on('click', function () {
    $('#sidebar').toggleClass('active');
    document.cookie = "sidebar-collapsed="+$('#sidebar').hasClass('active'); 
});


