import tkinter as t,requests as r,zipfile as z,os as o,tempfile as tf,shutil as s,platform as p # type: ignore
from tkinter import ttk as tt,messagebox as m,filedialog as f
from threading import Thread as tr
class MAAUpdaterApp:
 def __init__(s,root):
  s.root=root;root.title("MAA 更新工具");s.versions=[];s.target_dir=o.path.join(o.getcwd(),'MAA');s.github_token=None;s.selected_platform="win-x64"
  s.platform_extensions={"linux-aarch64":[".tar.gz",".AppImage"],"linux-x86_64":[".tar.gz",".AppImage"],"win-arm64":[".zip"],"win-x64":[".zip"],"macos":[".dmg",".zip"]};s.setup_ui()
 def setup_ui(s):
  mf=tt.Frame(s.root);mf.pack(padx=10,pady=10,fill=t.BOTH,expand=True)
  tf=tt.Frame(mf);tf.pack(pady=5,fill=t.X);tt.Label(tf,text="GitHub Token:").pack(side=t.LEFT);s.token_entry=tt.Entry(tf,width=40);s.token_entry.pack(side=t.LEFT,padx=5);tt.Button(tf,text="获取版本列表",command=s.fetch_releases).pack(side=t.LEFT)
  pf=tt.Frame(mf);pf.pack(pady=5,fill=t.X);tt.Label(pf,text="选择平台:").pack(side=t.LEFT);s.platform_var=t.StringVar(value="win-x64");s.platform_menu=tt.Combobox(pf,textvariable=s.platform_var,values=["linux-aarch64","linux-x86_64","win-arm64","win-x64","macos"],state="readonly",width=20);s.platform_menu.pack(side=t.LEFT,padx=5)
  lf=tt.Frame(mf);lf.pack(fill=t.BOTH,expand=True);s.version_listbox=t.Listbox(lf);sb=tt.Scrollbar(lf);s.version_listbox.config(yscrollcommand=sb.set);sb.config(command=s.version_listbox.yview);s.version_listbox.pack(side=t.LEFT,fill=t.BOTH,expand=True);sb.pack(side=t.RIGHT,fill=t.Y);s.version_listbox.bind('<<ListboxSelect>>',s.on_select)
  df=tt.Frame(mf);df.pack(pady=5,fill=t.X);tt.Button(df,text="选择目录",command=s.choose_directory).pack(side=t.LEFT);s.dir_label=tt.Label(df,text=s.target_dir);s.dir_label.pack(side=t.LEFT,padx=5)
  s.progress=tt.Progressbar(mf,orient=t.HORIZONTAL,mode='determinate');s.progress.pack(pady=5,fill=t.X);s.status=tt.Label(mf,text="就绪");s.status.pack(fill=t.X)
  bf=tt.Frame(mf);bf.pack(pady=5,fill=t.X);tt.Button(bf,text="使用指南",command=s.show_guide).pack(side=t.LEFT,padx=5);tt.Button(bf,text="作者",command=s.show_author).pack(side=t.LEFT,padx=5);tt.Button(bf,text="获取资源更新",command=s.fetch_resources).pack(side=t.LEFT,padx=5)
 def show_guide(s):m.showinfo("使用指南","[版本更新]\n 1. GitHub Token:\n - 输入框输入Token\n - 获取方法: https://ivpsr.com/7560.html\n────────────────────\n 2. 选择平台:\n - 下拉菜单选择(如win-x64/linux-aarch64)\n────────────────────\n 3. 获取版本列表:\n - 点击\"获取\"按钮\n - 版本范围:\n - Windows: 最新20个.zip\n - MacOS: 最新5个.dmg/.zip\n - Linux: 最新5个.AppImage/.tar.gz\n────────────────────\n 4. 选择安装目录:\n - 点击\"选择目录\"按钮\n────────────────────\n 5. 下载与安装:\n - 双击版本开始下载\n - Windows特殊处理:\n - 有MAA.exe/MaaCore.dll则清空目录并解压\n - 否则仅下载\n────────────────────\n 6. 状态查看:\n - 底部状态栏显示进度\n - 进度条显示百分比\n\n[资源更新]\n - 点击\"获取资源更新\"按钮\n - 下载MAA项目的Dev分支并提取resource文件夹")
 def show_author(s):m.showinfo("相关信息","作者：837cyo84o2rcj；\n邮箱：k578322@163.com；\n开源协议：BSD-3-Clause License；")
 def choose_directory(s):
  path=f.askdirectory()
  if path:s.target_dir=path;s.dir_label.config(text=path)
 def fetch_releases(s):
  s.github_token=s.token_entry.get().strip()
  if not s.github_token:m.showwarning("警告","请输入 GitHub Token");return
  def worker():
   try:
    s.status.config(text="正在获取版本信息...");url="https://api.github.com/repos/MaaAssistantArknights/MaaAssistantArknights/releases";headers={"User-Agent":"MAA-Updater/1.6","Authorization":f"token {s.github_token}"};response=r.get(url,headers=headers)
    if response.status_code!=200:raise Exception(f"GitHub API 请求失败，状态码: {response.status_code}")
    try:releases=response.json()
    except ValueError:raise Exception("GitHub API 返回的数据不是有效的 JSON 格式")
    if not isinstance(releases,list):raise Exception("GitHub API 返回的数据格式不符合预期")
    valid_versions=[];selected_platform=s.platform_var.get();valid_extensions=s.platform_extensions[selected_platform];max_versions=20 if selected_platform.startswith("win")else 10
    for release in releases:
     if len(valid_versions)>=max_versions:break
     if not isinstance(release,dict):continue
     assets=release.get('assets',[])
     if not isinstance(assets,list):continue
     for asset in assets:
      if not isinstance(asset,dict):continue
      asset_name=asset.get('name','')
      if"MAAComponent-DebugSymbol"in asset_name:continue
      if(selected_platform in asset_name and any(asset_name.endswith(ext)for ext in valid_extensions)):valid_versions.append({'name':f"{release.get('tag_name','未知版本')}({o.path.splitext(asset_name)[1]})",'url':asset.get('browser_download_url','')})
      if len(valid_versions)>=max_versions:break
    s.root.after(0,s.update_version_list,valid_versions);s.status.config(text="就绪")
   except Exception as e:s.root.after(0,lambda e=e:m.showerror("错误",f"获取版本失败: {str(e)}"))
  tr(target=worker,daemon=True).start()
 def fetch_resources(s):
  if not s.target_dir:m.showwarning("警告","请先选择安装目录");return
  def worker():
   try:
    s.status.config(text="正在下载资源更新...");url="https://github.com/MaaAssistantArknights/MaaAssistantArknights/archive/refs/heads/dev.zip"
    with tf.NamedTemporaryFile(delete=False)as tmp_file:
     response=r.get(url,stream=True);total_size=int(response.headers.get('content-length',0));downloaded=0
     for chunk in response.iter_content(chunk_size=1024*1024):
      tmp_file.write(chunk);downloaded+=len(chunk);progress=(downloaded/total_size)*100 if total_size else 0;s.root.after(0,s.progress.configure,{'value':progress})
     tmp_path=tmp_file.name
    s.root.after(0,lambda:s.status.config(text="正在提取资源..."));s.extract_resources(tmp_path);o.remove(tmp_path);s.root.after(0,lambda:(s.progress.configure({'value':0}),s.status.config(text="资源更新完成"),m.showinfo("成功","资源更新完成")))
   except Exception as e:s.root.after(0,lambda e=e:(m.showerror("错误",f"资源更新失败: {str(e)}"),s.status.config(text="就绪"),s.progress.configure({'value':0})))
  tr(target=worker,daemon=True).start()
 def extract_resources(s,zip_path):
  temp_dir=tf.mkdtemp()
  try:
   with z.ZipFile(zip_path)as zf:zf.extractall(temp_dir)
   dev_folder=o.path.join(temp_dir,"MaaAssistantArknights-dev");resource_folder=o.path.join(dev_folder,"resource")
   if not o.path.exists(resource_folder):raise Exception("未找到 resource 文件夹")
   dest_resource_folder=o.path.join(s.target_dir,"resource")
   if o.path.exists(dest_resource_folder):s.rmtree(dest_resource_folder)
   s.copytree(resource_folder,dest_resource_folder)
  finally:s.rmtree(temp_dir,ignore_errors=True)
 def update_version_list(s,versions):
  s.versions=versions;s.version_listbox.delete(0,t.END)
  for v in versions:s.version_listbox.insert(t.END,v['name'])
 def on_select(s,event):
  if not s.version_listbox.curselection():return
  index=s.version_listbox.curselection()[0];selected=s.versions[index]
  if not s.target_dir:m.showwarning("警告","请先选择安装目录");return
  if m.askyesno("确认",f"是否下载并安装 {selected['name']}?"):s.download_file(selected['url'])
 def download_file(s,url):
  def worker():
   try:
    s.status.config(text="正在下载...");o.makedirs(s.target_dir,exist_ok=True);current_os=p.system().lower();selected_platform=s.platform_var.get();is_windows_target=selected_platform.startswith("win");is_install_dir=(current_os=='windows'and is_windows_target and all(o.path.exists(o.path.join(s.target_dir,file))for file in["MaaCore.dll","MAA.exe"]))
    if is_install_dir:
     for item in o.listdir(s.target_dir):
      item_path=o.path.join(s.target_dir,item)
      if o.path.isfile(item_path)or o.path.islink(item_path):o.unlink(item_path)
      elif o.path.isdir(item_path):s.rmtree(item_path)
    temp_filename=o.path.join(s.target_dir,"temp_download.zip")
    with open(temp_filename,"wb")as temp_file:
     response=r.get(url,stream=True);total_size=int(response.headers.get('content-length',0));downloaded=0
     for chunk in response.iter_content(chunk_size=1024*1024):
      temp_file.write(chunk);downloaded+=len(chunk);progress=(downloaded/total_size)*100 if total_size else 0;s.root.after(0,s.progress.configure,{'value':progress})
    s.root.after(0,lambda:s.status.config(text="正在处理..."));s.handle_zip(temp_filename);s.root.after(0,lambda:(s.progress.configure({'value':0}),s.status.config(text="操作完成"),m.showinfo("成功","操作完成")))
   except Exception as e:s.root.after(0,lambda e=e:(m.showerror("错误",f"操作失败: {str(e)}"),s.status.config(text="就绪"),s.progress.configure({'value':0})))
  tr(target=worker,daemon=True).start()
 def handle_zip(s,zip_path):
  current_os=p.system().lower();selected_platform=s.platform_var.get();is_windows_target=selected_platform.startswith("win");o.makedirs(s.target_dir,exist_ok=True)
  if current_os=='windows'and is_windows_target:
   with z.ZipFile(zip_path)as zf:zf.extractall(s.target_dir)
   o.remove(zip_path)
  else:dest_path=o.path.join(s.target_dir,o.path.basename(zip_path));s.move(zip_path,dest_path)
if __name__=="__main__":root=t.Tk();app=MAAUpdaterApp(root);root.mainloop()