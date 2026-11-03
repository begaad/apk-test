# 教师答案（不要随 APK 发给学员）

## 1 敏感信息泄露
`GET /api/v1/account/export` 在认证后枚举全部账户，未限制为当前登录账户。使用 zhangsan 令牌也会收到 lisi、admin 的虚构 email、phone、recovery_code。
正确修复：只序列化已获授权的数据，删除 recovery_code 字段，数据层强制执行按主体的访问控制。

## 2 命令执行
`POST /api/v1/tools/diagnose` 的 `host` 被直接拼接成 `getent hosts <host>`，并以 `shell=True` 执行。用仅在容器内读取命令自身身份的测试输入 `localhost; id` 可观察注入效果。管理员不是必须的；这是供学员发现并报告的单一缺陷。
正确修复：用 `subprocess.run(["getent", "hosts", host], shell=False, ...)`，并在解析后严格验证主机名/IP，不拼接 shell。

不要赋予容器对宿主机文件、容器管理套接字或内网生产网段的访问权限。
