#!/usr/bin/env python3
"""
测试 admins VIEW 命令修复
验证修复后的代码能正确处理所有子命令
"""

import json
import os
import shutil
from pathlib import Path

# 模拟 BaseConfig
class TestBaseConfig:
    def __init__(self, user_id: str, base_path: str = "/tmp/test_admins_fix"):
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
def get_whitelist(base_path="/tmp/test_admins_fix"):
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
def on_admins(message_text: str, base_path="/tmp/test_admins_fix") -> str:
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
    print("测试 admins VIEW 命令修复")
    print("=" * 80)

    base_path = "/tmp/test_admins_fix"

    # 清理测试环境
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    # 设置测试用户
    print("\n📝 设置测试环境...")
    user1 = TestBaseConfig("123456", base_path)
    user1.whitelist_user()
    user1.admin_status(new_value=True)  # 设为管理员

    user2 = TestBaseConfig("789012", base_path)
    user2.whitelist_user()
    user2.admin_status(new_value=True)  # 设为管理员

    user3 = TestBaseConfig("345678", base_path)
    user3.whitelist_user()
    # 不设置为管理员

    print(f"   白名单用户: {get_whitelist(base_path)}")
    print(f"   管理员用户: 123456, 789012")

    # 测试用例
    tests = [
        {
            "name": "测试1: /admins (无子命令)",
            "input": "/admins",
            "expected_contains": ["Current Administrators", "123456", "789012"],
            "should_not_contain": ["IndexError", "Invalid formatting"]
        },
        {
            "name": "测试2: /admins view (小写)",
            "input": "/admins view",
            "expected_contains": ["Current Administrators", "123456", "789012"],
            "should_not_contain": ["IndexError", "Invalid formatting"]
        },
        {
            "name": "测试3: /admins VIEW (大写)",
            "input": "/admins VIEW",
            "expected_contains": ["Current Administrators", "123456", "789012"],
            "should_not_contain": ["IndexError", "Invalid formatting"]
        },
        {
            "name": "测试4: /admins ADD 345678",
            "input": "/admins ADD 345678",
            "expected_contains": ["Successfully added administrator(s)", "345678"],
            "should_not_contain": ["IndexError", "Failed to add"]
        },
        {
            "name": "测试5: /admins REMOVE 345678",
            "input": "/admins REMOVE 345678",
            "expected_contains": ["Successfully revoked administrator(s)", "345678"],
            "should_not_contain": ["IndexError", "Failed to revoke"]
        },
        {
            "name": "测试6: /admins INVALID (无效子命令)",
            "input": "/admins INVALID",
            "expected_contains": ["Invalid subcommand"],
            "should_not_contain": ["IndexError", "Current Administrators"]
        },
        {
            "name": "测试7: /admins ADD 999999 (非白名单用户)",
            "input": "/admins ADD 999999",
            "expected_contains": ["Failed to add", "not yet whitelisted"],
            "should_not_contain": ["IndexError"]
        },
    ]

    # 执行测试
    print("\n" + "=" * 80)
    print("执行测试用例")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, test in enumerate(tests, 1):
        print(f"\n{test['name']}")
        print(f"  输入: {test['input']}")

        try:
            result = on_admins(test['input'], base_path)
            print(f"  输出: {result}")

            # 验证结果
            all_passed = True

            # 检查预期包含的文本
            for expected in test['expected_contains']:
                if expected not in result:
                    print(f"  ❌ FAIL: 预期包含 '{expected}'")
                    all_passed = False

            # 检查不应该包含的文本
            for not_expected in test['should_not_contain']:
                if not_expected in result:
                    print(f"  ❌ FAIL: 不应该包含 '{not_expected}'")
                    all_passed = False

            if all_passed:
                print(f"  ✅ PASS")
                passed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ❌ FAIL: 抛出异常 - {e}")
            failed += 1

    # 测试完成后检查管理员状态
    print("\n" + "=" * 80)
    print("验证管理员状态")
    print("=" * 80)

    for user_id in get_whitelist(base_path):
        is_admin = TestBaseConfig(user_id, base_path).admin_status()
        print(f"用户 {user_id}: {'管理员' if is_admin else '普通用户'}")

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        print("\n✅ 所有测试通过！修复成功！")
    else:
        print(f"\n❌ {failed} 个测试失败")

    # 清理
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    print("\n" + "=" * 80)

    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
