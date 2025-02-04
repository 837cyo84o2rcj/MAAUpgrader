import tkinter as tk, requests, zipfile, os, tempfile, shutil
from tkinter import ttk, messagebox, filedialog
from threading import Thread

class MAAUpdaterApp:
    def __init__(self, root):
        self.root = root
        root.title("MAA 更新工具")
        self.versions = []
        self.target_dir = os.path.join(os.getcwd(), 'MAA')
        self.github_token = None  # 存储 GitHub Token
        
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
        ttk.Button(token_frame, text="获取", command=self.fetch_releases).pack(side=tk.LEFT)

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

        # 使用指南和作者按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5, fill=tk.X)
        
        ttk.Button(button_frame, text="使用指南", command=self.show_guide).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="作者", command=self.show_author).pack(side=tk.LEFT, padx=5)

    def show_guide(self):
        guide_text = """
        ### 使用指南 ###

        1. 输入 GitHub Token：
           - 登录 GitHub 账号，进入 [GitHub Token 页面](https://github.com/settings/tokens)。
           - 点击 "Generate new token"，勾选 `repo` 和 `public_repo` 权限，生成 Token。
           - 将生成的 Token 粘贴到输入框中。

        2. 获取版本列表：
           - 点击“获取”按钮，程序会尝试获取最新的 10 个版本。

        3. 选择安装目录：
           - 点击“选择目录”按钮，选择下载目录。

        4. 下载并安装：
           - 在版本列表中双击某个版本，程序会开始下载。
           - 如果目标目录中已包含 `MaaCore.dll` 和 `MAA.exe`，则目标目录将被视为MAA的安装目录，程序会在清理目标目录下的所有内容后将下载的压缩包内容解压至目标目录。
           - 如果目标目录中不包含上述文件，程序只会下载压缩包到目标目录，不会解压。

        5. 查看状态：
           - 界面底部的状态栏会显示当前的操作状态（如“正在下载”、“安装完成”等）。
           - 进度条会显示下载进度。
        """
        messagebox.showinfo("使用指南", guide_text)

    def show_author(self):
        messagebox.showinfo("作者", "作者：chndhjhf67")

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
                for release in releases:
                    if len(valid_versions) >= 10:
                        break
                    if not isinstance(release, dict):
                        continue
                    
                    assets = release.get('assets', [])
                    if not isinstance(assets, list):
                        continue
                    
                    for asset in assets:
                        if not isinstance(asset, dict):
                            continue
                        if 'win-x64' in asset.get('name', '') and asset.get('name', '').endswith('.zip'):
                            valid_versions.append({
                                'name': release.get('tag_name', '未知版本'),
                                'url': asset.get('browser_download_url', '')
                            })
                            break
                
                self.root.after(0, self.update_version_list, valid_versions)
                self.status.config(text="就绪")
            except Exception as e:
                self.root.after(0, lambda e=e: messagebox.showerror("错误", f"获取版本失败: {str(e)}"))
        
        Thread(target=worker, daemon=True).start()

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
                
                self.root.after(0, lambda: self.status.config(text="正在处理..."))
                self.handle_zip(tmp_path)
                os.remove(tmp_path)
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
        # 检查目标目录是否包含 MaaCore.dll 和 MAA.exe
        has_required_files = all(
            os.path.exists(os.path.join(self.target_dir, file))
            for file in ["MaaCore.dll", "MAA.exe"]
        )
        
        if has_required_files:
            # 清空目标目录
            for item in os.listdir(self.target_dir):
                item_path = os.path.join(self.target_dir, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            # 解压新版本
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(self.target_dir)
        else:
            # 只下载压缩包，不进行解压
            shutil.move(zip_path, os.path.join(self.target_dir, os.path.basename(zip_path)))

if __name__ == "__main__":
    root = tk.Tk()
    app = MAAUpdaterApp(root)
    root.mainloop()
