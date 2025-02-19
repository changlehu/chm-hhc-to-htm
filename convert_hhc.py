import os
import re
from pathlib import Path
import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read(10000)
    return chardet.detect(rawdata)['encoding']

def convert_chm_files(folder):
    """转换HHC/HHK文件（完整版）"""
    folder = Path(folder).resolve()
    
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.hhc', '.hhk')):
                file_path = Path(root) / file
                print(f"\n处理文件: {file_path}")
                
                # 自动检测编码（增加回退机制）
                try:
                    encoding = detect_encoding(file_path)
                    # 对中文编码的强制修正
                    if encoding.lower() in ['windows-1252', 'iso-8859-1']:
                        encoding = 'gb18030'
                except Exception as e:
                    print(f"编码检测失败: {str(e)}")
                    encoding = 'gb18030'  # 中文常用编码回退
                
                print(f"使用编码: {encoding} (自动修正后)" if '修正' in locals() else f"使用编码: {encoding}")
                
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                except Exception as e:
                    print(f"读取文件失败: {str(e)}")
                    continue
                
                # 改进的内容提取逻辑（处理不规范的HTML结构）
                body_start = content.lower().find('<body')
                body_end = content.lower().rfind('</body>')
                
                if body_start != -1:
                    body_start = content.find('>', body_start) + 1
                    clean_content = content[body_start:body_end] if body_end != -1 else content[body_start:]
                else:
                    clean_content = content  # 处理没有body标签的情况

                # 替换清理逻辑为对象标签转换
                def convert_object(match):
                    params = re.findall(r'<param\s+name="([^"]+)"\s+value="([^"]+)"\s*/>', match.group(0))
                    params = dict(params)
                    name = params.get('Name', '')
                    local = params.get('Local', '')
                    if local:
                        return f'<a href="{Path(local).stem}.htm" target="content">{name}</a>'
                    return name  # 处理没有Local参数的情况

                clean_content = re.sub(
                    r'<object[^>]*>(.*?)</object>',
                    convert_object,
                    clean_content,
                    flags=re.DOTALL | re.I
                )

                # 移除空的<li>标签
                clean_content = re.sub(r'<li>\s*</li>', '', clean_content)

                # 修复链接替换（增强路径处理）
                clean_content = re.sub(
                    r'href=(["\'])(.*?\.html?)(["\'])', 
                    lambda m: f'href={m.group(1)}{Path(m.group(2)).stem}.htm{m.group(3)} target="content"', 
                    clean_content,
                    flags=re.I
                )
                
                # 生成HTML
                final_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <base href="./">
    <style>
        body {{ margin: 8px; font-family: Microsoft YaHei; }}
        ul {{ padding-left: 20px; list-style: none; }}
        li {{ margin: 6px 0; }}
        a {{ color: #06c; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
{clean_content}
</body>
</html>'''

                new_path = file_path.with_suffix('.htm')
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                print(f"已生成: {new_path}")

def generate_framework(folder):
    """生成框架布局文件（完整版）"""
    folder = Path(folder).resolve()
    
    framework_html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CHM浏览器</title>
    <style>
        .frame-container {
            position: fixed;
            top: 0;
            bottom: 0;
            width: 100%;
            display: flex;
        }
        #left-pane { 
            width: 300px; 
            height: 100%;
            border-right: 1px solid #ddd;
        }
        #right-pane {
            flex: 1;
            height: 100%;
        }
        iframe {
            border: none;
            width: 100%;
            height: 100%;
        }
    </style>
</head>
<body>
    <div class="frame-container">
        <iframe id="left-pane" name="left" src="hhc.htm"></iframe>
        <iframe id="right-pane" name="content" src="welcome.htm"></iframe>
    </div>
</body>
</html>'''

    # 创建/覆盖欢迎页
    welcome_path = folder / 'welcome.htm'
    with open(welcome_path, 'w', encoding='utf-8') as f:
        f.write('''<html>
            <body style="padding:20px; font-family: Microsoft YaHei">
                <h2 style="color:#1a73e8">CHM 浏览器</h2>
                <p>请从左侧目录选择要查看的内容</p>
                <ul>
                    <li>📂 目录 - 按章节结构浏览</li>
                </ul>
            </body>
        </html>''')

    # 保存框架文件
    index_path = folder / 'index.htm'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(framework_html)
    
    print(f"框架文件已生成: {index_path}")

if __name__ == '__main__':
    try:
        import chardet
    except ImportError:
        print("请先安装依赖库：pip install chardet")
        exit(1)
    
    target_folder = input('请输入反编译目录的完整路径：')
    target_folder = Path(target_folder).resolve()
    
    if not target_folder.exists():
        print(f"错误：路径不存在 - {target_folder}")
        exit(1)
        
    print('\n正在转换HHC/HHK文件...')
    convert_chm_files(target_folder)
    
    print('\n正在生成浏览框架...')
    generate_framework(target_folder)
    
    print(f'\n操作完成！请访问：\n{target_folder}/index.htm')
    print('提示：若直接打开有问题，请使用本地HTTP服务器（如：python -m http.server）')
