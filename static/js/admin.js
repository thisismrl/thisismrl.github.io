document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const message = form.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });
});

document.querySelectorAll("[data-confirm-batch]").forEach((button) => {
  button.addEventListener("click", (event) => {
    const form = button.closest("form");
    const selected = form ? form.querySelectorAll('input[name="selected_photo"]:checked').length : 0;
    if (!selected) {
      event.preventDefault();
      window.alert("请先选择要删除的照片。");
      return;
    }
    if (!window.confirm(`确定删除选中的 ${selected} 张照片吗？此操作会同时删除展示图和封面图。`)) {
      event.preventDefault();
    }
  });
});

const input = document.getElementById("markdown-input");
const preview = document.getElementById("markdown-preview");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderPreview(markdown) {
  const blocks = markdown.trim().split(/\n{2,}/).filter(Boolean);
  return blocks.map((block) => {
    const safe = escapeHtml(block.trim());
    if (safe.startsWith("### ")) return `<h3>${safe.slice(4)}</h3>`;
    if (safe.startsWith("## ")) return `<h2>${safe.slice(3)}</h2>`;
    if (safe.startsWith("# ")) return `<h1>${safe.slice(2)}</h1>`;
    return `<p>${safe.replace(/\n/g, "<br>")}</p>`;
  }).join("");
}

if (input && preview) {
  const update = () => {
    preview.innerHTML = renderPreview(input.value);
  };
  input.addEventListener("input", update);
  update();
}

const articleForm = document.querySelector("[data-article-form]");

if (articleForm) {
  const category = articleForm.querySelector("[data-article-category]");
  const title = articleForm.querySelector("[data-article-title]");
  const cover = articleForm.querySelector("[data-cover-field]");
  const summary = articleForm.querySelector("[data-summary-field]");
  const guides = [...articleForm.querySelectorAll("[data-guide]")];

  const updateArticleFields = () => {
    const value = category.value;
    const isStreamType = value === "Essay" || value === "Notes" || value === "Poem";
    guides.forEach((guide) => {
      guide.classList.toggle("is-active", guide.dataset.guide === value);
    });
    if (cover) {
      cover.hidden = isStreamType;
    }
    if (title) {
      title.required = value === "Fiction";
      title.placeholder = isStreamType ? "可不填。为空时会根据日期自动生成。" : "";
    }
    if (summary) {
      summary.placeholder = isStreamType
        ? "可不填。用于文字页的时间流；为空时会从正文生成。"
        : "可不填。用于文字页和动态页的标题下方。";
    }
  };

  category.addEventListener("change", updateArticleFields);
  updateArticleFields();
}

document.querySelectorAll("[data-sortable-list]").forEach((list) => {
  let draggedRow = null;

  const moveRow = (row, direction) => {
    if (!row) return;
    if (direction === "up" && row.previousElementSibling) {
      list.insertBefore(row, row.previousElementSibling);
    }
    if (direction === "down" && row.nextElementSibling) {
      list.insertBefore(row.nextElementSibling, row);
    }
  };

  list.querySelectorAll("[data-move]").forEach((button) => {
    button.addEventListener("click", () => {
      moveRow(button.closest("[data-sortable-row]"), button.dataset.move);
    });
  });

  list.querySelectorAll("[data-sortable-row]").forEach((row) => {
    row.addEventListener("dragstart", () => {
      draggedRow = row;
      row.classList.add("is-dragging");
    });

    row.addEventListener("dragend", () => {
      row.classList.remove("is-dragging");
      draggedRow = null;
    });

    row.addEventListener("dragover", (event) => {
      event.preventDefault();
      if (!draggedRow || draggedRow === row) return;
      const box = row.getBoundingClientRect();
      const afterMiddle = event.clientY > box.top + box.height / 2;
      list.insertBefore(draggedRow, afterMiddle ? row.nextSibling : row);
    });
  });
});
