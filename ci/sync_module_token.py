#!/usr/bin/env python3
"""把模块只读令牌同步到组织内所有仓库的 Actions Secret。

由 GitHub App 的安装令牌驱动，因此组织内新建的仓库会自动出现在
GET /installation/repositories 的返回中，无需逐个仓库手工配置。
令牌值本身来自调用仓库的 WDR_MODULES_READ_TOKEN Secret，脚本只负责分发。
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
SECRET_NAME = "WDR_MODULES_READ_TOKEN"
ORG = os.environ.get("SYNC_ORG", "HFUT-WDR")
TOKEN = os.environ["SYNC_TOKEN"]
VALUE = os.environ.get("SYNC_VALUE", "")
DRY_RUN = os.environ.get("SYNC_DRY_RUN", "") == "1"


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


def installation_repositories():
    """列出 App 安装覆盖的全部仓库，新仓库自动包含在内。"""
    page = 1
    while True:
        data = call("GET", f"/installation/repositories?per_page=100&page={page}")
        for repo in data.get("repositories", []):
            yield repo
        if len(data.get("repositories", [])) < 100:
            return
        page += 1


def encrypt(public_key, secret_value):
    from nacl import encoding, public

    key = public.PublicKey(public_key.encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(key).encrypt(secret_value.encode())
    return base64.b64encode(sealed).decode()


def main():
    if not VALUE:
        raise SystemExit("调用仓库缺少 WDR_MODULES_READ_TOKEN，无法分发。")

    updated = skipped = failed = 0
    for repo in installation_repositories():
        full_name = repo["full_name"]
        if repo.get("archived"):
            print(f"SKIP {full_name}: 已归档")
            skipped += 1
            continue
        if not full_name.startswith(ORG + "/"):
            print(f"SKIP {full_name}: 不在 {ORG} 下")
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
