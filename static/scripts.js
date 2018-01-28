$(function() {

    var dz1, dz2;
    Dropzone.autoDiscover = false;
    $('#foo').dropzone({
        forceFallback: true,
        autoProcessQueue: false,
        autoQueue: false,
        createImageThumbnails: false,
        init: function() {
            var myDropzone = dz1 = this;
            this.on('sendingmultiple', function(data, xhr, formData) {
                for (var p of formData.entries()) {
                    console.log(p);
                }
                formData.append('bar', $('#bar').val());
                for (var p of formData.entries()) {
                    console.log(p);
                }
            });
            this.on('successmultiple', function(files, response) {
            });
            this.on('errormultiple', function(files, response) {
            });
            $('form').submit(function(e) {
                console.log("HERE");
                e.preventDefault();
                e.stopPropagation();
                for (f of dz1.files) {
                    console.log(f);
                    dz1.enqueueFile(f);
                }
                for (f of dz2.files) {
                    console.log(f);
                    dz1.addFile(f);
                    dz1.enqueueFile(f);
                    dz2.removeFile(f);
                }
                myDropzone.processQueue();
            });
        },
        method: 'post',
        paramName: 'files',
        uploadMultiple: true,
        url: '/'
    });

    $('#baz').dropzone({
        forceFallback: true,
        autoProcessQueue: false,
        autoQueue: false,
        createImageThumbnails: false,
        init: function() {
            var myDropzone = dz2 = this;
            this.on('sendingmultiple', function(data, xhr, formData) {
                console.log(formData);
                formData.append('bar', $('#bar').val());
                console.log(formData);
            });
            this.on('successmultiple', function(files, response) {
            });
            this.on('errormultiple', function(files, response) {
            });
            /*
            $('form').submit(function(e) {
                console.log("HERE");
                e.preventDefault();
                e.stopPropagation();
                myDropzone.processQueue();
            });
            */
        },
        method: 'post',
        paramName: 'bazzes',
        uploadMultiple: true,
        url: '/'
    });


});
