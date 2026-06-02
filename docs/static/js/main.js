document.documentElement.classList.add("js");

const languageButtons = [...document.querySelectorAll("[data-language]")];
const translatable = [...document.querySelectorAll("[data-i18n]")];

function setLanguage(language) {
  const safeLanguage = language === "en" ? "en" : "zh";
  document.documentElement.lang = safeLanguage === "zh" ? "zh-CN" : "en";
  translatable.forEach((node) => {
    node.textContent = node.dataset[safeLanguage] || node.textContent;
  });
  languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.language === safeLanguage);
  });
  window.localStorage.setItem("site-language", safeLanguage);
}

if (languageButtons.length) {
  languageButtons.forEach((button) => {
    button.addEventListener("click", () => setLanguage(button.dataset.language));
  });
  setLanguage(window.localStorage.getItem("site-language") || "zh");
}

const homeSlideshow = document.querySelector("[data-home-slideshow]");

if (homeSlideshow) {
  const slides = [...homeSlideshow.querySelectorAll(".home-slide")];
  if (slides.length > 1) {
    let index = 0;
    window.setInterval(() => {
      slides[index].classList.remove("is-active");
      index = (index + 1) % slides.length;
      slides[index].classList.add("is-active");
    }, 5200);
  }
}

const worksBrowser = document.querySelector("[data-works-browser]");

if (worksBrowser) {
  const projectSwitches = [...worksBrowser.querySelectorAll(".works-project-switch")];
  const projectPanels = [...worksBrowser.querySelectorAll("[data-project-panel]")];
  const switches = [...worksBrowser.querySelectorAll(".works-switch")];
  const previewLink = worksBrowser.querySelector("[data-preview-link]");
  const previewOpen = worksBrowser.querySelector("[data-preview-open]");
  const previewImage = worksBrowser.querySelector("[data-preview-image]");
  const previewTitle = worksBrowser.querySelector("[data-preview-title]");
  const previewMeta = worksBrowser.querySelector("[data-preview-meta]");
  const previewDescription = worksBrowser.querySelector("[data-preview-description]");

  const updatePreview = (item) => {
    if (!item) return;

    switches.forEach((other) => other.classList.remove("is-active"));
    item.classList.add("is-active");
    if (item.dataset.hideSubnav) {
      projectSwitches.forEach((other) => other.classList.remove("is-active"));
      projectPanels.forEach((panel) => panel.classList.remove("is-active"));
    }

    const title = item.dataset.title || "";
    const year = item.dataset.year || "";
    const location = item.dataset.location || "";
    const description = item.dataset.description || "";
    const image = item.dataset.image || "";
    const url = item.dataset.url || item.getAttribute("href") || "#";

    if (previewLink) previewLink.setAttribute("href", url);
    if (previewOpen) previewOpen.setAttribute("href", url);
    if (previewTitle) previewTitle.textContent = title;
    if (previewMeta) previewMeta.textContent = location ? `${year} / ${location}` : year;
    if (previewDescription) previewDescription.textContent = description;

    if (previewImage && image) {
      previewImage.setAttribute("src", image);
      previewImage.setAttribute("alt", title);
      previewImage.hidden = false;
    }
  };

  const activateProject = (project) => {
    projectSwitches.forEach((item) => item.classList.toggle("is-active", item.dataset.project === project));
    projectPanels.forEach((panel) => panel.classList.toggle("is-active", panel.dataset.projectPanel === project));
    const firstItem = worksBrowser.querySelector(`[data-project-panel="${project}"] .works-switch`);
    updatePreview(firstItem);
  };

  projectSwitches.forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      activateProject(item.dataset.project || "travel");
    });
  });

  switches.forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      updatePreview(item);
    });
  });
}

const textsBrowser = document.querySelector("[data-texts-browser]");

if (textsBrowser) {
  const switches = [...textsBrowser.querySelectorAll(".texts-switch")];
  const panels = [...textsBrowser.querySelectorAll("[data-category-panel]")];

  switches.forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      const category = item.dataset.category || "";

      switches.forEach((other) => other.classList.remove("is-active"));
      item.classList.add("is-active");

      panels.forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.categoryPanel === category);
      });

      if (item.href) {
        window.history.replaceState(null, "", item.getAttribute("href"));
      }
    });
  });
}
