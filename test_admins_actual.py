#!/usr/bin/env python3
"""
验证当前 /admins 命令的实际行为
模拟生产环境中的实际执行情况
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, '/Users/guoyingcheng/dreame/code/Telegram-Crypto-Alerts/src')

# 模拟 Telegram 消息对象
class MockMessage:
    def __init__(self, text):
        self.text = text
        self.from_user = type('User', (), {'id': 123456, 'username': 'testuser'})()

# 模拟 BaseConfig 和相关函数
class BaseConfig:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_path = "/tmp/test_admins"
        self.config_path = f"{self.base_path}/{user_id}/config.json"

    def admin_status(self, new_value=None):
        """获取或设置管理员状态"""
        import json
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
        except:
            config = {"settings": {}, "channels": [], "is_admin": False}

        if new_value is not None:
            config["is_admin"] = new_value
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        return config.get("is_admin", False)

def get_whitelist():
    """获取白名单用户列表"""
    import pathlib
    whitelist_dir = pathlib.Path("/tmp/test_admins")
    if not whitelist_dir.exists():
        return []
    return [d.name for d in whitelist_dir.iterdir() if d.is_dir()]

# 复制实际的 split_message 方法
def split_message(message: str) -> list:
    return [
        chunk.strip()
        for chunk in message.split(" ")[1:]
        if not all(char == " " for char in chunk) and len(chunk) > 0
    ]

# 复制实际的 on_admins 逻辑
def on_admins_test(message_text: str):
    """使用当前代码中的实际逻辑"""
    splt_msg = split_message(message_text)
    try:
        # 如果没有子命令或子命令是VIEW，显示管理员列表
        if len(splt_msg) == 0 or splt_msg[0].lower() == "view":
            msg = "Current Administrators:\n\n"
            for user_id in get_whitelist():
                if BaseConfig(user_id).admin_status():
                    msg += f"{user_id}\n"
            return f"✅ SUCCESS: {msg}"

        elif splt_msg[0].lower() == "add":
            return f"✅ SUCCESS: ADD command (not tested in this run)"

        elif splt_msg[0].lower() == "remove":
            return f"✅ SUCCESS: REMOVE command (not tested in this run)"

        else:
            # 无效子命令
            return f"❌ ERROR: Invalid subcommand. Use VIEW, ADD, or REMOVE."

    except IndexError:
        # 这不应该再发生，但保留以防万一
        return f"❌ ERROR: Invalid formatting - Use /admins VIEW/ADD/REMOVE USER_ID,USER_ID"
    except Exception as exc:
        return f"❌ ERROR: An unexpected error occurred - {exc}"

def main():
    print("=" * 80)
    print("验证当前 /admins 命令的实际行为")
    print("=" * 80)

    import shutil
    base_path = "/tmp/test_admins"

    # 清理并设置测试环境
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    # 创建测试用户
    for uid in ["111", "222", "333"]:
        os.makedirs(f"{base_path}/{uid}", exist_ok=True)
        import json
        config = {"settings": {}, "channels": [], "is_admin": False}
        if uid == "111":
            config["is_admin"] = True
        with open(f"{base_path}/{uid}/config.json", "w") as f:
            json.dump(config, f, indent=2)

    print(f"\n测试环境设置完成:")
    print(f"  白名单用户: {get_whitelist()}")
    print(f"  管理员: 111")

    # 执行测试用例
    print("\n" + "=" * 80)
    print("执行测试用例")
    print("=" * 80)

    test_cases = [
        ("/admins", "无子命令"),
        ("/admins view", "小写view"),
        ("/admins VIEW", "大写VIEW"),
        ("/admins ViEw", "混合大小写"),
        ("/admins add 222", "小写add"),
        ("/admins ADD 333", "大写ADD"),
        ("/admins INVALID", "无效子命令"),
    ]

    for cmd, desc in test_cases:
        print(f"\n测试: {desc}")
        print(f"  命令: {cmd}")
        result = on_admins_test(cmd)
        print(f"  结果: {result}")

    # 清理
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
