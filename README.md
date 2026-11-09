# WDR XRobot CI 与模块源

本仓库为HFUT-WDR私有模块提供统一索引和组织内共享CI。模块/框架私有仓库继承组织成员的读取权限；不公开代码。

- `index.yaml`：17个组织自维护模块的仓库地址。
- `.github/workflows/module-ci.yml`：Linux上解析依赖、生成仅编译不运行的构造调用，编译模块与依赖。
- `.github/workflows/bsp-stm32-ci.yml`：检查生成文件、配置格式和锁文件，按BSP预设构建并提供固件产物。
- `.github/workflows/sync-module-token.yml`：用组织 GitHub App 的安装令牌，把 `WDR_MODULES_READ_TOKEN` 分发到组织内所有仓库；新建仓库自动纳入下一次同步，无需逐个手工配置。
- `ci/credential_helper.py`：仅为HFUT-WDR的HTTPS Git请求读取CI Secret；不将凭据写入配置或日志。

## 组织令牌同步

`WDR_MODULES_READ_TOKEN` 是仓库级 Secret，新建仓库默认没有，导致首次 CI 失败。同步工作流的做法：

- 组织 owner 一次性创建 GitHub App 并安装到 HFUT-WDR（All repositories），授予 `Contents: read` 与 `Secrets: write`；
- 在 `xrobot-ci` 配置 `WDR_SYNC_APP_ID`、`WDR_SYNC_APP_PRIVATE_KEY`（App 私钥）和 `WDR_MODULES_READ_TOKEN`（要分发的值）；
- 手动运行或每日定时触发，脚本遍历 App 安装覆盖的仓库并写入 Secret。

App 安装到组织后，新建仓库自动出现在安装范围内，下一次同步即可通过 CI；也可手动 dispatch 立即同步。同步脚本只写入 `.github/workflows/*.yml` 中引用了 `HFUT-WDR/xrobot-ci` 或显式使用 `WDR_MODULES_READ_TOKEN` 的仓库，非 XRobot 仓库不会被写入；未匹配但确实需要的仓库可用 `extra_repos` 输入补充。未通过 `--dry_run` 前建议先空跑核对仓库列表。

工作流依据xrobot-org/XRobot的v1共享工作流维护，原始来源：
https://github.com/xrobot-org/XRobot/tree/v1/.github/workflows
保留其Apache-2.0许可证；WDR的修改包括组织模块索引和跨私有仓库只读认证。

## 调用

模块仓库的`.github/workflows/build.yml`调用：

```yaml
jobs:
  build:
    uses: HFUT-WDR/xrobot-ci/.github/workflows/module-ci.yml@dev
    secrets:
      WDR_MODULES_READ_TOKEN: ${{ secrets.WDR_MODULES_READ_TOKEN }}
```

BSP调用同目录的`bsp-stm32-ci.yml@dev`，填写工程名、产品配置和Debug/Release预设。
开发分支为dev；master/tag仅用于有意发布，不以首次上传代替发布。

## 私有依赖凭据

在每个模块仓库及BSP仓库配置`WDR_MODULES_READ_TOKEN`。使用资源所有者为HFUT-WDR的专用Fine-grained Token，只选择当前19个仓库，赋予Contents Read-only；Metadata保持GitHub要求的Read-only。不要复用个人广泛读写令牌。

框架中的`tools/configure_wdr_ci.py`可隐藏输入一次并加密写入18个调用仓库的Actions Secrets；`--check`只检查Secret名称，不读取值。不要把Token提交到仓库或发到聊天中。

共享工作流仓库的Settings→Actions→General→Access需允许组织内私有仓库访问。普通GITHUB_TOKEN仅访问当前仓库，不能代替跨模块读取凭据。

## 验证范围

模块CI编译构造调用但不执行，不启用电机；BSP构建不等价于烧录、通信或机构闭环验证。原车模式差异和硬件边界由框架文档记录。

DualYaw与Pitch已合入Gimbal内部组件；DualYaw仓库保留历史，Pitch仓库已删除；当前索引不再将两轴作为独立模块分发。
