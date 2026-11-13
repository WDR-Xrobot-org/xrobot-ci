# WDR XRobot CI 与模块源

本仓库为WDR-Xrobot-org私有模块提供统一索引和组织内共享CI。模块/框架私有仓库继承组织成员的读取权限；不公开代码。

- `index.yaml`：19 个组织自维护模块的仓库地址。
- `.github/workflows/module-ci.yml`：Linux上解析依赖、生成仅编译不运行的构造调用，编译模块与依赖。
- `.github/workflows/bsp-stm32-ci.yml`：检查生成文件、配置格式和锁文件，按BSP预设构建并提供固件产物。

## 调用

模块仓库的`.github/workflows/build.yml`调用：

```yaml
jobs:
  build:
    uses: WDR-Xrobot-org/xrobot-ci/.github/workflows/module-ci.yml@dev
    secrets:
      WDR_APP_PRIVATE_KEY: ${{ secrets.WDR_APP_PRIVATE_KEY }}
```

BSP调用同目录的`bsp-stm32-ci.yml@dev`，填写工程名、产品配置和Debug/Release预设。
开发分支为dev；master/tag仅用于有意发布，不以首次上传代替发布。

## 私有依赖凭据

使用组织 GitHub App（`wdr-xrobot-ci`），不再使用个人访问令牌：

- App 权限：`Contents: Read-only`、`Metadata: Read-only`；
- 安装范围：组织全部仓库；
- 每次 job 由 `actions/create-github-app-token@v2` 铸造一小时有效的安装令牌，
  通过 `credential.helper` 从环境变量提供给 git，不写进配置、参数或日志。

调用方只需要仓库级 Secret `WDR_APP_PRIVATE_KEY`（App 私钥 PEM）与组织或仓库级
变量 `WDR_APP_ID`。免费组织的组织级 Secret 不能被私有仓库读取，所以私钥按仓库配置；
新增仓库时补一次 Secret 即可，令牌本身无需轮换。

