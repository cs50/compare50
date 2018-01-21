<!DOCTYPE html>

<html lang="en">

    <head>

        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"/>

        <link href="/static/favicon.ico" rel="icon"/>

        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.3/css/bootstrap.min.css" rel="stylesheet"/>

        <link href="/static/toolkit-minimal.min.css" rel="stylesheet"/>

        <link href="/static/styles.css" rel="stylesheet"/>

        <script src="https://code.jquery.com/jquery-3.2.1.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.3/umd/popper.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js"></script>

        <script src="/static/toolkit.min.js"></script>
        <script src="/static/dropzone.js"></script>

        <title>CS50 Compare</title>

    </head>

    <body>
        <div class="container p-3">
            <div class="block text-left">
                <h1 class="block-title mb-0"><a href="{{ url_for('get') }}">CS50 Compare</a></h1>
                <h4 class="mb-0">Compare files for similarities.</h4>
                <h5 class="mb-3">
                    <small>Email <a href="mailto:sysadmins@cs50.harvard.edu">sysadmins@cs50.harvard.edu</a> about bugs (or lack of features).</small>
                </h5>

    <form action='{{ url_for("post") }}' enctype="multipart/form-data" method="post">
        <div class="form-group" id="foo">
            FOO
            <div class="fallback">
                <input multiple name="files" type="file"/>
            </div>
        </div>
        <input id="bar" name="bar" type="text" value="bar"/>
        <div class="form-group" id="baz">
            BAZ
            <div class="fallback">
                <input multiple name="bazzes" type="file"/>
            </div>
        </div>
        <button class="btn btn-primary">Compare</button>
    </form>

    <script>

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

    </script>


            </div>
        </div>
    </body>

</html>
