# LichAuto API - 前端自动化爆破工具

一个供AI调用的前端自动化爆破功能提取项目,支持简单/复杂登录页面的自动化爆破。

## 功能特性

- 自动识别登录页面
- 自动分类简单/复杂页面
- 简单爆破:基于Requests的表单提交
- 复杂爆破:基于Playwright的浏览器模拟
- 验证码识别:集成ddddocr进行验证码自动识别
- 内置账号密码字典

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 快速使用

### 最简单的方式

```python
from lichauto import auto_crack

result = auto_crack("http://example.com/login")
print(result)
```

### 或者使用类

```python
from lichauto import LichAuto

lich = LichAuto()

# 爆破单个URL
result = lich.run("http://example.com/login")

# 爆破多个URL
result = lich.run([
    "http://example.com/login",
    "http://test.com/admin"
])

# 获取保存的结果
results = lich.get_results()
print(results)

# 清空结果
lich.clear_results()
```

### 命令行使用

```bash
python lichauto.py http://example.com/login
```

## 工作流程

1. 接收URL输入
2. 自动判断是否为登录页面
3. 自动分类为简单/复杂模式
4. 简单模式 → 使用Requests爆破
5. 复杂模式 → 使用Playwright爆破(支持验证码)
6. 返回爆破结果

## 返回结果格式

```python
{
    "success": True,
    "classification": {
        "simple": ["http://example.com/login"],
        "complex": [],
        "unknown": []
    },
    "results": [
        {
            "url": "http://example.com/login",
            "username": "admin",
            "password": "123456",
            "timestamp": "2024-01-01T00:00:00"
        }
    ],
    "count": 1
}
```

## 项目结构

```
lichauto-api/
├── config.py           # 配置文件
├── utils.py            # 工具函数
├── classifier.py       # 资产分类模块
├── cracker_simple.py   # 简单爆破模块
├── cracker_complex.py  # 复杂爆破模块
├── lichauto.py         # 主API接口
├── example.py          # 使用示例
├── requirements.txt    # 依赖
├── README.md          # 文档
└── listdir/           # 数据目录
    ├── usernames.txt    # 用户名字典
    ├── passwords.txt    # 密码字典
    ├── url.txt
    ├── simple_list.txt
    ├── complex_list.txt
    └── unknown_list.txt
```

## 注意事项

- 本工具仅供授权安全测试使用
- 请遵守当地法律法规
- 不要对未授权的目标进行测试
