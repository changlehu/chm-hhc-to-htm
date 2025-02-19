import os
import re
from pathlib import Path
import chardet

def detect_encoding(file_path):
    """尝试检测文件编码，如果失败则回退到 'gb18030'"""
    try:
        with open(file_path, 'rb') as f:
            rawdata = f.read(10000)
        encoding = chardet.detect(rawdata)['encoding']
        if encoding:
            encoding = encoding.lower()
            # 常见错误编码的修正
            if encoding in ['windows-1252', 'iso-8859-1']:
                return 'gb18030'  # 针对中文CHM的常见错误
            elif 'utf' in encoding:
                return 'utf-8'
            else:
                return encoding
        else:
            print(f"警告: chardet 检测编码失败，回退到 gb18030")
            return 'gb18030'
    except Exception as e:
        print(f"警告: 编码检测出错 ({e})，回退到 gb18030")
        return 'gb18030'

def convert_chm_files(folder):
    """转换HHC/HHK文件为HTML"""
    folder = Path(folder).resolve()
    hhc_file = None
    hhk_file = None

    # 首先扫描文件夹，找到HHC和HHK文件
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.hhc'):
                hhc_file = Path(root) / file
            elif file.lower().endswith('.hhk'):
                hhk_file = Path(root) / file

    # 转换HHC文件
    if hhc_file:
        print(f"\n处理目录文件: {hhc_file}")
        convert_file(hhc_file)

    # 转换HHK文件
    if hhk_file:
        print(f"\n处理索引文件: {hhk_file}")
        convert_file(hhk_file)

def convert_file(file_path):
    """转换单个HHC/HHK文件"""
    encoding = detect_encoding(file_path)
    print(f"使用编码: {encoding}")

    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        content = content.replace('\r\n', '\n').replace('\r', '\n')
    except Exception as e:
        print(f"错误: 读取文件失败 ({e})")
        return

    # 提取正文内容
    body_match = re.search(r'<body.*?>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
    if body_match:
        clean_content = body_match.group(1)
    else:
        print("警告：未找到<body>标签，尝试提取整个文件内容")
        clean_content = content

    # 对象标签转换
    def convert_object(match):
        print(f"完整匹配内容:\n{match.group(0)}")  # 调试信息
        
        # 改进的正则表达式
        params = re.findall(
            r'<param\s+name\s*=\s*"([^"]+)"\s+value\s*=\s*"([^"]+)"\s*/?>',
            match.group(0),
            re.DOTALL | re.IGNORECASE
        )
        
        print(f"提取的参数: {params}")  # 调试信息
        
        params = dict(params)
        name = params.get('Name', '')
        local = params.get('Local', '')
        image_number = params.get('ImageNumber', '')
        
        if local:
            local_path = Path(local)
            if not local_path.is_absolute():
                local_path = file_path.parent / local_path
                try:
                    local_path = local_path.resolve().relative_to(file_path.parent)
                except ValueError:
                    local_path = local
            return f'<li><a href="{local_path}" target="content">{name}</a></li>'
        elif image_number:  # 目录节点
            return f'<li><span class="section">{name}</span></li>'
        else:
            return f'<li>{name}</li>'

    # 处理内容
    def process_content(content):
        # 转换所有OBJECT标签
        content = re.sub(
            r'<object[^>]*>(.*?)</object>',
            convert_object,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # 清理空的UL标签
        content = re.sub(r'<ul>\s*</ul>', '', content, flags=re.IGNORECASE)
        # 清理空的LI标签
        content = re.sub(r'<li>\s*</li>', '', content, flags=re.IGNORECASE)
        
        return content

    clean_content = process_content(clean_content)

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
        .section {{ font-weight: bold; color: #333; }}
    </style>
</head>
<body>
<ul>
{clean_content}
</ul>
</body>
</html>'''

    # 根据原始文件类型生成新文件名
    if file_path.suffix.lower() == '.hhc':
        new_path = file_path.with_name(file_path.stem + '.hhc.htm')
    elif file_path.suffix.lower() == '.hhk':
        new_path = file_path.with_name(file_path.stem + '.hhk.htm')
    else:
        new_path = file_path.with_suffix('.htm')

    try:
        with open(new_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(final_html)
        print(f"已生成: {new_path}")
    except Exception as e:
        print(f"错误: 写入文件失败 ({e})")

def generate_framework(folder):
    """生成框架布局文件"""
    folder = Path(folder).resolve()
    hhc_file = None
    hhk_file = None

    # 查找转换后的HHC和HHK文件
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.hhc.htm'):
                hhc_file = file
            elif file.lower().endswith('.hhk.htm'):
                hhk_file = file

    # 创建/覆盖欢迎页
    welcome_path = folder / 'welcome.htm'
    with open(welcome_path, 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { padding: 20px; font-family: Microsoft YaHei; }
        h2 { color: #1a73e8; }
    </style>
</head>
<body>
    <h2>CHM 浏览器</h2>
    <p>请从左侧选择要查看的内容</p>
</body>
</html>''')

    # 保存框架文件
    index_path = folder / 'index.htm'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CHM浏览器</title>
    <style>
        .frame-container {{
            position: fixed;
            top: 0;
            bottom: 0;
            width: 100%;
            display: flex;
        }}
        #left-pane {{
            width: 300px;
            height: 100%;
            border-right: 1px solid #ddd;
        }}
        #right-pane {{
            flex: 1;
            height: 100%;
        }}
        iframe {{
            border: none;
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
    <div class="frame-container">
        <iframe id="left-pane" name="left" src="{hhc_file or 'welcome.htm'}"></iframe>
        <iframe id="right-pane" name="content" src="welcome.htm"></iframe>
    </div>
</body>
</html>''')

    print(f"框架文件已生成: {index_path}")
    if not hhc_file:
        print("警告：未找到转换后的HHC文件")
    if not hhk_file:
        print("警告：未找到转换后的HHK文件")

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
