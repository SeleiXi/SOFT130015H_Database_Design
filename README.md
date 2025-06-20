# LLM问答评估系统

基于Streamlit的问答评估数据库管理系统，用于管理和评估LLM模型的问答性能。

## 功能

### 核心功能
- **用户认证**：完整的用户注册、登录、权限管理系统
- **角色权限**：支持管理员、评估员、访客三种用户角色
- **数据库管理**：快速创建所有必要的数据库表，实时查看各个表的内容
- **数据导入**：支持JSON、CSV格式数据的批量导入
- **LLM评估**：集成多种大语言模型进行问答质量评估
- **数据爬取**：爬取StackExchange数据
- **查询分析**：提供多种数据查询和统计分析功能

### 用户角色权限
- **管理员 (admin)**：所有功能权限，包括用户管理
- **评估员 (evaluator)**：数据查看、LLM评估、数据导入权限
- **访客 (guest)**：仅基础数据查看权限

### 安全特性
- 密码加密存储（bcrypt）
- JWT令牌身份验证
- 基于角色的访问控制（RBAC）
- 会话管理和自动登出

## 安装与运行

1. 安装依赖：

```bash
conda create -n db_design python=3.12
conda activate db_design
pip install -r requirements.txt
```

**新增认证依赖**：
- `bcrypt`: 密码加密
- `PyJWT`: JWT令牌
- `streamlit-authenticator`: Streamlit认证组件


## Config

#### 方法1：环境变量（推荐）
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=db_design_pj
```

#### 方法2：.env 文件
1. 复制配置示例：
```bash
cp configs/config_example.env .env
```

2. 编辑 `.env` 文件修改你的配置


2. 配置数据库连接：
建立数据库（如database_pj）
使用环境变量或创建 `.env` 文件（参考上面的配置系统）。


4. 启动：

```bash
streamlit run ./src/app.py
```

## 首次使用设置

1. **创建管理员账户**：
   - 启动系统后，点击"管理员设置"
   - 创建默认管理员账户（用户名：admin，密码：admin123）
   - ⚠️ **重要**：登录后立即修改默认密码

2. **用户注册**：
   - 普通用户可以通过"注册"功能自行注册
   - 支持两种用户类型：评估员、访客
   - 管理员可以通过用户管理功能管理所有用户

3. **权限说明**：
   - 不同角色有不同的功能权限
   - 详细权限说明请查看 `README_AUTH.md`

## 技术栈

- Python
- Streamlit
- MySQL
- 原生SQL（无ORM）
- 原生SQL（无ORM）
- 环境变量配置管理

## 环境变量说明

### 数据库配置
- `DB_HOST`: 数据库主机地址（默认：localhost）
- `DB_USER`: 数据库用户名（默认：root）
- `DB_PASSWORD`: 数据库密码（默认：root）
- `DB_NAME`: 数据库名称（默认：db_design_pj）
- `DB_PORT`: 数据库端口（默认：3306）
- `DB_CHARSET`: 字符集（默认：utf8mb4）

### 应用配置
- `APP_DEBUG`: 调试模式（默认：False）
- `STREAMLIT_PORT`: Streamlit端口（默认：8501）
- `STREAMLIT_HOST`: Streamlit主机（默认：localhost）

### 认证配置
- `JWT_SECRET`: JWT密钥（⚠️ 生产环境必须修改）
- `JWT_ALGORITHM`: JWT算法（默认：HS256）
- `JWT_EXPIRATION_HOURS`: 令牌过期时间（默认：24小时）
- `BCRYPT_ROUNDS`: 密码加密轮数（默认：12）

## 更多文档

- [认证功能详细说明](README_AUTH.md)
- [环境变量配置示例](env-example) 