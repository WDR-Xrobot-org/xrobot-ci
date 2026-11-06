# WDR XRobot CI 与模块源

本仓库为HFUT-WDR私有模块提供统一索引和组织内共享CI。模块/框架私有仓库继承组织成员的读取权限；不公开代码。

- `index.yaml`：18个组织自维护模块的仓库地址。
- `.github/workflows/module-ci.yml`：Linux上解析依赖、生成仅编译不运行的构造调用，编译模块与依赖。
- `.github/workflows/bsp-stm32-ci.yml`：检查生成文件、配置格式和锁文件，按BSP预设构建并提供固件产物。
- `ci/credential_helper.py`：仅为HFUT-WDR的HTTPS Git请求读取CI Secret；不将凭据写入配置或日志。

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

在每个模块仓库及BSP仓库配置`WDR_MODULES_READ_TOKEN`。使用资源所有者为HFUT-WDR的专用Fine-grained Token，只选择本次20个仓库，赋予Contents Read-only；Metadata保持GitHub要求的Read-only。不要复用个人广泛读写令牌。

框架中的`tools/configure_wdr_ci.py`可隐藏输入一次并加密写入19个调用仓库的Actions Secrets；`--check`只检查Secret名称，不读取值。不要把Token提交到仓库或发到聊天中。

共享工作流仓库的Settings→Actions→General→Access需允许组织内私有仓库访问。普通GITHUB_TOKEN仅访问当前仓库，不能代替跨模块读取凭据。

## 验证范围

模块CI编译构造调用但不执行，不启用电机；BSP构建不等价于烧录、通信或机构闭环验证。原车模式差异和硬件边界由框架文档记录。
