import yaml
import os


def load_yaml(path):
    """
    加载任意 yaml 文件，支持绝对/相对路径。
    如文件不存在自动抛错并提示修正。
    返回：dict/list
    """
    # 自动适配绝对和相对路径
    if not os.path.isabs(path):
        # 优先从当前目录/工程根目录查找
        local_path = os.path.join(os.getcwd(), path)
        if os.path.exists(local_path):
            path = local_path
        else:
            # 尝试从 config.ROOT_DIR 读取（兼容工程树多入口）
            try:
                import config
                root_path = os.path.join(config.ROOT_DIR, path)
                if os.path.exists(root_path):
                    path = root_path
            except ImportError:
                pass
    if not os.path.exists(path):
        raise FileNotFoundError(f"内容池yaml不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        raise ValueError(f"内容池yaml为空: {path}")
    return data


def auto_init_yaml(path, template_dict=None):
    """
    自动生成模板yaml文件（如缺失），支持中英表头、内容池初始内容。
    """
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(template_dict or {}, f, allow_unicode=True)
        print(f"已自动生成内容池模板: {path}")

# 批量内容池自动检测与生成（可扩展，适合多业务场景）


def batch_init_yaml(yaml_list):
    for item in yaml_list:
        if isinstance(item, str):
            auto_init_yaml(item)
        elif isinstance(item, tuple) and len(item) == 2:
            auto_init_yaml(item[0], item[1])
