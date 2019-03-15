var allCorporaChecks = document.querySelectorAll('input.under-all');
var wordSearchData = document.getElementById('word-search-datalist');
var wordSearchInput = document.getElementById('word-search-box');
var textSearchTimeout = null;
var searchLemmas = document.getElementById('lemma_search');

// Thanks to https://stackoverflow.com/questions/31136882/displaying-slider-value-alongside-wtforms-fields-html5-decimalrangefield
function outputUpdate(plusMinus, targetId) {
    document.querySelector(targetId).value = plusMinus;
}

function checkSubCorpora(tag, category) {
    var subelements = document.getElementsByClassName(category)
    for(var i=0; i<subelements.length; i++) {
        subelements[i].checked = tag.checked;
    }
}

// for autocomplete as you type I need the following things:
// - a listener for when the field changes
// see https://blog.manifold.co/leveraging-the-power-of-elasticsearch-autocomplete-and-fuzzy-search-1d491d3e0b38 for some ideas
wordSearchInput.onkeyup = function(e) {
    // using the timeout so that it waits until the user stops typing for .5 seconds before making the request to the server
    // idea from https://schier.co/blog/2014/12/08/wait-for-user-to-stop-typing-using-javascript.html
    clearTimeout(textSearchTimeout);
    textSearchTimeout = setTimeout(function () {
        // - a function that sends the partial search query request to the server to be sent to elasticsearch (see showLexEntry above)
        // this is taken directly from https://blog.teamtreehouse.com/creating-autocomplete-dropdowns-datalist-element
        var word = wordSearchInput.value;
        if(word !== ''){
            previous = word;
            var request = new XMLHttpRequest();
            request.onreadystatechange = function(response) {
                if (request.readyState === 4) {
                    if (request.status === 200) {
                        var jsonOptions = JSON.parse(request.responseText);
                        var docFrag = document.createDocumentFragment();
                        jsonOptions.forEach(function(item) {
                            var option = document.createElement('option');
                            option.value = item;
                            docFrag.appendChild(option);
                        });
                        wordSearchData.innerHTML = '';
                        wordSearchData.appendChild(docFrag);
                        wordSearchInput.placeholder = wordSearchInput.getAttribute('default');
                    } else {
                        // An error occured
                        wordSearchInput.placeholder = "Couldn't load suggestions.";
                    }
                }
            };
            
            wordSearchInput.placeholder = "Loading options...";
            
            // Set up and make the request.
            request.open('GET', '/search/suggest/' + word + buildUrl(), true);
            request.send();
        }
    }, 500);
};

// *******************************************************************
// functions to store unsubmitted values from the advanced search page
// *******************************************************************

// build the tail end of the url to submit via AJAX
function buildUrl() {
    var params = {
        corpus:[],
        field:'autocomplete',
        fuzziness:'0',
        in_order:'False',
        slop:'0'
    };
    if (searchLemmas.checked) {
        params.field = 'autocomplete_lemmas';
    } else {
        params.field = 'autocomplete';
    }
    allCorporaChecks.forEach(function(formula) {
        if (formula.checked) {
            params.corpus.push(formula.value);
        }
    });
    if (document.getElementById('in_order').checked) {
        params.in_order = document.getElementById('in_order').value;
    };
    params.fuzziness = document.getElementById('fuzziness').value;
    params.slop = document.getElementById('slop').value;
    var urlExt = "?corpus=" + params.corpus.join('+') + "&field=" + params.field + "&fuzziness=" + params.fuzziness + "&in_order=" + params.in_order + "&slop=" + params.slop;
    return urlExt;
}

function change_lemma_search() {
    searchLemmas = !searchLemmas;
}

function updateParam(par) {
    if (par === 'searchLemmas') {
        params.field = this.val();
    } else {
        params[par] = this.value;
    }
}
