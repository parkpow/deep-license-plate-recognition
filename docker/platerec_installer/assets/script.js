new ClipboardJS("#copy-stream");
new ClipboardJS("#copy-snapshot");

document.addEventListener(
  "click",
  (event) => {
    if (
      event.target.matches("#button-choose-stream") ||
      event.target.matches("#button-choose-snapshot")
    ) {
      document.getElementsByClassName("background")[0].style.display = "none";
      const tabs = document.getElementsByClassName("nav-link");
      for (const tab of tabs) {
        if (tab.textContent === event.target.textContent) {
          tab.click();
          return;
        }
      }
    }
  },
  false,
);
