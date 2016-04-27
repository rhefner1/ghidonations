var iFrames = $('#donate_iframe');

function iResize() {
    for (var i = 0, j = iFrames.length; i < j; i++) {
        iFrames[i].style.height = iFrames[i].contentWindow.document.body.offsetHeight + 'px';
    }
}

$(document).ready(function () {
    //Setting domain suffix to make same-origin policy happy
    document.domain = "globalhopeindia.org";

    if ($.browser.safari || $.browser.opera) {
        iFrames.load(function () {
            setTimeout(iResize, 0);
        });

        for (var i = 0, j = iFrames.length; i < j; i++) {
            var iSource = iFrames[i].src;
            iFrames[i].src = '';
            iFrames[i].src = iSource;
        }

    } else {
        iFrames.load(function () {
            this.style.height = this.contentWindow.document.body.offsetHeight + 'px';
        });
    }

});