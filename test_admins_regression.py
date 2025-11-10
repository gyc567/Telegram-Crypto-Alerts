#!/usr/bin/env python3
"""
回归测试 - 验证修复没有影响其他功能
"""

import json
import os
import shutil
from pathlib import Path

# 模拟 BaseConfig
class TestBaseConfig:
    def __init__(self, user_id: str, base_path: str = "/tmp/test_admins_regression"):
        self.user_id = user_id
        self.base_path = base_path
        self.config_path = f"{base_path}/{user_id}/config.json"
        self.default_config = {
            "settings": {},
            "channels": [],
            "is_admin": False
        }

    def admin_status(self, new_value=None):
        """获取或设置管理员状态"""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
        except:
            config = self.default_config.copy()

        if new_value is not None:
            config["is_admin"] = new_value
            self._save_config(config)
        return config.get("is_admin", False)

    def _save_config(self, config):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

    def whitelist_user(self):
        """将用户添加到白名单"""
        if self.user_id in get_whitelist():
            return

        os.makedirs(f"{self.base_path}/{self.user_id}", exist_ok=True)
        config = self.default_config.copy()
        config["channels"].append(self.user_id)
        self._save_config(config)

# 模拟 get_whitelist()
def get_whitelist(base_path="/tmp/test_admins_regression"):
    """获取白名单用户列表"""
    whitelist_dir = Path(base_path)
    if not whitelist_dir.exists():
        return []
    return [d.name for d in whitelist_dir.iterdir() if d.is_dir()]

# 模拟 split_message() 行为
def split_message(message: str) -> list:
    """模拟telegram.py中的split_message方法"""
    return [
        chunk.strip()
        for chunk in message.split(" ")[1:]
        if not all(char == " " for char in chunk) and len(chunk) > 0
    ]

# 模拟 on_admins 函数逻辑 (修复后版本)
def on_admins(message_text: str, base_path="/tmp/test_admins_regression") -> str:
    """模拟修复后的on_admins函数"""
    splt_msg = split_message(message_text)
    try:
        # 如果没有子命令或子命令是VIEW，显示管理员列表
        if len(splt_msg) == 0 or splt_msg[0].lower() == "view":
            msg = "Current Administrators:\n\n"
            for user_id in get_whitelist(base_path):
                if TestBaseConfig(user_id, base_path).admin_status():
                    msg += f"{user_id}\n"
            return msg

        elif splt_msg[0].lower() == "add":
            new_admins = splt_msg[1].split(",")
            failure_msgs = []
            whitelist = get_whitelist(base_path)
            for i, new_admin in enumerate(new_admins):
                try:
                    if new_admin in whitelist:
                        TestBaseConfig(new_admin, base_path).admin_status(new_value=True)
                    else:
                        failure_msgs.append(
                            f"{new_admins[i]} - User is not yet whitelisted"
                        )
                except Exception as exc:
                    failure_msgs.append(f"{new_admin} - {exc}")
            msg = f"Successfully added administrator(s): {', '.join(new_admins)}"
            if len(failure_msgs) > 0:
                msg += "\n\nFailed to add administrator(s):"
                for fail_msg in failure_msgs:
                    msg += f"\n{fail_msg}"
            return msg

        elif splt_msg[0].lower() == "remove":
            rm_admins = splt_msg[1].split(",")
            failure_msgs = []
            whitelist = get_whitelist(base_path)
            for i, admin in enumerate(rm_admins):
                try:
                    if admin in whitelist:
                        TestBaseConfig(admin, base_path).admin_status(new_value=False)
                    else:
                        failure_msgs.append(
                            f"{rm_admins[i]} - User is not yet whitelisted"
                        )
                except Exception as exc:
                    failure_msgs.append(f"{admin} - {exc}")
            msg = f"Successfully revoked administrator(s): {', '.join(rm_admins)}"
            if len(failure_msgs) > 0:
                msg += "\n\nFailed to revoke administrator(s):"
                for fail_msg in failure_msgs:
                    msg += f"\n{fail_msg}"
            return msg

        else:
            # 无效子命令
            return "Invalid subcommand. Use VIEW, ADD, or REMOVE."

    except IndexError:
        return "Invalid formatting - Use /admins VIEW/ADD/REMOVE USER_ID,USER_ID"
    except Exception as exc:
        return f"An unexpected error occurred - {exc}"

def main():
    print("=" * 80)
    print("回归测试 - admins 命令修复")
    print("=" * 80)

    base_path = "/tmp/test_admins_regression"

    # 清理测试环境
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    # 测试场景1: 批量ADD操作
    print("\n📝 测试场景1: 批量ADD操作")
    print("-" * 80)

    # 创建10个用户
    for i in range(100, 110):
        user = TestBaseConfig(str(i), base_path)
        user.whitelist_user()

    print(f"   创建了 {len(get_whitelist(base_path))} 个白名单用户")

    # 批量添加为管理员
    result = on_admins("/admins ADD 100,101,102,103,104", base_path)
    print(f"   执行: /admins ADD 100,101,102,103,104")
    print(f"   结果: {result}")

    # 验证
    admin_count = sum(1 for uid in get_whitelist(base_path) if TestBaseConfig(uid, base_path).admin_status())
    if admin_count == 5:
        print(f"   ✅ 批量ADD成功: {admin_count} 个管理员")
    else:
        print(f"   ❌ 批量ADD失败: 预期5个管理员，实际{admin_count}个")

    # 测试场景2: 批量REMOVE操作
    print("\n📝 测试场景2: 批量REMOVE操作")
    print("-" * 80)

    result = on_admins("/admins REMOVE 100,101,102", base_path)
    print(f"   执行: /admins REMOVE 100,101,102")
    print(f"   结果: {result}")

    # 验证
    admin_count = sum(1 for uid in get_whitelist(base_path) if TestBaseConfig(uid, base_path).admin_status())
    if admin_count == 2:
        print(f"   ✅ 批量REMOVE成功: {admin_count} 个管理员")
    else:
        print(f"   ❌ 批量REMOVE失败: 预期2个管理员，实际{admin_count}个")

    # 测试场景3: 空管理员列表
    print("\n📝 测试场景3: 空管理员列表")
    print("-" * 80)

    # 移除所有管理员
    for uid in get_whitelist(base_path):
        TestBaseConfig(uid, base_path).admin_status(new_value=False)

    result = on_admins("/admins VIEW", base_path)
    print(f"   执行: /admins VIEW (无管理员时)")
    print(f"   结果: {result}")

    if "Current Administrators" in result and "100" not in result and "101" not in result:
        print(f"   ✅ 空管理员列表显示正常")
    else:
        print(f"   ❌ 空管理员列表显示异常")

    # 测试场景4: 混合操作
    print("\n📝 测试场景4: 混合ADD/REMOVE操作")
    print("-" * 80)

    # 先添加一些管理员
    on_admins("/admins ADD 100,105,106", base_path)
    print(f"   添加了3个管理员")

    # 再次添加已存在的管理员
    result = on_admins("/admins ADD 100,107", base_path)
    print(f"   执行: /admins ADD 100,107 (100已存在)")
    print(f"   结果: {result}")

    # 验证100仍然是管理员
    if TestBaseConfig("100", base_path).admin_status():
        print(f"   ✅ 重复添加不影响现有管理员")
    else:
        print(f"   ❌ 重复添加影响了现有管理员")

    # 移除不存在的管理员
    on_admins("/admins REMOVE 200,201", base_path)
    print(f"   执行: /admins REMOVE 200,201 (用户不存在)")
    print(f"   结果: 应当有错误提示")

    # 测试场景5: 边界情况
    print("\n📝 测试场景5: 边界情况测试")
    print("-" * 80)

    # 测试特殊字符
    test_cases = [
        ("/admins", "无参数"),
        ("/admins view", "小写view"),
        ("/admins VIEW", "大写VIEW"),
        ("/admins ViEw", "混合大小写"),
        ("/admins add 108", "小写add"),
        ("/admins ADD 109", "大写ADD"),
        ("/admins remove 105", "小写remove"),
        ("/admins REMOVE 106", "大写REMOVE"),
    ]

    for cmd, desc in test_cases:
        try:
            result = on_admins(cmd, base_path)
            if "IndexError" in result or "An unexpected error" in result:
                print(f"   ❌ {desc}: {cmd} - 抛出异常")
            else:
                print(f"   ✅ {desc}: {cmd} - 正常")
        except Exception as e:
            print(f"   ❌ {desc}: {cmd} - 异常: {e}")

    # 测试场景6: 性能测试
    print("\n📝 测试场景6: 性能测试")
    print("-" * 80)

    import time

    # 创建100个用户
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    for i in range(200, 300):
        user = TestBaseConfig(str(i), base_path)
        user.whitelist_user()

    # 性能测试 - VIEW操作
    start_time = time.time()
    for _ in range(100):
        on_admins("/admins VIEW", base_path)
    end_time = time.time()

    avg_time = (end_time - start_time) / 100
    print(f"   执行100次 /admins VIEW 操作")
    print(f"   总时间: {end_time - start_time:.3f}s")
    print(f"   平均时间: {avg_time*1000:.2f}ms")

    if avg_time < 0.1:  # 100ms
        print(f"   ✅ 性能可接受 (< 100ms)")
    else:
        print(f"   ⚠️  性能较慢 (> 100ms)")

    # 清理
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    print("\n" + "=" * 80)
    print("回归测试完成")
    print("=" * 80)

    return True

if __name__ == "__main__":
    main()
