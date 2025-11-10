#!/usr/bin/env python3
"""
测试 whitelist ADD 命令是否会覆盖原有用户
模拟用户报告的问题
"""

import json
import os
from pathlib import Path

# 模拟 BaseConfig 的核心逻辑
class TestBaseConfig:
    def __init__(self, user_id: str, base_path: str = "/tmp/test_whitelist"):
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
        """模拟 whitelist_user 方法"""
        # 模拟：检查用户是否已在白名单中
        existing_users = self._get_existing_users()
        if self.user_id in existing_users:
            print(f"  用户 {self.user_id} 已在白名单中，跳过")
            return

        # 创建用户目录
        os.makedirs(f"{self.base_path}/{self.user_id}", exist_ok=True)

        # 加载默认配置
        config = self.default_config.copy()

        # 关键操作：添加用户ID到 channels 列表
        config["channels"].append(self.user_id)
        print(f"  将用户 {self.user_id} 添加到 channels 列表")

        # 写入配置文件
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"  创建配置文件: {self.config_path}")
        print(f"  配置内容: {config}")

    def _get_existing_users(self):
        """获取现有白名单用户"""
        whitelist_dir = Path(self.base_path)
        if not whitelist_dir.exists():
            return []
        return [d.name for d in whitelist_dir.iterdir() if d.is_dir()]

    def get_channels(self):
        """获取用户配置中的 channels"""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            return config.get("channels", [])
        except:
            return []


def main():
    print("=" * 70)
    print("测试 whitelist ADD 命令行为")
    print("=" * 70)

    # 清理测试环境
    import shutil
    base_path = "/tmp/test_whitelist"
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

    # 创建默认配置
    os.makedirs(f"{base_path}/resources", exist_ok=True)
    with open(f"{base_path}/resources/default_config.json", "w") as f:
        json.dump({
            "settings": {},
            "channels": [],
            "is_admin": False
        }, f, indent=2)

    print("\n步骤1: 添加第一个用户 (5047052833)")
    user1 = TestBaseConfig("5047052833", base_path)
    user1.whitelist_user()

    print(f"\n用户1的 channels 列表: {user1.get_channels()}")

    print("\n步骤2: 添加第二个用户 (123456789)")
    user2 = TestBaseConfig("123456789", base_path)
    user2.whitelist_user()

    print(f"\n用户2的 channels 列表: {user2.get_channels()}")

    print("\n步骤3: 检查用户1的 channels 列表")
    print(f"用户1的 channels 列表: {user1.get_channels()}")

    print("\n" + "=" * 70)
    print("分析结果:")
    print("=" * 70)

    channels_user1 = user1.get_channels()
    channels_user2 = user2.get_channels()

    print(f"\n用户1 (5047052833) 的配置文件:")
    with open(user1.config_path, "r") as f:
        print(f.read())

    print(f"\n用户2 (123456789) 的配置文件:")
    with open(user2.config_path, "r") as f:
        print(f.read())

    # 分析是否存在覆盖问题
    if channels_user1 == ["5047052833"] and channels_user2 == ["123456789"]:
        print("\n✅ 每个用户有独立的配置文件，没有覆盖问题")
    else:
        print("\n❌ 存在配置共享或覆盖问题！")
        print(f"   用户1的channels: {channels_user1}")
        print(f"   用户2的channels: {channels_user2}")

    # 验证预期行为
    if channels_user1 == ["5047052833"] and channels_user2 == ["123456789"]:
        print("\n✅ 行为正常：每个用户独立管理，无覆盖")
    else:
        print("\n❌ 行为异常：用户配置可能相互影响")
        print("   建议检查 whitelist_user 实现")

    # 清理
    shutil.rmtree(base_path)

if __name__ == "__main__":
    main()
