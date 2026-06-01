# Personal Archive Site

一个本地动态管理、公网静态展示的个人艺术档案型网站。它用于长期整理摄影作品系列、文学写作和个人档案，视觉方向保持极简、安静、留白充分，接近艺术家档案网站，而不是摄影博客、相册图床或商业作品集模板。

## 技术栈

- 后端：Python, Flask, SQLite
- 图片处理：Pillow
- 文本：Markdown
- 模板：Jinja2
- 前端：HTML, CSS, 原生 JavaScript
- 部署：GitHub Pages 从 `main` 分支的 `/docs` 目录发布
- DNS：Cloudflare 管理自定义域名

## 本地安装

```bash
cd personal-archive-site
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动 Flask

```bash
python app.py
```

访问：

- 前台：http://127.0.0.1:5050/
- 后台：http://127.0.0.1:5050/admin/

首次启动会自动创建：

- `instance/site.db`
- `instance/secret_key.txt`
- `instance/admin_password.txt`
- `uploads/originals/`
- `uploads/display/`
- `uploads/covers/`

## 登录后台

后台路径是 `/admin`。默认密码写在：

```text
instance/admin_password.txt
```

首次启动后请直接编辑这个文件，把 `change-this-password` 改成你自己的本地后台密码。`instance/` 已写入 `.gitignore`，不会进入 Git。

## 上传照片

1. 进入 `/admin/collections/new` 创建摄影作品集。
2. 进入 `/admin/photos/upload` 上传照片，并选择所属作品集。
3. 可以一次选择一张或多张照片。
4. 多张照片会自动接在该作品集现有排序后面。
5. 可以把第一张上传照片自动设为作品集封面。
6. 上传后会保留原图到 `uploads/originals/`。
7. 同时生成前台展示图到 `uploads/display/`，封面图到 `uploads/covers/`。
8. 前台和静态导出只使用 WebP 展示图，不直接加载原图。

图片处理规则：

- display 最大宽度 1800px，WebP quality 82
- cover 最大宽度 2400px，WebP quality 86
- 默认不导出 `uploads/originals/`

## 创建文章

进入 `/admin/articles/new` 创建文章。

文章分类包括：

- `Essay`
- `Fiction`
- `Notes`

正文使用 Markdown。只有状态为 `published` 的文章会显示在前台和导出的静态站里。后台编辑页提供一个轻量 Markdown 预览，最终保存时由 Python Markdown 渲染为 HTML。

不同分类的发布逻辑：

- `Essay`：完整散文或随笔。标题必填，封面可选，摘要可手写；如果摘要为空，系统会从正文自动截取。
- `Fiction`：小说或故事。标题必填，封面可选，摘要可手写；如果摘要为空，系统会从正文自动截取。
- `Notes`：短札、日记性文字或片段。封面会被忽略；标题可以为空，系统会用发布时间生成标题；摘要为空时会从正文自动生成，作为 News 和 Notes 列表里的短句。

## 生成静态站

后台进入 `/admin/export`，点击 `Generate docs/`。

也可以在命令行运行：

```bash
python export_static.py
```

导出会生成：

- `docs/index.html`
- `docs/works/index.html`
- `docs/works/<slug>/index.html`
- `docs/texts/index.html`
- `docs/texts/<slug>/index.html`
- `docs/archive/index.html`
- `docs/about/index.html`
- `docs/contact/index.html`
- `docs/static/`
- `docs/uploads/display/`
- `docs/uploads/covers/`
- `docs/.nojekyll`

如果项目根目录存在 `CNAME` 文件，会自动复制到 `docs/CNAME`。

## 部署到 GitHub Pages

1. 把项目推送到 GitHub 仓库。
2. 在本地后台完成内容更新。
3. 生成静态站到 `docs/`。
4. 提交并推送：

```bash
git add .
git commit -m "Update archive site"
git push
```

5. 在 GitHub 仓库设置里打开 Pages：
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/docs`

GitHub Pages 只托管静态页面，不运行 Flask、不运行 SQLite、也不提供后台登录。

## 绑定自定义域名

1. 在项目根目录创建 `CNAME` 文件，内容为你的域名，例如：

```text
example.com
```

2. 重新运行静态导出，`CNAME` 会被复制到 `docs/CNAME`。
3. 在 GitHub Pages 设置中填写自定义域名。
4. 在 Cloudflare DNS 中按 GitHub Pages 的要求配置 `CNAME` 或 `A` 记录。
5. 等待 DNS 生效，并在 GitHub Pages 中启用 HTTPS。

## 为什么不把后台部署到公网

这个项目的核心原则是：

```text
本地动态管理，公网静态展示。
```

后台用于上传照片、编辑作品集、写文章和生成静态站。它会访问本地 SQLite、原图文件和管理密码，不适合作为公网服务暴露。公网只发布 `docs/` 里的静态 HTML、CSS、JS 和展示图，风险更低，也更稳定。

## Cloudflare Tunnel 的可选用途

Cloudflare Tunnel 只建议用于临时调试，例如：

- 临时让朋友预览本地 Flask 站点
- 临时远程访问本地后台
- 开发时检查移动端或外部网络访问

它不作为正式展示路径。正式访问路径是：

```text
GitHub Pages + 自定义域名
```

因为 Tunnel 依赖本地电脑开机、Flask 正在运行、`cloudflared` 正在运行，并且把后台暴露出去会增加安全风险。

## 图片存储注意事项

- `uploads/originals/` 保存原图，默认不进入 Git。
- `uploads/display/` 和 `uploads/covers/` 会被导出到 `docs/`，用于公网展示。
- 如果照片很多，GitHub 仓库可能会变大。建议只把必要的展示图发布到 Pages，原图长期保留在本地或独立备份。
- 不要手动把 `instance/`、数据库、后台密码、secret key 或原图提交到 Git。

## 目录结构

```text
personal-archive-site/
  app.py
  config.py
  db.py
  models.py
  image_utils.py
  export_static.py
  requirements.txt
  README.md
  .gitignore
  instance/
  templates/
  static/
  uploads/
  docs/
```
