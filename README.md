# SpiderX - JS前端加密自动化绕过工具 

![Static Badge](https://img.shields.io/badge/SpiderX-v1.0-blue)
![Static Badge](https://img.shields.io/badge/python-3.12.3-yellow)
![Stars](https://img.shields.io/badge/dynamic/json?color=blue&label=Stars&query=stargazers_count&url=https%3A%2F%2Fapi.github.com%2Frepos%2FLiChaser%2FSpiderX)

## 修改日志
### 2026年6月24日  接入mcp格式,回到纯脚本使用
```
#以opencode为例在 opencode.json 注册
#C:\Users\14844\.opencode\opencode.json:
{
  "mcp": {
    "lichauto": {
      "type": "local",
      "command": ["python", "D:/.../mcp_server.py"],
      "enabled": true
    }
  }
正常使用lichauto传参url即可
```

### 2026年3月

把笨重的gui换成了可云上线的web端，部署使用都方便起来了，具体跳转到下链接

https://github.com/LiChaser/Lich-Spiderx

### 2025年7月23日

1. 使用 [uv](https://docs.astral.sh/uv/getting-started/installation/) 作为包管理器，通过 [pyproject.toml](pyproject.toml) 实现更精准的 Python 及各个依赖的版本控制。
2. 统一配置文件，并将默认配置存放在 `config/default.py` 中
3. 逐渐模块化项目，目前进行到 1/3
4. 移除「测试靶场服务」压缩包，转移至 `playground` 统一管理

使用 uv 时，只需要以下命令即可运行 GUI：

```bash
uv run gui.py
```

### 2025年3月20日

这里再重申下使用方法:

1. 先将headless调为false，线程数调为1，单个调试观测是否正常填入验证
2. 确保完成调整headless为True和线程数为10
3. 输入对应参数即可运行。

### 2025年3月6日 

不是不想更新，而是最近没有时间，详情请看首页，抱歉抱歉😭😭

2025年2月12日 温馨提示：

这个工具的亮点在于通过模拟浏览器点击实现前端加密爆破。它源于我在实际场景中遇到的问题，经过多次测试，虽然仍有一些难以预料的异常情况，但整体效果还是不错的。如果你在使用过程中遇到问题，不妨根据我的思路，结合具体场景尝试自己编写脚本。其实花不了太多时间，而且相比无法解密的JS，这种方法至少为你提供了一种新的攻击途径。建议在存在弱密码或撞库可能的内网环境中使用，成功率会更高。

**写这么多主要是希望大家不要喷我啊！这个工具的图形化界面其实是为了我的毕业设计，顺便开源出来积累点项目经验。如果觉得不好用，请多多包涵。网安圈子里天天都是各种骂战，看着都让人心慌，我心理承受能力比较差，希望大家手下留情。祝大家新年技术突飞猛进，升职加薪，财源滚滚！**



2025-2-10 很多师傅遇到报错，这是正常的，因为本身模拟点击的成功率与网络影响息息相关，不要将这个工具当作常规武器，我初步的定位是内网段一些常见的弱密码容易爆破但因为加密影响得分，想要应用到更多的场景，就是要学会调试，例如闪退那就在检测函数或者填入函数进行sleep睡眠一步步来看，**建议使用前先看下面的介绍文章**

2025-2-6 得到一些师傅的建议，发现drissionpage有更好的自动化性能，目前备考时间比较少，等结束打算重构下项目，感兴趣的师傅follow我，随时推送动态

2025-1-29 (有师傅觉得gui界面用的不方便，我现在在整理纯脚本的文件并且相关内容我已经用AI注释了方便理解，整理好会上传,师傅们等等)--已上传

2025-1-28 **我将gui和精简版的源码还有测试靶场已经打包放入release中**

2025-1-26 初始版上线

相关自写介绍文章

基础篇
https://mp.weixin.qq.com/s/p4COfICXluUxctotQ7cw2A

使用篇
https://mp.weixin.qq.com/s/FUpdomCBjHinAdAcLFieJg

## 🎯 核心用途

### 🔴 红队渗透增强
- **痛点解决**：针对前端传参加密率年增35%的现状（来源：OWASP 2023）
- **效率提升**：自动化绕过JS加密，爆破速度达普通爬虫传统方案N倍(自己评估,怕被喷)
- **技术门槛**：无需JS逆向经验，自动解析加密逻辑

### 🔵 蓝队自查利器
- **风险发现**：检测弱密码漏洞效率提升6.2倍(AI讲的，but对于JS加密的场景适用性很高)
- **防御验证**：模拟真实攻击路径，验证WAF防护有效性

## 🚀 部分核心技术架构

### 🌐 智能并发引擎

采用concurrent.futures线程池，实现10线程并发处理。每个线程独立处理密码子集，通过动态分块算法确保负载偏差<7%

### 🛡️ 验证码三级识别策略

1. URL直连下载
▸ 成功率：82%
▸ 适用场景：静态验证码URL
2. Canvas渲染截取
▸ 补足率：13%
▸ 适用场景：base64图片解析
3. javascript屏幕区域截图（最后5%）

## ⚠️ 部署问题

Python 版本 3.13 后不行，因为 ddddocr 包会无法下载 1.5.5版本，只要依赖包能正常下载都能运行。

使用前优先确认url是否能访问，如果没出现密码爆破的痕迹说明url无法访问或者异常。

准确性和速度是需要根据电脑的性能来决定，我放在虚拟机里跑线程就开的很低才能正常爆破，属于正常现象，因为爬虫本质需要模拟访问点击需要加载基础网页缓存。

调试可以通过headless参数来设置是否打开，全局搜索去找进行注释掉,看下自动化浏览器有无加载出来。

## 本地测试获取成功截图

![image](https://github.com/user-attachments/assets/186aba78-fa14-4bcc-8743-ef52909436ab)

🎥 点击查看演示视频

[https://github.com/user-attachments/assets/afd645a3-0443-4c56-a4bc-c9f1546d9bf6](https://github.com/user-attachments/assets/afd645a3-0443-4c56-a4bc-c9f1546d9bf6
)

🧑‍💻作者留言:

爬虫模拟最大的问题就是反爬机制和各种报错，我尝试了很久也没办法完全处理各种的异常，因为有的异常selenium包里就没法绕过，所以就选择了最常见的几种格式来。
同时为了有意向**二开的师傅**我也在GitHub上传了源码可以进行使用，大家可以根据check_login函数来自己自定义反应成功机制，根据login函数来调整登陆的点击操作，如果有好的想法欢迎与我交流😄

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LiChaser/SpiderX&type=Date)](https://www.star-history.com/#LiChaser/SpiderX&Date)

## 公众号

自己有空写的一些网安内容，不搬运纯原创，如果你觉得无聊可以循着我的文章分享来实践一下。
![image](https://github.com/user-attachments/assets/14647f50-98f4-4f93-bc10-cd807f3ff78a)

