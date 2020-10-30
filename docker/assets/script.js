new ClipboardJS('#copy-stream');
new ClipboardJS('#copy-snapshot');

document.addEventListener('click', function (event) {
	if (event.target.matches('#button-choose-stream') || event.target.matches('#button-choose-snapshot')) {
		document.getElementsByClassName('background')[0].style.display = 'none'
		let tabs = document.getElementsByClassName('nav-link')
			for (let tab of tabs) {
				if (tab.textContent === event.target.textContent) {
					tab.click()
					return
				}
			}
	}
}, false);
