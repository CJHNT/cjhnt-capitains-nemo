var lexModal = document.getElementById('lexicon-modal');

$(function () {
  $('[data-toggle="popover"]').popover()
})

function makePopupNote(id) {
    var popup = document.getElementById(id);
    popup.classList.toggle("show");
}

function showLemma(x) {
    var lemma = x.getAttribute("lemma");
    var lem_box = document.getElementById("lem_box");
    lem_box.setAttribute("default-data", lem_box.innerHTML);
    lem_box.innerHTML = lemma;
}

function hideLemma() {
    var lem_box = document.getElementById("lem_box");
    lem_box.innerHTML = lem_box.getAttribute("default-data");
    lem_box.removeAttribute("default-data");
}

//to disable cut, copy, paste, and mouse right-click
$(document).ready(function () {    
    //Disable cut, copy, and paste
    $('.no-copy').bind('cut copy paste', function (e) {
        e.preventDefault();
        $('#no-copy-message').modal('show')
    });
    
    //Disable right-mouse click
    $(".no-copy").on("contextmenu",function(e){
        return false;
    });

    $('#source-collapse0').collapse({toggle: false})

    $('.nt-source-text').each(function(i, origElem) {
        var urn = $(origElem).attr('source-text');
        var target = $(origElem).attr('source-verse');
        var words = $(origElem).attr('source-words');
        if ( words ) {
            target = target + '?words=' + words
        }
        var request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (this.readyState == 4) {
                if (this.status == 200) {
                    $(origElem).html(this.responseText);
                } else {
                    alert("Passage " + urn + ':' + target + " not found")
                }
            }
        };
        request.open('GET', '/snippet/' + urn + '/subreference/' + target, true);
        request.send()
    }
    )

    $('.source-button').on("click", function() {
        var collapseTarget = $(this).attr('data-target');
        var currentId = $(this).attr('id');
        if ($(collapseTarget).attr('lastused') == currentId) {
            $(collapseTarget).attr('lastused', '');
            $(collapseTarget).collapse('hide')
        } else {
            $(collapseTarget).attr('lastused', currentId)
            var urn = $(this).attr('urn');
            var target = $(this).attr('target')
            var request = new XMLHttpRequest();
            request.onreadystatechange = function() {
                if (this.readyState == 4) {
                    if (this.status == 200) {
                        $(collapseTarget).html(this.responseText);
                        $(collapseTarget).collapse('show');
                    } else {
                        alert("Passage " + urn + ':' + target + " not found")
                    }
                }
            };
            request.open('GET', '/snippet/' + urn + '/subreference/' + target, true);
            request.send()
        }
    }
    )

    $('.commentary-word').on('shown.bs.popover', function() {
        var popElement = '#' + $(this).attr('aria-describedby');
        var urns = $(this).attr('comm-passages');
        var request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (this.readyState == 4) {
                if (this.status == 200) {
                    $(popElement).children('.popover-body').html(this.responseText);
                } else {
                    alert("Something went wrong trying to process " + urns)
                }
            }
        };
        request.open('GET', '/related/' + urns, true);
        request.send()
    })

    /* $('.commentary-word').on('shown.bs.popover', function() {
        var popElement = '#' + $(this).attr('aria-describedby');
        var comm_urns = $(this).attr('comm-passages').split('%');
        var comm_passages = [];
        comm_passages = $.makeArray(comm_passages);
        comm_urns.forEach(function(comm_urn) {
            var urn = comm_urn.split(';')[0]
            var target = comm_urn.split(';')[1]
            var request = new XMLHttpRequest();
            request.onreadystatechange = function() {
                if (this.readyState == 4) {
                    if (this.status == 200) {
                        comm_passages.push(this.responseText)
                    } else {
                        alert("Passage " + urn + ':' + target + " not found")
                    }
                }
            };
            request.open('GET', '/snippet/' + urn + '/subreference/' + target + '?source=ntPassage', true);
            request.send()
        });
        console.log(comm_passages);
        $(popElement).children('.popover-body').html(comm_passages);
    }) */
});

function hideNotes(c) {
    var nodeclass = c + ' show'
    var matches = document.getElementsByClassName(nodeclass);
    while (matches.length > 0) {
        matches.item(0).setAttribute('aria-expanded', 'false');
        matches.item(0).classList.remove('show');
    }
}

function showNotes(c) {
    var matches = document.getElementsByClassName(c);
    for (var i=0; i<matches.length; i++) {
        matches[i].classList.add('show');
        matches[i].setAttribute('aria-expanded', 'true');
    }
}

function showLexEntry(word) {
        var lemma = word.getAttribute('data-lexicon');
        var request = new XMLHttpRequest();
        var message = lexModal.getAttribute('message');
        request.onreadystatechange = function() {
            if (this.readyState == 4) {
                if (this.status == 200) {
                    lexModal.innerHTML = this.responseText;
                    lexModal.style.display = 'block';
                } else {
                    alert(message + lemma)
                }
            }
        };
        request.open('GET', '/lexicon/urn:cts:formulae:elexicon.' + lemma + '.deu001', true);
        request.send()
    }

function closeLexEntry() {
    lexModal.style.display = "none";
}
    
window.onclick = function(event) {
    if (event.target == lexModal) {
        lexModal.style.display = 'none';
    }
}

function getSubElements(coll) {
        var objectId = coll.getAttribute('sub-element-url');
        var targetList = document.getElementById(coll.getAttribute('sub-element-id'));
        if (coll.getAttribute('ul-shown') == 'true') {
            coll.setAttribute('ul-shown', 'false');
            targetList.innerHTML = ''
        } else {
            var request = new XMLHttpRequest();
            request.onreadystatechange = function() {
                if (this.readyState == 4) {
                    if (this.status == 200) {
                        targetList.innerHTML = this.responseText;
                        coll.setAttribute('ul-shown', 'true');
                    } else {
                        alert("No texts found for collection.")
                    }
                }
            };
            request.open('GET', objectId, true);
            request.send()
    }
}

$(function () {
    if ($('#carousel-text-first').hasClass('active')) {
        $('.carousel-control-prev').hide();
    } 
    if ($('#carousel-text-last').length == 0) {
        $('.carousel-control-next').hide();
    }
})

$('#commentaryCarousel').on('slid.bs.carousel', function () {
  if ($('#carousel-text-first').hasClass('active')) {
        $('.carousel-control-prev').hide();
    } else {
        $('.carousel-control-prev').show();
    };
    if ($('#carousel-text-last').hasClass('active')) {
        $('.carousel-control-next').hide();
    } else {
        $('.carousel-control-next').show();
    };
})
