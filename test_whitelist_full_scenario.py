#!/usr/bin/env python3
"""
完整测试 whitelist ADD 命令的用户使用流程
模拟实际用户操作场景
"""

import json
import os
import shutil
from pathlib import Path

# 模拟 BaseConfig
class TestBaseConfig:
    def __init__(self, user_id: str, base_path: str = "/tmp/test_full_whitelist"):
        self.user_id = user_id
        self.base_path = base_path
        self.user_config_root = f"{base_path}/{user_id}"
        self.config_path = f"{base_path}/{user_id}/config.json"
        self.default_config_path = f"{base_path}/resources/default_config.json"
        self.default_config = {
            "settings": {},
            "channels": [],
            "is_admin": False
        }

    def whitelist_user(self):
        existing_users = self._get_existing_users()
        if self.user_id in existing_users:
            print(f"  ⚠️  用户 {self.user_id} 已在白名单中，跳过")
            return

        os.makedirs(f"{self.base_path}/{self.user_id}", exist_ok=True)
        config = self.default_config.copy()
        config["channels"].append(self.user_id)

        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"  ✅ 添加用户 {self.user_id}")

    def blacklist_user(self):
        """模拟移除用户"""
        user_dir = Path(f"{self.base_path}/{self.user_id}")
        if user_dir.exists():
            shutil.rmtree(user_dir)
            print(f"  🗑️  移除用户 {self.user_id}")

    def _get_existing_users(self):
        whitelist_dir = Path(self.base_path)
        if not whitelist_dir.exists():
            return []
        return [d.name for d in whitelist_dir.iterdir() if d.is_dir()]

    def get_config(self):
        """获取用户配置"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except:
            return None

# 模拟 get_whitelist()
def get_whitelist(base_path="/tmp/test_full_whitelist"):
    whitelist_dir = Path(base_path)
    if not whitelist_dir.exists():
        return []
    return [d.name for d in whitelist_dir.iterdir() if d.is_dir()]

# 模拟 on_whitelist 的 VIEW 操作
def view_whitelist(base_path="/tmp/test_full_whitelist"):
    """模拟 /whitelist VIEW 命令"""
    whitelist = get_whitelist(base_path)
    if not whitelist:
        return "Current Whitelist:\n\n(空)"
    msg = "Current Whitelist:\n\n"
    for user_id in whitelist:
        msg += f"{user_id}\n"
    return msg

# 模拟 on_whitelist 的 ADD 操作
def add_to_whitelist(user_id: str, base_path="/tmp/test_full_whitelist"):
    """模拟 /whitelist ADD 命令"""
    config = TestBaseConfig(user_id, base_path)
    config.whitelist_user()

def main():
    print("=" * 80)
    print("完整测试 whitelist ADD 命令用户使用流程")
    print("=" * 80)

    base_path = "/tmp/test_full_whitelist"

    # 清理
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    # 模拟场景：用户A添加自己到白名单
    print("\n📝 场景1: 用户A添加自己到白名单")
    user_a = "5047052833"
    add_to_whitelist(user_a, base_path)

    print("\n📋 用户A查看白名单:")
    print(view_whitelist(base_path))
    print(f"   白名单用户: {get_whitelist(base_path)}")

    # 模拟场景：用户B添加自己到白名单
    print("\n📝 场景2: 用户B添加自己到白名单")
    user_b = "123456789"
    add_to_whitelist(user_b, base_path)

    print("\n📋 用户A再次查看白名单:")
    print(view_whitelist(base_path))
    print(f"   白名单用户: {get_whitelist(base_path)}")

    # 验证
    print("\n" + "=" * 80)
    print("验证结果:")
    print("=" * 80)

    whitelist = get_whitelist(base_path)
    print(f"\n当前白名单: {whitelist}")
    print(f"白名单用户数: {len(whitelist)}")

    if user_a in whitelist and user_b in whitelist:
        print(f"\n✅ 用户A ({user_a}) 仍在白名单中")
        print(f"✅ 用户B ({user_b}) 已在白名单中")
        print("\n✅ 行为正常：没有用户被覆盖")
    else:
        print("\n❌ 发现问题!")
        if user_a not in whitelist:
            print(f"   ❌ 用户A ({user_a}) 丢失了!")
        if user_b not in whitelist:
            print(f"   ❌ 用户B ({user_b}) 未添加成功!")
        print("\n❌ 这证实了用户报告的问题：白名单被覆盖")

    # 检查每个用户的配置文件
    print("\n" + "=" * 80)
    print("详细检查每个用户的配置文件:")
    print("=" * 80)

    for user_id in whitelist:
        config = TestBaseConfig(user_id, base_path).get_config()
        if config:
            print(f"\n用户 {user_id}:")
            print(f"  配置文件: {config}")
            print(f"  channels: {config.get('channels', [])}")
            print(f"  is_admin: {config.get('is_admin', False)}")

    # 测试重复添加
    print("\n" + "=" * 80)
    print("测试重复添加用户:")
    print("=" * 80)

    print(f"\n再次添加用户A ({user_a}):")
    add_to_whitelist(user_a, base_path)

    print(f"\n最终白名单: {get_whitelist(base_path)}")
    print(f"白名单用户数: {len(whitelist)}")

    # 清理
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
