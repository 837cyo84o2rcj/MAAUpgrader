import tkinter as tk, requests, zipfile, os, tempfile, shutil, platform
from tkinter import ttk, messagebox, filedialog
from threading import Thread

class MAAUpdaterApp:
    def __init__(self, root):
        self.root = root
        root.title("MAA 更新工具")
        self.versions = []
        self.target_dir = os.path.join(os.getcwd(), 'MAA')
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
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # GitHub Token 输入框
        token_frame = ttk.Frame(main_frame)
        token_frame.pack(pady=5, fill=tk.X)

        ttk.Label(token_frame, text="GitHub Token:").pack(side=tk.LEFT)
        self.token_entry = ttk.Entry(token_frame, width=40)
        self.token_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(token_frame, text="获取版本列表", command=self.fetch_releases).pack(side=tk.LEFT)

        # 平台选择下拉菜单
        platform_frame = ttk.Frame(main_frame)
        platform_frame.pack(pady=5, fill=tk.X)

        ttk.Label(platform_frame, text="选择平台:").pack(side=tk.LEFT)
        self.platform_var = tk.StringVar(value="win-x64")
        self.platform_menu = ttk.Combobox(
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
        self.platform_menu.pack(side=tk.LEFT, padx=5)

        # 版本列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.version_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame)
        self.version_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.version_listbox.yview)

        self.version_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.version_listbox.bind('<<ListboxSelect>>', self.on_select)

        # 目录选择
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(pady=5, fill=tk.X)

        ttk.Button(dir_frame, text="选择目录", command=self.choose_directory).pack(side=tk.LEFT)
        self.dir_label = ttk.Label(dir_frame, text=self.target_dir)
        self.dir_label.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(pady=5, fill=tk.X)

        # 状态栏
        self.status = ttk.Label(main_frame, text="就绪")
        self.status.pack(fill=tk.X)

        # 使用指南、作者和资源更新按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5, fill=tk.X)

        ttk.Button(button_frame, text="使用指南", command=self.show_guide).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="作者", command=self.show_author).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="获取资源更新", command=self.fetch_resources).pack(side=tk.LEFT, padx=5)

    def show_guide(self):
        guide_text = """
        ### 使用指南 ###

        版本更新
        ---------------------------------------------------------------------------------------------------------
        |1. 输入 GitHub Token：                                                                                 
        |   - 登录 GitHub 账号，进入 [GitHub Token 页面](https://github.com/settings/tokens)。                  
        |   - 点击 "Generate new token"，勾选 `repo` 和 `public_repo` 权限，生成 Token。                        
        |   - 将生成的 Token 粘贴到输入框中。                                                                                   
        ---------------------------------------------------------------------------------------------------------
        |2. 选择平台：                                                                                          
        |   - 从下拉菜单中选择需要下载的平台（如 win-x64、linux-aarch64 等）。                                  
        ---------------------------------------------------------------------------------------------------------
        |3.获取版本列表：                                                                                       
        |   - 点击“获取”按钮，程序会尝试从MAA的GitHub仓库获取版本列表。                                       
        |                                                                                                       
        |    版本列表范围：                                                                                     
        |       - Windows（x64与arm64均是）：最新的20个版本的.zip格式的安装包；                                 
        |       - MacOS：最新的5个版本的.dmg格式与.zip格式的安装包；                                            
        |       - Linux：最新的5个版本的.AppImage格式与.tar.gz格式的安装包。                                    
        ---------------------------------------------------------------------------------------------------------
        |4. 选择安装目录：                                                                                      
        |   - 点击“选择目录”按钮，选择安装包的下载（或安装）目录。                                                
        ---------------------------------------------------------------------------------------------------------
        |5. 下载与安装：                                                                                        
        |     - 下载：                                                                                          
        |         在版本列表中双击某个版本，程序会开始下载。                                                    
        |     - 安装：                                                                                          
        |         只有在Windows环境下载Windows版本时会执行如下操作：                                            
        |              1.检查指定目录下是否包含“MAA.exe”与“MaaCore.dll”;                                    
        |              2.若包含，则程序将清除指定目录下的所有内容，并将下载的安装包内的内容解压至指定目录；     
        |              3.若不包含，则程序将仅下载安装包至指定目录。                                             
        ---------------------------------------------------------------------------------------------------------            
        |6. 查看状态：                                                                                           
        |   - 界面底部的状态栏会显示当前的操作状态（如“正在下载”、“安装完成”等）。                          
        |   - 进度条会显示下载进度。                                                                            
        ---------------------------------------------------------------------------------------------------------

        资源更新
        ---------------------------------------------------------------------------------------------------------
        |    输入GitHub Token后，点击“获取资源更新”按钮，程序会尝试将MAA的GitHub项目的Dev分支整个下载，       
        |并从中提取resouce文件夹至目标目录。                                                                    
        ---------------------------------------------------------------------------------------------------------
        """
        messagebox.showinfo("使用指南", guide_text)

    def show_author(self):
        messagebox.showinfo("相关信息", "作者：837cyo84o2rcj；\n邮箱：k578322@163.com；\n开源协议：BSD-3-Clause License；")

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.target_dir = path
            self.dir_label.config(text=path)

    def fetch_releases(self):
        self.github_token = self.token_entry.get().strip()
        if not self.github_token:
            messagebox.showwarning("警告", "请输入 GitHub Token")
            return

        def worker():
            try:
                self.status.config(text="正在获取版本信息...")
                url = "https://api.github.com/repos/MaaAssistantArknights/MaaAssistantArknights/releases"
                headers = {
                    "User-Agent": "MAA-Updater/1.0",
                    "Authorization": f"token {self.github_token}"
                }

                response = requests.get(url, headers=headers)

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
                                'name': f"{release.get('tag_name', '未知版本')} ({os.path.splitext(asset_name)[1]})",
                                'url': asset.get('browser_download_url', '')
                            })
                            if len(valid_versions) >= max_versions:
                                break

                self.root.after(0, self.update_version_list, valid_versions)
                self.status.config(text="就绪")
            except Exception as e:
                self.root.after(0, lambda e=e: messagebox.showerror("错误", f"获取版本失败: {str(e)}"))

        Thread(target=worker, daemon=True).start()

    def fetch_resources(self):
        if not self.target_dir:
            messagebox.showwarning("警告", "请先选择安装目录")
            return

        def worker():
            try:
                self.status.config(text="正在下载资源更新...")
                url = "https://github.com/MaaAssistantArknights/MaaAssistantArknights/archive/refs/heads/dev.zip"
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    response = requests.get(url, stream=True)
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
                os.remove(tmp_path)
                self.root.after(0, lambda: (
                    self.progress.configure({'value': 0}),
                    self.status.config(text="资源更新完成"),
                    messagebox.showinfo("成功", "资源更新完成")
                ))
            except Exception as e:
                self.root.after(0, lambda e=e: (
                    messagebox.showerror("错误", f"资源更新失败: {str(e)}"),
                    self.status.config(text="就绪"),
                    self.progress.configure({'value': 0})
                ))

        Thread(target=worker, daemon=True).start()

    def extract_resources(self, zip_path):
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            # 解压整个 dev 分支
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(temp_dir)

            # 找到 resource 文件夹
            dev_folder = os.path.join(temp_dir, "MaaAssistantArknights-dev")
            resource_folder = os.path.join(dev_folder, "resource")
            if not os.path.exists(resource_folder):
                raise Exception("未找到 resource 文件夹")

            # 将 resource 文件夹复制到目标目录
            dest_resource_folder = os.path.join(self.target_dir, "resource")
            if os.path.exists(dest_resource_folder):
                shutil.rmtree(dest_resource_folder)
            shutil.copytree(resource_folder, dest_resource_folder)
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def update_version_list(self, versions):
        self.versions = versions
        self.version_listbox.delete(0, tk.END)
        for v in versions:
            self.version_listbox.insert(tk.END, v['name'])

    def on_select(self, event):
        if not self.version_listbox.curselection():
            return

        index = self.version_listbox.curselection()[0]
        selected = self.versions[index]

        if not self.target_dir:
            messagebox.showwarning("警告", "请先选择安装目录")
            return

        if messagebox.askyesno("确认", f"是否下载并安装 {selected['name']}?"):
            self.download_file(selected['url'])

    def download_file(self, url):
        def worker():
            try:
                self.status.config(text="正在下载...")
            
                # 确保目标目录存在
                os.makedirs(self.target_dir, exist_ok=True)
            
                # 检查目标目录是否被视为安装目录
                current_os = platform.system().lower()
                selected_platform = self.platform_var.get()
                is_windows_target = selected_platform.startswith("win")
                is_install_dir = (current_os == 'windows' and is_windows_target and
                                 all(os.path.exists(os.path.join(self.target_dir, file))
                                 for file in ["MaaCore.dll", "MAA.exe"]))
            
                # 如果目标目录被视为安装目录，则清理目录
                if is_install_dir:
                    for item in os.listdir(self.target_dir):
                        item_path = os.path.join(self.target_dir, item)
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
            
                # 在目标目录中创建临时文件
                temp_filename = os.path.join(self.target_dir, "temp_download.zip")
                with open(temp_filename, "wb") as temp_file:
                    response = requests.get(url, stream=True)
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
                    messagebox.showinfo("成功", "操作完成")
                ))
            except Exception as e:
                self.root.after(0, lambda e=e: (
                    messagebox.showerror("错误", f"操作失败: {str(e)}"),
                    self.status.config(text="就绪"),
                    self.progress.configure({'value': 0})
                ))

        Thread(target=worker, daemon=True).start()

    def handle_zip(self, zip_path):
        current_os = platform.system().lower()
        selected_platform = self.platform_var.get()
        is_windows_target = selected_platform.startswith("win")

        # 确保目标目录存在
        os.makedirs(self.target_dir, exist_ok=True)

        # 仅Windows环境下载Windows版本时执行解压逻辑
        if current_os == 'windows' and is_windows_target:
            # 解压新版本
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(self.target_dir)
            os.remove(zip_path)
        else:
            # 其他情况直接移动压缩包
            dest_path = os.path.join(self.target_dir, os.path.basename(zip_path))
            shutil.move(zip_path, dest_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = MAAUpdaterApp(root)
    root.mainloop()
