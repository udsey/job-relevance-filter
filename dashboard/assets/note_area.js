const observer = new MutationObserver(() => {
  const textarea = document.getElementById("note-textarea");
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

observer.observe(document.body, { childList: true, subtree: true });