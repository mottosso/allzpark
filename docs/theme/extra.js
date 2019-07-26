window.addEventListener("load", function () {

  var OSName = "powershell";
  if (window.navigator.userAgent.indexOf("Windows")   != -1) OSName = "powershell";
  if (window.navigator.userAgent.indexOf("Mac")  != -1) OSName = "bash";
  if (window.navigator.userAgent.indexOf("X11")  != -1) OSName = "bash";
  if (window.navigator.userAgent.indexOf("Linux")   != -1) OSName = "bash";

  // Per default, display tab most relevant to the current OS
  var defaultTab = document.getElementsByClassName("tab " + OSName);
  for (i = 0; i < defaultTab.length; i++){
    defaultTab[i].click();
    break;
  }
}, false );

/* Utility function */
function hasClass(element, cls) {
    return (' ' + element.className + ' ').indexOf(' ' + cls + ' ') > -1;
}

/* Called when the user clicks any tabbed element */
function setTab(event, tabName) {
    var i, tabcontent, tabs;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = hasClass(tabcontent[i], tabName) ? "block" : "none";
    }

    // Get all elements with class="tabs" and remove the class "active"
    tabs = document.getElementsByClassName("tab");
    for (i = 0; i < tabs.length; i++) {
        tabs[i].className = tabs[i].className.replace(" active", "");
        tabs[i].className += hasClass(tabs[i], tabName) ? " active" : ""
    }
}

/* Called when the user clicks a spoiler button */
function reveal(event, id) {
  var button = event.currentTarget;

  if (hasClass(button, "revealed")) {
    button.className = button.className.replace(" revealed", "");
  } else {
    button.className += " revealed";
  }

  var content = document.getElementById(id);

  if (hasClass(content, "hidden")) {
      content.className = content.className.replace(" hidden", "");
  } else {
      content.className += " hidden";
  }
}