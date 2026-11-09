#!/usr/bin/env python3
"""把模块只读令牌同步到 XRobot BSP 与模块仓库。

目标仓库来自两处显式清单，不扫描仓库内容，因此 App 只需 Metadata 与
Secrets 权限：

- index.yaml 中的 HFUT-WDR 模块；
- ci/bsp-repositories.txt 中列出的 BSP 仓库。

App 安装令牌只能访问安装范围内的仓库；目标不在安装范围内时逐个报告。
可选 SYNC_EXTRA_REPOS 用逗号分隔补充仓库。
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
SECRET_NAME = "WDR_MODULES_READ_TOKEN"
ORG = os.environ.get("SYNC_ORG", "HFUT-WDR")
TOKEN = os.environ["SYNC_TOKEN"]
VALUE = os.environ.get("SYNC_VALUE", "")
DRY_RUN = os.environ.get("SYNC_DRY_RUN", "") == "1"
EXTRA = {name.strip() for name in os.environ.get("SYNC_EXTRA_REPOS", "").split(",")
         if name.strip()}
INDEX = Path(os.environ.get("SYNC_INDEX", "index.yaml"))
BSP_LIST = Path(os.environ.get("SYNC_BSP_LIST", "ci/bsp-repositories.txt"))


def call(method, path, payload=None):
    request = urllib.request.Request(
        API + path,
        method=method,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request) as response:
        body = response.read()
    return json.loads(body) if body else None


def index_repositories():
    """从模块索引读取 owner/repo。索引只允许简单 YAML，按行解析即可。"""
    if not INDEX.exists():
        raise SystemExit(f"找不到模块索引 {INDEX}")
    repos = set()
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- id:"):
            module_id = line.split(":", 1)[1].strip()
            if "/" in module_id and module_id.startswith(ORG + "/"):
                repos.add(module_id)
    return repos


def bsp_repositories():
    if not BSP_LIST.exists():
        return set()
    repos = set()
    for line in BSP_LIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        repos.add(line)
    return repos


def installation_repositories():
    """列出 App 安装覆盖的全部仓库，用于判断目标是否在安装范围。"""
    repos = set()
    page = 1
    while True:
        data = call("GET", f"/installation/repositories?per_page=100&page={page}")
        for repo in data.get("repositories", []):
            repos.add(repo["full_name"])
        if len(data.get("repositories", [])) < 100:
            return repos
        page += 1


def encrypt(public_key, secret_value):
    from nacl import encoding, public

    key = public.PublicKey(public_key.encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(key).encrypt(secret_value.encode())
    return base64.b64encode(sealed).decode()


def main():
    if not VALUE:
        raise SystemExit("调用仓库缺少 WDR_MODULES_READ_TOKEN，无法分发。")

    targets = index_repositories() | bsp_repositories() | EXTRA
    installed = installation_repositories()
    print(f"目标仓库 {len(targets)} 个，App 安装覆盖 {len(installed)} 个")

    updated = skipped = failed = 0
    for full_name in sorted(targets):
        if full_name not in installed:
            print(f"SKIP {full_name}: 不在 App 安装范围")
            skipped += 1
            continue
        try:
            key = call("GET", f"/repos/{full_name}/actions/secrets/public-key")
            if DRY_RUN:
                print(f"DRY  {full_name}")
                updated += 1
                continue
            call(
                "PUT",
                f"/repos/{full_name}/actions/secrets/{SECRET_NAME}",
                {"encrypted_value": encrypt(key["key"], VALUE), "key_id": key["key_id"]},
            )
            print(f"OK   {full_name}")
            updated += 1
        except urllib.error.HTTPError as error:
            # 权限不足或已被组织策略限制的仓库逐个报告，不中断整批同步。
            print(f"FAIL {full_name}: HTTP {error.code} {error.reason}")
            failed += 1

    print(f"完成：更新 {updated}，跳过 {skipped}，失败 {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
