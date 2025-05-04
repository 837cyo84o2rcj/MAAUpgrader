import tkinter as t, requests as r, zipfile as z, os as o, tempfile as tf, shutil as s, platform as p # type: ignore
from tkinter import ttk as tt, messagebox as m, filedialog as f
from threading import Thread as tr

class MAAUpdaterApp:
    def __init__(self, root):
        self.root = root
        root.title("MAA 更新工具")
        self.versions = []
        self.target_dir = o.path.join(o.getcwd(), 'MAA')
        self.github_token = None
        self.selected_platform = "win-x64"  # 默认平台

        # 平台扩展名映射
        self.platform_extensions = {
            "linux-aarch64": [".tar.gz", ".AppImage"],
            "linux-x86_64": [".tar.gz", ".AppImage"],
            "win-arm64": [".zip"],
            "win-x64": [".zip"],
            "macos": [".dmg", ".zip"]
        }

        self.setup_ui()

    def setup_ui(self):
        main_frame = tt.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=t.BOTH, expand=True)

        # GitHub Token 输入框
        token_frame = tt.Frame(main_frame)
        token_frame.pack(pady=5, fill=t.X)

        tt.Label(token_frame, text="GitHub Token:").pack(side=t.LEFT)
        self.token_entry = tt.Entry(token_frame, width=40)
        self.token_entry.pack(side=t.LEFT, padx=5)
        tt.Button(token_frame, text="获取版本列表", command=self.fetch_releases).pack(side=t.LEFT)

        # 平台选择菜单
        platform_frame = tt.Frame(main_frame)
        platform_frame.pack(pady=5, fill=t.X)

        tt.Label(platform_frame, text="选择平台:").pack(side=t.LEFT)
        self.platform_var = t.StringVar(value="win-x64")
        self.platform_menu = tt.Combobox(
            platform_frame,
            textvariable=self.platform_var,
            values=[
                "linux-aarch64",
                "linux-x86_64",
                "win-arm64",
                "win-x64",
                "macos"
            ],
            state="readonly",
            width=20
        )
        self.platform_menu.pack(side=t.LEFT, padx=5)

        # 版本列表
        list_frame = tt.Frame(main_frame)
        list_frame.pack(fill=t.BOTH, expand=True)

        self.version_listbox = t.Listbox(list_frame)
        scrollbar = tt.Scrollbar(list_frame)
        self.version_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.version_listbox.yview)

        self.version_listbox.pack(side=t.LEFT, fill=t.BOTH, expand=True)
        scrollbar.pack(side=t.RIGHT, fill=t.Y)
        self.version_listbox.bind('<<ListboxSelect>>', self.on_select)

        # 目录选择
        dir_frame = tt.Frame(main_frame)
        dir_frame.pack(pady=5, fill=t.X)

        tt.Button(dir_frame, text="选择目录", command=self.choose_directory).pack(side=t.LEFT)
        self.dir_label = tt.Label(dir_frame, text=self.target_dir)
        self.dir_label.pack(side=t.LEFT, padx=5)

        # 进度条
        self.progress = tt.Progressbar(main_frame, orient=t.HORIZONTAL, mode='determinate')
        self.progress.pack(pady=5, fill=t.X)

        # 状态栏
        self.status = tt.Label(main_frame, text="就绪")
        self.status.pack(fill=t.X)

        # 使用指南、作者和资源更新按钮
        button_frame = tt.Frame(main_frame)
        button_frame.pack(pady=5, fill=t.X)

        tt.Button(button_frame, text="使用指南", command=self.show_guide).pack(side=t.LEFT, padx=5)
        tt.Button(button_frame, text="作者", command=self.show_author).pack(side=t.LEFT, padx=5)
        tt.Button(button_frame, text="获取资源更新", command=self.fetch_resources).pack(side=t.LEFT, padx=5)

    def show_guide(self):
        guide_text = """
        [版本更新]
         1. GitHub Token:
         - 输入框输入Token
         - 获取方法: https://ivpsr.com/7560.html
        ────────────────────
         2. 选择平台:
         - 下拉菜单选择(如win-x64/linux-aarch64)
        ────────────────────
         3. 获取版本列表:
         - 点击"获取"按钮
         - 版本范围:
             - Windows: 最新20个.zip
             - MacOS: 最新5个.dmg/.zip
             - Linux: 最新5个.AppImage/.tar.gz
        ────────────────────
         4. 选择安装目录:
         - 点击"选择目录"按钮
        ────────────────────
         5. 下载与安装:
         - 双击版本开始下载
         - Windows特殊处理:
             - 有MAA.exe/MaaCore.dll则清空目录并解压
             - 否则仅下载
        ────────────────────
         6. 状态查看:
             - 底部状态栏显示进度
             - 进度条显示百分比

        [资源更新]
         - 点击"获取资源更新"按钮
         - 下载MAA项目的Dev分支并提取resource文件夹
        """
        m.showinfo("使用指南", guide_text)

    def show_author(self):
        m.showinfo("相关信息", "作者：837cyo84o2rcj；\n邮箱：k578322@163.com；\n开源协议：BSD-3-Clause License；")

    def choose_directory(self):
        path = f.askdirectory()
        if path:
            self.target_dir = path
            self.dir_label.config(text=path)

    def fetch_releases(self):
        self.github_token = self.token_entry.get().strip()
        if not self.github_token:
            m.showwarning("警告", "请输入 GitHub Token")
            return

        def worker():
            try:
                self.status.config(text="正在获取版本信息...")
                url = "https://api.github.com/repos/MaaAssistantArknights/MaaAssistantArknights/releases"
                headers = {
                    "User-Agent": "MAA-Updater/1.0",
                    "Authorization": f"token {self.github_token}"
                }

                response = r.get(url, headers=headers)

                if response.status_code != 200:
                    raise Exception(f"GitHub API 请求失败，状态码: {response.status_code}")

                try:
                    releases = response.json()
                except ValueError:
                    raise Exception("GitHub API 返回的数据不是有效的 JSON 格式")

                if not isinstance(releases, list):
                    raise Exception("GitHub API 返回的数据格式不符合预期")

                valid_versions = []
                selected_platform = self.platform_var.get()
                valid_extensions = self.platform_extensions[selected_platform]

                # 根据平台设置最大版本数
                max_versions = 20 if selected_platform.startswith("win") else 10

                for release in releases:
                    if len(valid_versions) >= max_versions:
                        break
                    if not isinstance(release, dict):
                        continue

                    assets = release.get('assets', [])
                    if not isinstance(assets, list):
                        continue

                    for asset in assets:
                        if not isinstance(asset, dict):
                            continue
                        asset_name = asset.get('name', '')
                        
                        # 新增排除调试符号包的过滤条件
                        if "MAAComponent-DebugSymbol" in asset_name:
                            continue
                        
                        if (selected_platform in asset_name and
                            any(asset_name.endswith(ext) for ext in valid_extensions)):
                            valid_versions.append({
                                'name': f"{release.get('tag_name', '未知版本')} ({o.path.splitext(asset_name)[1]})",
                                'url': asset.get('browser_download_url', '')
                            })
                            if len(valid_versions) >= max_versions:
                                break

                self.root.after(0, self.update_version_list, valid_versions)
                self.status.config(text="就绪")
            except Exception as e:
                self.root.after(0, lambda e=e: m.showerror("错误", f"获取版本失败: {str(e)}"))

        tr(target=worker, daemon=True).start()

    def fetch_resources(self):
        if not self.target_dir:
            m.showwarning("警告", "请先选择安装目录")
            return

        def worker():
            try:
                self.status.config(text="正在下载资源更新...")
                url = "https://github.com/MaaAssistantArknights/MaaAssistantArknights/archive/refs/heads/dev.zip"
                with tf.NamedTemporaryFile(delete=False) as tmp_file:
                    response = r.get(url, stream=True)
                    total_size = int(response.headers.get('content-length', 0))

                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        tmp_file.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100 if total_size else 0
                        self.root.after(0, self.progress.configure, {'value': progress})

                    tmp_path = tmp_file.name

                self.root.after(0, lambda: self.status.config(text="正在提取资源..."))
                self.extract_resources(tmp_path)
                o.remove(tmp_path)
                self.root.after(0, lambda: (
                    self.progress.configure({'value': 0}),
                    self.status.config(text="资源更新完成"),
                    m.showinfo("成功", "资源更新完成")
                ))
            except Exception as e:
                self.root.after(0, lambda e=e: (
                    m.showerror("错误", f"资源更新失败: {str(e)}"),
                    self.status.config(text="就绪"),
                    self.progress.configure({'value': 0})
                ))

        tr(target=worker, daemon=True).start()

    def extract_resources(self, zip_path):
        # 创建临时目录
        temp_dir = tf.mkdtemp()
        try:
            # 解压整个 dev 分支
            with z.ZipFile(zip_path) as zf:
                zf.extractall(temp_dir)

            # 找到 resource 文件夹
            dev_folder = o.path.join(temp_dir, "MaaAssistantArknights-dev")
            resource_folder = o.path.join(dev_folder, "resource")
            if not o.path.exists(resource_folder):
                raise Exception("未找到 resource 文件夹")

            # 将 resource 文件夹复制到目标目录
            dest_resource_folder = o.path.join(self.target_dir, "resource")
            if o.path.exists(dest_resource_folder):
                s.rmtree(dest_resource_folder)
            s.copytree(resource_folder, dest_resource_folder)
        finally:
            # 清理临时目录
            s.rmtree(temp_dir, ignore_errors=True)

    def update_version_list(self, versions):
        self.versions = versions
        self.version_listbox.delete(0, t.END)
        for v in versions:
            self.version_listbox.insert(t.END, v['name'])

    def on_select(self, event):
        if not self.version_listbox.curselection():
            return

        index = self.version_listbox.curselection()[0]
        selected = self.versions[index]

        if not self.target_dir:
            m.showwarning("警告", "请先选择安装目录")
            return

        if m.askyesno("确认", f"是否下载并安装 {selected['name']}?"):
            self.download_file(selected['url'])

    def download_file(self, url):
        def worker():
            try:
                self.status.config(text="正在下载...")
            
                # 确保目标目录存在
                o.makedirs(self.target_dir, exist_ok=True)
            
                # 检查目标目录是否被视为安装目录
                current_os = p.system().lower()
                selected_platform = self.platform_var.get()
                is_windows_target = selected_platform.startswith("win")
                is_install_dir = (current_os == 'windows' and is_windows_target and
                                 all(o.path.exists(o.path.join(self.target_dir, file))
                                 for file in ["MaaCore.dll", "MAA.exe"]))
            
                # 如果目标目录被视为安装目录，则清理目录
                if is_install_dir:
                    for item in o.listdir(self.target_dir):
                        item_path = o.path.join(self.target_dir, item)
                        if o.path.isfile(item_path) or o.path.islink(item_path):
                            o.unlink(item_path)
                        elif o.path.isdir(item_path):
                            s.rmtree(item_path)
            
                # 在目标目录中创建临时文件
                temp_filename = o.path.join(self.target_dir, "temp_download.zip")
                with open(temp_filename, "wb") as temp_file:
                    response = r.get(url, stream=True)
                    total_size = int(response.headers.get('content-length', 0))

                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        temp_file.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100 if total_size else 0
                        self.root.after(0, self.progress.configure, {'value': progress})

                # 调用 handle_zip 函数处理解压或移动操作
                self.root.after(0, lambda: self.status.config(text="正在处理..."))
                self.handle_zip(temp_filename)
                self.root.after(0, lambda: (
                    self.progress.configure({'value': 0}),
                    self.status.config(text="操作完成"),
                    m.showinfo("成功", "操作完成")
                ))
            except Exception as e:
                self.root.after(0, lambda e=e: (
                    m.showerror("错误", f"操作失败: {str(e)}"),
                    self.status.config(text="就绪"),
                    self.progress.configure({'value': 0})
                ))

        tr(target=worker, daemon=True).start()

    def handle_zip(self, zip_path):
        current_os = p.system().lower()
        selected_platform = self.platform_var.get()
        is_windows_target = selected_platform.startswith("win")

        # 确保目标目录存在
        o.makedirs(self.target_dir, exist_ok=True)

        # 仅Windows环境下载Windows版本时执行解压逻辑
        if current_os == 'windows' and is_windows_target:
            # 解压新版本
            with z.ZipFile(zip_path) as zf:
                zf.extractall(self.target_dir)
            o.remove(zip_path)
        else:
            # 其他情况直接移动压缩包
            dest_path = o.path.join(self.target_dir, o.path.basename(zip_path))
            s.move(zip_path, dest_path)

if __name__ == "__main__":
    root = t.Tk()
    app = MAAUpdaterApp(root)
    root.mainloop()
