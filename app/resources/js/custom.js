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
    let status = $('#sidebar').hasClass('active')
    document.cookie = `sidebar-collapsed=${status}; Path=/; SameSite=None; Secure`; 
});

var csrf_token = "{{ csrf_token() }}";
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    }
});

$(function(){
    let callback = function(data){
      sessionStorage.checkUpdate = 1;
      if (data) {
        let last_version = data.app_version
        if (data.update_available == 1) {
          $('#check-update').html(`New version detected, please restart to update to ${last_version}`)
        }
        sessionStorage.app_version = last_version
      } else {
        sessionStorage.removeItem('app_version')
      }
    }
  
    if (!sessionStorage.checkUpdate)
      $.queryData({method:"get", url:"{{url_for('api.system_version')}}", success:callback, error:callback});

});

