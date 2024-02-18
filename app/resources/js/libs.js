"use strict";

// *** Bootstrap Validation ***
// Fetch all the forms we want to apply custom Bootstrap validation styles to
const forms = document.querySelectorAll(".needs-validation");

// Loop over them and prevent submission
Array.from(forms).forEach((form) => {
  form.addEventListener(
    "submit",
    (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    },
    false,
  );
});

// *** Observer Toast ***
// Callback function to execute when mutations are observed
const callback = function (mutationsList, observer) {
  for (const mutation of mutationsList) {
    if (mutation.type === "childList") {
      $.each($(".toast"), function (e) {
        $(this).toast("show");
        $(this).on("hide.bs.toast", function () {
          $(this).find(".toast-body").html("");
        });
      });
    }
  }
};
// Select the node that will be observed for mutations
// Create an observer instance linked to the callback function
// Options for the observer (which mutations to observe)
const targetNode = document.getElementById("toast");
const observer = new MutationObserver(callback);
const config = { attributes: true, childList: true, subtree: true };
// Start observing the target node for configured mutations
observer.observe(targetNode, config);

// *** Query Rest API ***
// Query get or post with data
$.queryData = function (options) {
  var o = $.extend(
    {
      method: "POST",
      url: null,
      data: null,
      success: null,
      error: null,
      convertJson: null,
      xhrFields: null,
    },
    options || {},
  );

  if (o.convertJson == null) o.convertJson = true;
  if (o.method.toUpperCase() == "GET") o.convertJson = false;

  $.ajax({  
    method: o.method,
    url: o.url,
    data: o.convertJson && o.data != "" ? JSON.stringify(o.data) : o.data,
    contentType: "application/json; charset=utf-8",
    xhrFields: o.xhrFields,  
    success: function (data) {
      $("#toast").removeClass("text-bg-danger").addClass("text-bg-primary");
      if (data && data.responseJSON)
        $("#toast .toast-body").html(data.responseJSON["message"]);
      if (o.success) return o.success(data);
    },
    error: function (data) {
      $("#toast").removeClass("text-bg-primary").addClass("text-bg-danger");
      $("#toast .toast-body").html(data.status + " - " + data);
      if (data.responseJSON)
        $("#toast .toast-body").html(data.responseJSON["message"]);
      if (o.error) return o.error(data);
    },
  });
};

// *** Serialize Forms ***
$.filterFloat = function (value) {
  if (/^(\-|\+)?([0-9]+(\.[0-9]+)?|Infinity)$/.test(value))
    return Number(value);
  return NaN;
};

$.fn.serialize = function (options) {
  return $.param(this.serializeArray(options));
};

$.fn.serializeArray = function (options) {
  var o = $.extend(
    {
      checkboxesAsBools: false,
    },
    options || {},
  );

  var rCRLF = /\r?\n/g;
  var rcheckableType = /^(?:checkbox|radio)$/i;
  var rsubmitterTypes = /^(?:submit|button|image|reset|file)$/i;
  var rsubmittable = /^(?:input|select|textarea|keygen)/i;

  return this.map(function () {
    // Can add propHook for "elements" to filter or add form elements
    var elements = jQuery.prop(this, "elements");
    return elements ? jQuery.makeArray(elements) : this;
  })
    .filter(function () {
      var type = this.type;
      return (
        this.name &&
        !jQuery(this).is(":disabled") &&
        rsubmittable.test(this.nodeName) &&
        !rsubmitterTypes.test(type)
      );
    })
    .map(function (_i, elem) {
      var val = jQuery(this).val();
      if (val == null) {
        return null;
      }
      if (Array.isArray(val)) {
        return jQuery.map(val, function (val) {
          return { name: elem.name, value: val.replace(rCRLF, "\r\n") };
        });
      } else if (rcheckableType.test(this.type)) {
        if (o.checkboxesAsBools) {
          return {
            name: elem.name,
            value:
              o.checkboxesAsBools && this.type === "checkbox"
                ? this.checked
                  ? true
                  : false
                : val.replace(rCRLF, "\r\n"),
          };
        } else {
          if (this.checked)
            return { name: elem.name, value: val.replace(rCRLF, "\r\n") };
        }
      } else {
        return { name: elem.name, value: val.replace(rCRLF, "\r\n") };
      }
    })
    .get();
};

$.fn.serializeObject = function (options) {
  var o = $.extend({ checkboxesAsBools: false }, options || {});
  return this.serializeArray({
    checkboxesAsBools: o.checkboxesAsBools,
  }).reduce(function (obj, item) {
    var name = item["name"];
    var check_value = $.filterFloat(item["value"]) || item["value"];
    if (check_value == "0") check_value = 0;
    if (!obj.hasOwnProperty(name)) {
      obj[name] = check_value;
    } else {
      if (Array.isArray(obj[name])) {
        obj[name].push(check_value);
      } else {
        var pval = obj[name];
        obj[name] = [pval, check_value];
      }
    }
    return obj;
  }, {});
};