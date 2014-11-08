/**
 * Created by Manas on 11/1/2014.
 */

//--------------------Base------------------------

function handleTabNavigation() {
    // navigate to logs if no hash found
    if (window.location.hash == '') {
        window.location.href = window.location.href + '#logs'
    }
    navigateToActiveTab();

    // navigate to active tab every time the hash changes
    $(window).on('hashchange', function () {
        navigateToActiveTab();
    });
}

function navigateToActiveTab() {
    var hash = window.location.hash;

    // only mark selected tab as active
    var activeTab = $('a[href="' + hash +'"]');
    activeTab.siblings().removeClass('tab-active');
    activeTab.addClass('tab-active');

    // only show active tab content
    var activeContent = $('.' + hash.substr(1) + '-content');
    activeContent.show();
    activeContent.siblings().hide();
}

//--------------------Albums------------------------

function handleAlbums() {
    AddOrEditAlbumModal.init();
    DeleteAlbumModal.init();
}

var AddOrEditAlbumModal = (function() {

    var _config = {
        form: $('#add-or-edit-album-modal-form'),
        errorContainer: $('#add-or-edit-album-modal-error-container'),
        modalTitle: $('#add-or-edit-album-modal-title'),
        inputName: $('#add-or-edit-album-modal-name-input'),
        inputStartDate: $('#add-or-edit-album-modal-start-date-input'),
        inputEndDate: $('#add-or-edit-album-modal-end-date-input'),
        submitButton: $('#add-or-edit-album-modal-submit-button'),
        modal: $('#add-or-edit-album-modal'),
        dropdownItemEdit: $('.album-dropdown-item-edit'),
        addNewAlbumButton: $('#add-new-album-button'),
        formSubmitUrl: ''
    };

    function _bindUIActions() {
        _config.addNewAlbumButton.click(function () {
            _showModal('Add new album', '', '', '', 'Add');
            _config.formSubmitUrl = '/mytravelog/album/create/';
        });
        _config.dropdownItemEdit.click(function () {
            //get all data about the selected album
            var album = $(this).parents('.album');
            var id = album.attr('data-id');
            var name = album.children('.name').text();
            var startDate = album.attr('data-start-date');
            var endDate = album.attr('data-end-date');

            _showModal('Edit album', name, startDate, endDate, 'Save');
            _config.formSubmitUrl = '/mytravelog/album/update/' + id + '/'
        });
        _config.form.submit(function (event) {
            event.preventDefault();
            submitForm($(this), _config.errorContainer, _config.formSubmitUrl);
        });
    }

    function _showModal(modalTitle, name, startDate, endDate, submitButtonText) {
        _config.errorContainer.hide();
        _config.errorContainer.empty();
        _config.modalTitle.text(modalTitle);
        _config.inputName.val(name);
        _config.inputStartDate.val(startDate);
        _config.inputEndDate.val(endDate);
        _config.submitButton.text(submitButtonText);
        _config.modal.modal();
    }

    function init() {
        _bindUIActions();
    }

    return {
        init: init
    };
}());

var DeleteAlbumModal = (function () {

    var _config = {
        albumName:  $('#delete-album-modal-album-name'),
        submitButton: $('#delete-album-modal-submit-button'),
        errorContainer: $('#delete-album-modal-error-container'),
        modal: $('#delete-album-modal'),
        dropdownItemDelete: $('.album-dropdown-item-delete'),
        submitUrl: ''
    };

    function _bindUIActions() {
        _config.dropdownItemDelete.click(function () {
            //get required data about the selected album
            var album = $(this).parents('.album');
            var id = album.attr('data-id');
            var name = album.children('.name').text();

            _showModal(name);
            _config.submitUrl = '/mytravelog/album/delete/' + id + '/';
        });
        _config.submitButton.click(function () {
            submitSimpleRequest(_config.errorContainer, _config.submitUrl);
        });
    }

    function _showModal(name) {
        _config.albumName.text(name);
        _config.modal.modal();
    }

    function init() {
        _bindUIActions();
    }

    return {
        init:init
    };
}());


//--------------------Logs------------------------

function handleLogs() {
    AddLogModal.init();
    LogPicturesViewer.init();
}

var AddLogModal = (function () {

    var _config = {
        form: $('#add-log-modal-form'),
        errorContainer: $('#add-log-modal-error-container'),
        mapContainer: $('#add-log-modal-map-container'),
        inputLocation: $('#add-log-modal-location-input'),
        inputAlbum: $('#add-log-modal-album-input'),
        inputDescription: $('#add-log-modal-description-input'),
        imagesContainer: $('#add-log-modal-images-container'),
        submitButton: $('#add-log-modal-submit-button'),
        moreImagesButton: $('#add-log-modal-more-images-button'),
        modal: $('#add-log-modal'),
        addNewLogButton: $('#add-new-log-button'),
        additionalImageCounter: 0
    };

    function init() {
        _bindUIActions();
    }

    function _bindUIActions() {
        _config.addNewLogButton.click(function () {
            _showModal();
        });
        // if multiple files are submitted with the same name, only the last file is received on the server side
        // to solve this, input name is changed based on a counter
        _config.moreImagesButton.click(function () {
            _config.additionalImageCounter++;
            _config.imagesContainer.append('<input class="form-control form-input" id="add-log-modal-image-input" name="log_picture_' + _config.additionalImageCounter + '" type="file">');
        });
        _config.form.submit(function (event) {
            event.preventDefault();
            submitForm($(this), _config.errorContainer, '/mytravelog/log/create/');
        });
    }

    function _showModal() {
        _config.errorContainer.hide();
        _config.errorContainer.empty();
        _config.inputAlbum.find('option[value="None"]').attr('selected', true);
        _config.inputDescription.val('');
        _config.imagesContainer.empty().append('<input class="form-control form-input" id="add-log-modal-image-input" name="log_picture_1" type="file">');
        _config.additionalImageCounter = 1;
        _config.modal.modal();

        //show current location on map and location input field
        setTimeout(_showCurrentPosition, 1000);
    }

    function _showCurrentPosition() {
        console.log('called');
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(_showCurrentPositionSuccessCallback, _showCurrentPositionFailureCallback);
        }
        else {
            console.log("Geolocation is not supported by this browser");
        }
    }

    function _showCurrentPositionSuccessCallback(position) {
        var lat = position.coords.latitude;
        var lng = position.coords.longitude;
        var latlng = new google.maps.LatLng(lat, lng);

        //show current location on map
        var options = {
            zoom: 15,
            center: latlng,
            mapTypeControl: false,
            navigationControlOptions: {
                style: google.maps.NavigationControlStyle.SMALL
            },
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };

        var map = new google.maps.Map(_config.mapContainer[0], options);
        var marker = new google.maps.Marker({
            position: latlng,
            map: map,
            title:"You are here!"
        });
        marker.setMap(map);

        //reverse geocode latlng and then show current city and country in the input element provided
        _reverseGeocode(latlng);
    }

    function _showCurrentPositionFailureCallback(error) {
        var error_message = null;
        switch(error.code) {
            case error.PERMISSION_DENIED:
                error_message = "User denied the request for Geolocation.";
                break;
            case error.POSITION_UNAVAILABLE:
                error_message = "Location information is unavailable.";
                break;
            case error.TIMEOUT:
                error_message = "The request to get user location timed out.";
                break;
        }
        console.log(error_message);
    }

    function _reverseGeocode(latlng) {
        var geocoder = new google.maps.Geocoder();
        geocoder.geocode({'latLng': latlng}, function (results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                if (results[0]) {
                    var city = null;
                    var country = null;
                    for (var i=0; i<results[0].address_components.length; i++) {
                        for (var b=0;b<results[0].address_components[i].types.length;b++) {
                            if (results[0].address_components[i].types[b] == "locality") {
                                city = results[0].address_components[i];
                            }
                            if (results[0].address_components[i].types[b] == "country") {
                                country = results[0].address_components[i];
                            }
                        }
                    }
                    if (city && country) {
                        _config.inputLocation.val(city.long_name + ", " + country.long_name);
                    }
                    else {
                        _config.inputLocation.val("Location not found");
                    }
                }
                else {
                    console.log("location not found");
                }
            }
            else {
                console.log("Geocoder failed due to: " + status);
            }
        });
    }

    return {
        init:init
    };
}());


var LogPicturesViewer = (function () {

    var _config = {
        logPicture: $('.log-picture'),
        modal: $('#log-picture-modal'),
        modalPictureContainer: $('#log-picture-modal-picture'),
        modalPreviousButton: $('#log-picture-modal-previous-button'),
        modalNextButton: $('#log-picture-modal-next-button'),
        modalIndex: $('#log-picture-modal-index'),
        currentIndex: 0,
        totalPictures: 0,
        urls: []
    };

    function init() {
        _bindUIActions();
    }

    function _bindUIActions() {
        _config.logPicture.click(function () {
            _config.logPicture = $(this);
            _getCurrentIndexAndUrls();
            _config.modal.modal();
        });
        _config.modal.on('shown.bs.modal', function(){
            _showCurrentPicture();
        });
        _config.modal.on('hidden.bs.modal', function(){
            _config.modalPictureContainer.html('');
        });
        _config.modalNextButton.click(function () {
            _config.currentIndex++;
            _showCurrentPicture();
        });
        _config.modalPreviousButton.click(function () {
            _config.currentIndex--;
            _showCurrentPicture();
        });
    }

    function _showCurrentPicture() {
        var img = '<div id="log-picture-modal-picture" style="background-image: url(\'' + _config.urls[_config.currentIndex] +'\')"/>';
        _config.modalPictureContainer.html(img);

        //set modal index
        _config.modalIndex.text(_config.currentIndex+1 + ' of ' + _config.totalPictures);

        // hide/show previous and next buttons depending on the index
        if (_config.currentIndex == _config.totalPictures-1) {
            _config.modalNextButton.css('visibility', 'hidden');
        }
        else {
            _config.modalNextButton.css('visibility', 'visible');
        }
        if (_config.currentIndex == 0) {
            _config.modalPreviousButton.css('visibility', 'hidden');
        }
        else {
            _config.modalPreviousButton.css('visibility', 'visible');
        }
    }

    function _getCurrentIndexAndUrls() {
        _config.urls = [];
        var logPicturesContainer = _config.logPicture.closest('.log-pictures-container');
        var logPictures = logPicturesContainer.find('.log-picture');
        logPictures.each(function () {
            _config.urls.push($(this).attr('data-url'));
        });
        _config.totalPictures = logPictures.length;

        //get index of selected picture
        var currentUrl = _config.logPicture.attr('data-url');
        for (var i=0; i<_config.totalPictures; i++) {
            if (_config.urls[i] == currentUrl) {
                _config.currentIndex = i;
            }
        }
    }

    return {
        init: init
    };
})();


//--------------------Helper functions------------------------

function submitForm(form, errorContainer, url) {
    //clear and hide existing errors
    errorContainer.empty();
    errorContainer.hide();

    //get form data
    var formData = new FormData(form[0]);                  //get reference of the form DOM element
    formData.append('csrfmiddlewaretoken', csrf_token);    //token declared in user base template

    $.ajax({
        url: url,
        type: "POST",
        dataType: "json",
        data: formData,
        success: function (response) {
            var redirect_to = response['redirect_to'];
            var error_message = response['error'];
            if (redirect_to != null) {
                window.location.href = redirect_to;
            }
            else if (error_message != null) {
                errorContainer.append('<strong>Error! </strong>' + error_message);
                errorContainer.show();
            }
            else {
                window.location.reload();
            }
        },
        //Options to tell JQuery not to process data or worry about content-type
        cache: false,
        contentType: false,
        processData: false
    });
}

function submitSimpleRequest(errorContainer, url) {
    //clear and hide existing errors
    errorContainer.empty();
    errorContainer.hide();

    $.ajax({
        url: url,
        type: "POST",
        dataType: "json",
        data: {
            csrfmiddlewaretoken: csrf_token
        },
        success: function (response) {
            var redirect_to = response['redirect_to'];
            var error_message = response['error'];
            if (redirect_to != null) {
                window.location.href = redirect_to;
            }
            else if (error_message != null) {
                errorContainer.append('<strong>Error! </strong>' + error_message);
                errorContainer.show();
            }
            else {
                window.location.reload();
            }
        }
    });
}


//--------------------Function calls go here------------------------

$(document).ready(function () {
    handleTabNavigation();
    handleAlbums();
    handleLogs();
});