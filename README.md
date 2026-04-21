# 医学伦理学 Streamlit 复习平台

基于两份本地 DOCX 题库构建的 Streamlit 课程复习平台，支持：

- 邀请码 + 昵称进入
- 错题本沉淀与 DOCX 导出
- 当前进度与定位保存
- 题号跳转、导航矩阵、来源/章节/题型筛选
- 使用 Supabase 做云端进度与错题同步

## 项目结构

- `app.py`：首页与登录入口
- `pages/1_刷题.py`：主刷题页
- `pages/2_错题本.py`：错题本与 DOCX 导出
- `pages/3_进度.py`：进度统计页
- `scripts/build_question_bank.py`：从两份 DOCX 生成结构化 JSON
- `scripts/validate_question_bank.py`：校验 JSON 数量与字段完整性
- `scripts/smoke_test_streamlit.py`：本地 Playwright 冒烟脚本
- `data/question_bank.json`：结构化题库
- `supabase/schema.sql`：Supabase 建表脚本

## 本地运行

1. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

2. 生成题库 JSON

```powershell
python .\scripts\build_question_bank.py
python .\scripts\validate_question_bank.py
```

3. 启动应用

```powershell
streamlit run .\app.py
```

如果你还没有配置 `.streamlit/secrets.toml`，应用会自动进入本地演示模式：

- 本地演示邀请码：`DEMO`
- 进度只保存在当前 Streamlit 会话

## Supabase 配置

1. 在 Supabase 新建项目。
2. 在 SQL Editor 中执行 `supabase/schema.sql`。
3. 在本地或 Streamlit Cloud 的 secrets 中配置：

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_SERVICE_KEY = "your-service-role-key"
APP_INVITE_CODE = "你的统一邀请码"
```

本地可放到 `.streamlit/secrets.toml`。

## GitHub 推送

因为当前目录还不是 Git 仓库，可以按下面步骤初始化：

```powershell
git init
git add .
git commit -m "feat: build ethics revision platform"
git branch -M main
git remote add origin <你的仓库地址>
git push -u origin main
```

## Streamlit Community Cloud 部署

1. 把仓库推到 GitHub。
2. 打开 Streamlit Community Cloud 并连接 GitHub 仓库。
3. 选择主文件：`app.py`
4. 在应用 secrets 中填入：
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `APP_INVITE_CODE`
5. 部署完成后，把统一邀请码发给朋友即可。

## 本地验收建议

先看解析：

```powershell
python .\scripts\build_question_bank.py
python .\scripts\validate_question_bank.py
```

再做网页冒烟：

```powershell
python .\skills\webapp-testing\scripts\with_server.py --help
python .\skills\webapp-testing\scripts\with_server.py --server "streamlit run app.py --server.headless true --server.port 8501" --port 8501 -- python .\scripts\smoke_test_streamlit.py
```

## 题库说明

- 只解析：
  - `伦理章节测.docx`
  - `南京医科大学医学伦理学自测题库.docx`
- 不去重，重复题按不同来源分别保留
- 第一份 DOCX 中有 1 组“匹配题”，实现里按真实题意展开为 3 小题，所以最终 JSON 总量为 `256`，不是最初估算的 `254`
- 统一 JSON 字段：
  - `question_id`
  - `source_doc`
  - `bank_key`
  - `section_title`
  - `question_type`
  - `source_no`
  - `display_order`
  - `group_range`
  - `stem`
  - `options`
  - `answer`
