// how-well.art — pagination & search
// ◊ show more · ◊ search
(function() {
    function init() {
        var selector = document.body.getAttribute('data-paginate');
        if (!selector) return;

        var showCount = parseInt(document.body.getAttribute('data-paginate-show') || '5', 10);
        var items = Array.prototype.slice.call(document.querySelectorAll(selector));
        if (items.length === 0) return;

        var header = document.querySelector('header');
        var footer = document.querySelector('footer');
        var needsPagination = items.length > showCount;

        // --- Search bar ---
        var searchWrap = document.createElement('div');
        searchWrap.className = 'paginate-search-wrap';

        var searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'paginate-search';
        searchInput.placeholder = '\u25CA search...';
        searchInput.setAttribute('aria-label', 'Search content');
        searchWrap.appendChild(searchInput);

        var counter = document.createElement('p');
        counter.className = 'paginate-counter';
        searchWrap.appendChild(counter);

        header.parentNode.insertBefore(searchWrap, header.nextSibling);

        // --- Show more button ---
        var moreBtn = null;
        var expanded = !needsPagination;

        if (needsPagination) {
            moreBtn = document.createElement('button');
            moreBtn.className = 'paginate-more';
            if (footer) {
                footer.parentNode.insertBefore(moreBtn, footer);
            } else {
                document.body.appendChild(moreBtn);
            }

            // Hide items beyond initial count
            for (var i = showCount; i < items.length; i++) {
                items[i].classList.add('paginate-hidden');
            }

            updateMore();

            moreBtn.addEventListener('click', function() {
                expanded = true;
                items.forEach(function(item) {
                    item.classList.remove('paginate-hidden');
                });
                moreBtn.style.display = 'none';
                updateCounter('');
            });
        }

        updateCounter('');

        // --- Search with debounce ---
        var timer;
        searchInput.addEventListener('input', function() {
            clearTimeout(timer);
            timer = setTimeout(function() {
                doSearch(searchInput.value.trim().toLowerCase());
            }, 150);
        });

        // --- Escape to clear ---
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                searchInput.value = '';
                doSearch('');
                searchInput.blur();
            }
        });

        function doSearch(q) {
            removeNoResults();

            if (!q) {
                // Restore paginated view
                items.forEach(function(item, i) {
                    if (expanded || i < showCount) {
                        item.classList.remove('paginate-hidden');
                    } else {
                        item.classList.add('paginate-hidden');
                    }
                });
                if (moreBtn && !expanded) {
                    moreBtn.style.display = '';
                    updateMore();
                }
                updateCounter('');
                return;
            }

            // Search mode — hide show-more, filter all items
            if (moreBtn) moreBtn.style.display = 'none';

            var matches = 0;
            items.forEach(function(item) {
                if (item.textContent.toLowerCase().indexOf(q) !== -1) {
                    item.classList.remove('paginate-hidden');
                    matches++;
                } else {
                    item.classList.add('paginate-hidden');
                }
            });

            updateCounter(q, matches);
            if (matches === 0) showNoResults();
        }

        function updateMore() {
            if (!moreBtn) return;
            moreBtn.textContent = '\u25CA show all (' + items.length + ' total)';
        }

        function updateCounter(q, matches) {
            if (!q) {
                if (needsPagination && !expanded) {
                    counter.textContent = 'showing ' + showCount + ' of ' + items.length;
                } else {
                    counter.textContent = items.length + ' total';
                }
            } else {
                counter.textContent = matches + ' of ' + items.length + ' match';
            }
        }

        function showNoResults() {
            removeNoResults();
            var msg = document.createElement('p');
            msg.className = 'paginate-no-results';
            msg.textContent = 'no matches';
            if (footer) {
                footer.parentNode.insertBefore(msg, footer);
            }
        }

        function removeNoResults() {
            var el = document.querySelector('.paginate-no-results');
            if (el) el.parentNode.removeChild(el);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
