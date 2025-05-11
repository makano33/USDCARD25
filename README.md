# Paga 服务平台

## 项目简介

Paga 服务平台是一个用于管理 Paga 账户的工具，提供包括开通美元卡和为美元卡充值等功能。该项目使用 FastAPI 作为后端框架，并提供简洁的前端界面使用户能够轻松地管理他们的 Paga 账户。

## 功能特点

- **强制开通美元卡**: 帮助用户开通 Paga 美元卡，实现美元交易需求
- **美元卡充值**: 为 Paga 美元卡充值，保持资金充足

## 安装与设置

1. 克隆仓库
```bash
git clone https://github.com/FMPASS/paga.git
cd paga
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
python paga.py
```

应用将在 `http://localhost:8000` 启动

## 项目结构

```
paga/
├── paga.py           # FastAPI 后端应用
├── paga/             # 静态文件目录
│   ├── index.html    # 主页面
│   ├── card.html     # 开通美元卡页面
│   └── fundCard.html # 充值美元卡页面
└── README.md         # 项目说明文档
```

## 使用说明

1. 打开浏览器访问 `http://localhost:8000`
2. 根据界面提示选择需要的服务：
   - 强制开美元卡
   - 充值美元卡
3. 按照页面指引输入相关信息
4. 提交表单后等待操作完成

## 注意事项

- 本工具仅供学习和研究使用
- 使用前请确保账户至少有3600奈，并确保手机号已经换绑
- 本功能不记录账户信息，使用完可自行修改密码
- 所有操作需要自担风险

## 免责声明

本项目仅作为技术研究和学习目的提供，使用者需遵守当地法律法规并自行承担使用风险。项目开发者不承担因使用本工具而产生的任何直接或间接责任。

## 许可证

[MIT License](https://opensource.org/licenses/MIT)
