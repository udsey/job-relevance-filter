const observer_match = new MutationObserver(() => {
  const textarea = document.getElementById("job-match-job-description");
  if (textarea) console.log("textarea found", textarea);
  if (textarea && !textarea._autosize) {
    textarea._autosize = true;
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
    textarea.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = this.scrollHeight + "px";
    });
  }
});

observer_match.observe(document.body, { childList: true, subtree: true });