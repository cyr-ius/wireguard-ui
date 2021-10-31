// Alert
function alert(message, type, elementId) {
    var wrapper = document.createElement('div')
    wrapper.innerHTML = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' + message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>'
    var liveAlert = document.getElementById(elementId)
    liveAlert.append(wrapper)
  }

// submitNewClient function for new client form submission
function submitNewClient() {
    var name = $("#name").val();
    var email = $("#email").val();
    var csrf_token = $("#csrf_token").val();
    var allocated_ips = $("#allocated_ips").val();
    var allowed_ips = $("#allowed_ips").val();

    let use_server_dns = false;
    if ($("#use_server_dns").is(':checked')){
        use_server_dns = true;
    }

    let enabled = false;
    if ($("#enabled").is(':checked')){
        enabled = true;
    }

    var data = {"name": name, "email": email, "allocated_ips": allocated_ips, "allowed_ips": allowed_ips,
        "use_server_dns": use_server_dns, "enabled": enabled, "csrf_token": csrf_token};

    $.ajax({
        cache: false,
        method: 'POST',
        url: '/api/client/',
        dataType: 'json',
        contentType: "application/json",
        data: JSON.stringify(data),
        success: function(responseJson) {
            $("#modal_new_client").modal('hide');
            flashMessage(responseJson['message'],'success')
            if (window.location.pathname === "/clients") {
                location.reload();
            }
        },
        error: function(jqXHR, exception) {
            const responseJson = jQuery.parseJSON(jqXHR.responseText);
            flashMessage(responseJson['message'],'error')
        }
    });
    
}

// updateIPAllocationSuggestion function for automatically fill the IP Allocation input with suggested ip addresses
function updateIPAllocationSuggestion() {
    $.ajax({
        cache: false,
        method: 'GET',
        url: '/api/suggest-client-ips',
        dataType: 'json',
        contentType: "application/json",
        success: function(data) {
            $("#allocated_ips").next().remove()
            data.forEach(function (item, index) {
                $('#allocated_ips').val(item);
            })
            var allocation = document.querySelector('#allocated_ips')
            tagin(allocation)
        },
        error: function(jqXHR, exception) {
            const responseJson = jQuery.parseJSON(jqXHR.responseText);
            toastr.error(responseJson['message']);
        }
    });
}

// obsever catch toast added
function eventToast(element){
    // Select the node that will be observed for mutations
    const targetNode = document.getElementById(element);

    // Options for the observer (which mutations to observe)
    const config = { attributes: true, childList: true, subtree: true };

    // Callback function to execute when mutations are observed
    const callback = function(mutationsList, observer) {
        // Use traditional 'for loops' for IE 11
        for(const mutation of mutationsList) {
            if (mutation.type === 'childList') {
                $.each($('.toast'), function(e) { 
                    $(this).toast("show");
                    $(this).on('hidden.bs.toast', function () {
                        $(this).remove();
                    });
                })
            }
        }
    };

    // Create an observer instance linked to the callback function
    const observer = new MutationObserver(callback);
    
    // Start observing the target node for configured mutations
    observer.observe(targetNode, config);

    return observer
}

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

$(document).ready(function () {

    $.validator.setDefaults({
        submitHandler: function () {
            submitNewClient();
        }
    });
   
// New client form validation
$("#frm_new_client").validate({
    rules: {
        name: {
            required: true,
        },
        email: {
            required: true,
            email: true,
        },
    },
    messages: {
        name: {
            required: "Please enter a name"
        },
        email: {
            required: "Please enter an email address",
            email: "Please enter a valid email address"
        },
    },
    errorElement: 'span',
    errorPlacement: function (error, element) {
        error.addClass('invalid-feedback');
        element.closest('.form-group').append(error);
    },
    highlight: function (element, errorClass, validClass) {
        $(element).addClass('is-invalid');
    },
    unhighlight: function (element, errorClass, validClass) {
        $(element).removeClass('is-invalid');
    }
});


    for (const el of document.querySelectorAll('.tagin')) {tagin(el)} 

    // Run observer to toast
    eventToast('toast')
});

// New Client modal event
$("#modal_new_client").on('shown.bs.modal', function (e) {
    $("#name").val("");
    $("#email").val("");
    updateIPAllocationSuggestion();
});

// Wireguard service modal event
$("#modal_wg_service").on('shown.bs.modal', function (event) {
    let modal = $(this);
    var button = event.relatedTarget
    var service = button.getAttribute('data-bs-service-status') 
    modal.find('#modal_wg_service_alert').children().remove()
    modal.find('.modal-service').val(service)
    var modalTitle = modal.find('.modal-title')
    var modalBodyInput = modal.find('.modal-body')
    if (service == 'stop') {
        modalTitle.html("Stop Wireguard")
        modalBodyInput.html("Are you sure to stop the service ?")  
    } else if (service == 'start') {
        modalTitle.html("Start Wireguard service")
        modalBodyInput.html("Are you sure to start the service ?")                  
    } else if (service == 'restart'){
        modalTitle.html("Restart Wireguard")
        modalBodyInput.html("Are you sure to restart the service ?")    
    }
});

// Button service stop/start/restart
$("#apply_wg_service_confirm").click(function (event) {
    var service = $('#modal_wg_service .modal-service').val();
    var data = {"service": service};
    $.ajax({
        cache: false,
        method: 'POST',
        url: '/api/wg',
        dataType: 'json',
        contentType: "application/json",
        data: JSON.stringify(data),
        success: function(resp) {
            if (service == 'restart') {
                $("#modal_wg_service").modal('hide');
                flashMessage(resp['message'],'success');
            } else {
                location.reload()
            }
        },
        error: function(jqXHR, exception) {
            const responseJson = jQuery.parseJSON(jqXHR.responseText);
            alert(responseJson['message'],'danger','modal_wg_service_alert');
        }
    });
}); 

// Button collaped sidebar
$('#sidebarCollapse').on('click', function () {
    $('#sidebar').toggleClass('active');
    document.cookie = "sidebar-collapsed="+$('#sidebar').hasClass('active'); 
});


