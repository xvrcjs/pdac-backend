(function(code) { code(window.jQuery, window, document); })(function ($, window, document){
    $(function () {
        $('div.select-with-checkboxs').on('load', function() {
            console.log('debug');
        });
    });
});