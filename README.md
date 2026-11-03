# 轻商店 APK + API 安全审计靶场

纯教学用，模拟数据。**仅在隔离实验环境中运行，不要在公网或真实内部网络部署。**

## 两个预置考点
- 敏感信息泄露：已认证普通用户访问 `/api/v1/account/export`，会收到三个账户的虚构个人资料及找回码。问题是后端缺失按当前用户的过滤。
- 命令执行：`POST /api/v1/tools/diagnose` 的 `host` 参数未经安全处理拼到 shell 命令，执行发生于受限制的 Docker 容器内。详见教师答案。

除以上两处外，其他接口按正常业务逻辑实现。所有个人资料与找回码均为虚构教学数据。

## 账号
| 账号 | 密码 | 身份 |
|---|---|---|
| zhangsan | zhangsan123 | 普通用户 |
| lisi | lisi123 | 普通用户 |
| admin | admin123 | 管理员（可以查看全部订单） |

## 一、构建 Android APK（一次）

需要 JDK 17、Android SDK Platform 35、Build Tools 35.0.0、Gradle 8.9（或直接用 Android Studio 打开 `android/`）。

```bash
cd android
gradle :app:assembleDebug
cd ..
cp android/app/build/outputs/apk/debug/app-debug.apk apk/app.apk
```

如果本地没有 Android 环境，把本项目推到 GitHub，运行仓库内 `.github/workflows/build-apk.yml`，从工作流产物 `audit-lab-apk` 下载 `app-debug.apk`，放到项目的 `apk/app.apk` 即可。

**本次交付不包含已编译 APK：制作环境缺少 Android SDK，不能假称已完成可安装 APK。**

## 二、启动 API 服务

```bash
docker compose up -d --build
```

- `http://127.0.0.1:8080/`：如果 APK 已存在，则直接以附件形式下载 `audit-lab.apk`；否则返回 503 编译提示。
- `http://127.0.0.1:8080/healthz`：服务健康、APK 是否存在。

Docker 默认只监听宿主机 127.0.0.1。Android 模拟器访问宿主机时，**需要把 compose 的映射临时改成 `8080:8080`**，并使用应用默认的 `http://10.0.2.2:8080`；真机则填写宿主机局域网地址（并设置严格防火墙/隔离网络）。APK 下载首页可从电脑本地浏览器访问。

> 特别注意：不建议在公共 Wi-Fi、真实办公网或者拥有敏感服务的主机部署。容器设置非 root、只读根文件系统、权限丢弃、资源限制；这些不是可以面对不可信攻击者的完整沙箱隔离保证。

## 三、APP 功能与 API

- 登录：`POST /api/v1/auth/login`
- 当前用户：`GET /api/v1/me`
- 商品列表：`GET /api/v1/products`
- 创建订单：`POST /api/v1/orders`
- 查看订单：`GET /api/v1/orders`
- 账户数据导出：`GET /api/v1/account/export`
- 网络诊断：`POST /api/v1/tools/diagnose`

APP 首次打开可设置 API 基地址，模拟器默认 `http://10.0.2.2:8080`。

## 四、考核步骤

安装 APK → 登录、正常操作并抓包 → 使用 jadx 反编译检查 API 路径和请求 JSON → 分析后端返回的敏感字段 → 定位诊断接口参数流向并在隔离环境中完成安全的命令执行验证 → 编写修复建议。

## 五、验证

```bash
python -m pytest -q tests
```

接口测试使用本地 ASGI，不需要启动 Docker；Android 编译和安装必须在具有 Android SDK 的环境中单独完成。
