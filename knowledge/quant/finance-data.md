# 金融数据包概览

## 1. 金融数据包概览

在量化交易的 pipeline 中，数据是地基。无论回测策略还是实盘决策，第一步永远是**获取可靠的历史与实时数据**。手动从网页爬取数据不仅低效，还面临反爬、格式变动、鉴权等问题。

金融数据包（Financial Data Packages）封装了数据获取的复杂度，让你用 **几行 Python 代码** 拿到结构化的 DataFrame。本文介绍四个最具代表性的包：

| 包           | 数据市场                | 核心定位               |
| ------------ | ----------------------- | ---------------------- |
| **akshare**  | A股/期货/宏观/基金/债券 | 免费聚合器，覆盖面最广 |
| **tushare**  | A股/港股/美股/宏观/另类 | 专业标准化，Token 鉴权 |
| **ccxt**     | 加密货币（100+交易所）  | 统一交易接口，跨所套利 |
| **yfinance** | 全球股票/ETF/外汇/商品  | 轻量级，雅虎数据直达   |

---

## 2. 环境准备

```bash
pip install akshare tushare ccxt yfinance pandas matplotlib notebook
```

验证安装：

```python
import akshare as ak
import tushare as ts
import ccxt
import yfinance as yf

print(f"akshare  : {ak.__version__}")
print(f"tushare  : {ts.__version__}")
print(f"ccxt     : {ccxt.__version__}")
print(f"yfinance : {yf.__version__}")
```

---

## 3. akshare — 国内免费数据聚合器

### 3.1 设计理念

> **"一个函数，一个数据源"** —— 把国内主流财经网站（东方财富、新浪、腾讯、同花顺、巨潮资讯等）的公开数据接口封装成统一风格的 Python 函数。

akshare 的核心哲学：

- **零配置**：无需注册、Token、API Key，`pip install` 即可用
- **源头透明**：函数名直接反映数据来源（`stock_zh_a_hist` = 东方财富A股历史行情，`stock_zh_a_hist_tx` = 腾讯A股历史行情）
- **覆盖面广**：A股/港股/期货/期权/基金/债券/宏观/另类数据，几乎涵盖所有国内公开金融数据
- **时效优先**：直接调用源头 HTTP API，不做中间缓存（除非源头本身有缓存）

> **重要提醒**：东方财富对非大陆 IP 限制严格，`_em` 后缀函数可能频繁断连。建议优先使用**腾讯源**（`_tx` 后缀）和**通达信**（mootdx UDP 协议），这些源在国内网络更稳定。

```
┌──────────────────────────────────────────┐
│               akshare                     │
│  ┌──────────────────────────────────────┐ │
│  │   统一函数签名  →  DataFrame          │ │
│  └──────────────────────────────────────┘ │
│       ↑         ↑        ↑         ↑      │
│  ┌────┴───┐ ┌──┴──┐ ┌───┴───┐ ┌───┴───┐  │
│  │东方财富 │ │腾讯 │ │ 新浪  │ │通达信 │  │
│  │(HTTP)  │ │(HTTP)│ │(HTTP) │ │(UDP)  │  │
│  │⚠不稳定 │ │✅稳定│ │⚠较慢 │ │✅稳定 │  │
│  └────────┘ └────┘ └───────┘ └───────┘  │
└──────────────────────────────────────────┘
```

### 3.2 数据源稳定性说明

> **注意**：东方财富（`_em` 后缀函数）对中国大陆以外 IP 限制日益严格，频繁出现 `ConnectionError` / `RemoteDisconnected`。以下示例优先推荐**腾讯源**（`_tx` 后缀）和**通达信**（mootdx），这些源在国内网络环境下更稳定。

| 场景     | 不稳定（东财源）       | 稳定替代                          |
| -------- | ---------------------- | --------------------------------- |
| 历史日线 | `stock_zh_a_hist`      | `stock_zh_a_hist_tx`（腾讯）      |
| 实时行情 | `stock_zh_a_spot_em`   | `mootdx` 通达信 UDP 协议          |
| 指数日线 | `stock_zh_index_daily` | `stock_zh_index_daily_tx`（腾讯） |

### 3.3 核心函数速览

```python
import akshare as ak
from mootdx.quotes import Quotes

# ──── 行情类（推荐：腾讯源 + 通达信）────
# A股个股历史日K线（腾讯源，更稳定）
df = ak.stock_zh_a_hist_tx(
    symbol="sz000001",        # 深市 sz 前缀，沪市 sh 前缀
    start_date="20240101",
    end_date="20250701",
    adjust="qfq",             # 前复权
)

# A股实时行情（通达信 UDP 协议，不依赖 HTTP）
tdx = Quotes.factory(market="std")
quotes = tdx.quotes(symbol=["000001", "600519", "300750"])

# A股全市场行情快照（东财源，不稳定时降级到通达信）
# df = ak.stock_zh_a_spot_em()

# 指数历史数据（腾讯源）
df = ak.stock_zh_index_daily_tx(symbol="sz399001")  # 深证成指

# ──── 基本面类 ────
# 个股财务指标（东财源）
df = ak.stock_financial_abstract(symbol="000001")

# ──── 另类数据 ────
# 融资融券（东财源）
df = ak.stock_margin_detail_sse(date="20250630")
```

### 3.4 适用场景

- ✅ A股策略研究与回测数据准备
- ✅ 需要快速验证一个想法（"茅台历史上股息率最高是多少？"）
- ✅ 爬取东方财富/新浪/腾讯上能看到的任何公开数据
- ⚠️ 东方财富源（`_em` 后缀）可能被墙，优先用腾讯源（`_tx`）+ 通达信（mootdx）
- ❌ 需要毫秒级实时行情（这是聚合器，不是交易所直连）
- ❌ 需要完整的历史深度（比如二十年前的退市股数据）

---

## 4. tushare — 专业级金融数据平台

### 4.1 设计理念

> **"数据即服务"** —— 建立标准化的数据模型，统一 API 规范，通过 Token 机制实现分级授权。

tushare 与 akshare 的根本不同在于：**它不是爬虫，而是一个数据服务平台**。背后有独立的数据库和清洗流水线。

核心哲学：

- **标准化**：所有接口返回结构一致的 DataFrame，字段名、类型统一
- **分级授权**：基础数据免费（需注册），高频/深度数据需积分兑换
- **数据清洗**：服务端做过去重、复权校准、停牌标记等预处理
- **PRO 接口体系**：新版接口统一以 `pro_api()` 方式调用，参数通过 dict 传入

```
┌──────────────────────────────────┐
│            tushare               │
│  ┌─────────────────────────────┐ │
│  │   pro_api() 统一入口         │ │
│  │   参数 → JSON → 服务端查询   │ │
│  └─────────────────────────────┘ │
│          ↓ (Token 鉴权)          │
│  ┌─────────────────────────────┐ │
│  │      Tushare 后端数据库       │ │
│  │  (独立采集 → 清洗 → 存储)     │ │
│  └─────────────────────────────┘ │
└──────────────────────────────────┘
```

### 4.2 Token 注册

1. 访问 https://tushare.pro → 注册账号
2. 登录后 → 个人主页 → "接口TOKEN" → 复制
3. 设置 Token：

```python
import tushare as ts
ts.set_token("你的TOKEN")
pro = ts.pro_api()
```

### 4.3 核心接口速览

```python
import tushare as ts

ts.set_token("YOUR_TOKEN")
pro = ts.pro_api()

# ──── 行情类 ────
# 日线行情
df = pro.daily(ts_code="000001.SZ", start_date="20240101", end_date="20240701")

# 分钟线
df = pro.stk_mins(ts_code="000001.SZ", freq="5min")

# ──── 基本面类 ────
# 利润表 / 资产负债表 / 现金流量表
df = pro.income(ts_code="000001.SZ", period="20231231")
df = pro.balancesheet(ts_code="000001.SZ", period="20231231")
df = pro.cashflow(ts_code="000001.SZ", period="20231231")

# 财务指标（ROE/ROA/毛利率等）
df = pro.fina_indicator(ts_code="000001.SZ")

# ──── 特色数据 ────
# 沪深股通十大成交股
df = pro.hsgt_top10(trade_date="20240701")

# 龙虎榜
df = pro.top_list(trade_date="20240701")

# 限售解禁
df = pro.share_float(ts_code="000001.SZ")
```

### 4.4 适用场景

- ✅ 需要长期维护的量化系统（接口稳定性好）
- ✅ 需要三张财务报表 + 财务指标的统一数据
- ✅ 与团队协作（Token 统一管理，数据格式标准）
- ❌ 快速原型验证（注册+Token 有门槛，不如 akshare 即装即用）

---

## 5. ccxt — 加密货币交易所统一接口

### 5.1 设计理念

> **"一个 API，所有交易所"** —— 将 100+ 加密货币交易所的 REST/WebSocket API 抽象为一套统一的方法签名。

ccxt 的核心哲学：

- **统一方法名**：不管底层是 Binance 还是 OKX，`fetch_ohlcv()` 就是拿K线，`create_order()` 就是下单
- **标准化输出**：所有交易所返回的 OHLCV 数据格式完全相同，方便跨所策略
- **市场无关**：你写的套利策略可以不加修改地跑在 Binance↔OKX 之间
- **社区驱动**：新交易所、新功能的支持靠社区贡献（GitHub 60000+ Star）

```
┌──────────────────────────────────────┐
│               ccxt                   │
│  ┌────────────────────────────────┐  │
│  │   统一方法                     │  │
│  │  fetch_ohlcv()                 │  │
│  │  fetch_ticker()                │  │
│  │  create_order()     ...        │  │
│  └────────────────────────────────┘  │
│        ↓  (按 exchange id 分发)       │
│  ┌──────┐ ┌──────┐ ┌──────┐         │
│  │Binance│ │ OKX  │ │Bybit │  ...    │
│  └──────┘ └──────┘ └──────┘         │
│   (REST + WebSocket 连接池)          │
└──────────────────────────────────────┘
```

### 5.2 核心方法速览

```python
import ccxt

# 创建交易所实例
exchange = ccxt.binance({
    'enableRateLimit': True,   # 内置限流，防止被封
    'options': {'defaultType': 'spot'},  # 现货
})

# 不需要 API Key 的公开接口：
# ──── 市场数据 ────
markets = exchange.load_markets()                              # 加载所有交易对
ticker  = exchange.fetch_ticker('BTC/USDT')                    # 实时行情
ohlcv   = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=100)   # K线
orderbook = exchange.fetch_order_book('BTC/USDT', limit=20)   # 订单簿深度
trades  = exchange.fetch_trades('BTC/USDT', limit=50)          # 最近成交
```

### 5.3 适用场景

- ✅ 加密货币量化交易（现货/合约）
- ✅ 跨交易所套利（"搬砖"）
- ✅ 做市策略开发
- ❌ 传统股票/期货市场（ccxt 专注加密货币）

---

## 6. yfinance — 雅虎财经全球市场数据

### 6.1 设计理念

> **"极简即用"** —— 用 `yf.download()` 一行代码拿到全球任何市场的历史数据。

yfinance 的设计极简到了极致：

- **一行下载**：`yf.download('AAPL')` 即可获取苹果全部历史
- **全球化**：覆盖美股/港股/A股/外汇/期货/ETF/指数/加密货币
- **零配置**：无需 API Key，直接访问雅虎财经公开接口
- **Ticker 对象模型**：每个标的物是一个对象，`.history()` `.info` `.dividends` 方法自然派生

```
┌──────────────────────────────┐
│          yfinance             │
│  ┌─────────────────────────┐ │
│  │  Ticker("AAPL")          │ │
│  │   .history()  → K线      │ │
│  │   .info       → 基本面   │ │
│  │   .dividends  → 分红     │ │
│  │   .financials → 财报     │ │
│  └─────────────────────────┘ │
│             ↓                 │
│  ┌─────────────────────────┐ │
│  │    Yahoo Finance API      │ │
│  │  (全球市场，免费公开)     │ │
│  └─────────────────────────┘ │
└──────────────────────────────┘
```

### 6.2 Ticker 对象详解

```python
import yfinance as yf

# 创建 Ticker 对象
aapl = yf.Ticker("AAPL")

# 基本信息（市值/PE/行业/描述等，一个 dict 包含上百个字段）
info = aapl.info
print(info.get("marketCap"), info.get("trailingPE"), info.get("sector"))

# 历史K线
hist = aapl.history(period="1y")           # 最近1年
hist = aapl.history(start="2020-01-01")    # 指定起始日
hist = aapl.history(period="5d", interval="1h")  # 小时线

# 分红与拆股
print(aapl.dividends.tail(10))   # 历史分红
print(aapl.splits)               # 历史拆股

# 财务报表
print(aapl.financials)           # 年度利润表
print(aapl.balance_sheet)        # 资产负债表
print(aapl.cashflow)             # 现金流量表

# 多标的同时下载
df = yf.download(["AAPL", "GOOGL", "MSFT"], start="2024-01-01")
```

### 6.3 适用场景

- ✅ 全球市场（特别是美股）的历史数据获取
- ✅ 快速查看一只股票的基本面（`.info` 非常丰富）
- ✅ 投资组合分析（多标的批量下载）
- ❌ 需要 A 股 Level-2 盘口/逐笔成交（yfinance 不支持）
- ❌ 中国大陆网络环境不稳定时（可能需要代理）

---

## 7. 四包设计理念对比

| 维度         | akshare               | tushare              | ccxt                   | yfinance               |
| ------------ | --------------------- | -------------------- | ---------------------- | ---------------------- |
| **设计模式** | 函数式聚合器          | 服务化数据平台       | 交易所适配器           | 对象化数据下载器       |
| **核心抽象** | 一个函数 = 一个数据源 | pro_api + 统一参数   | exchange.fetch\_\*     | Ticker 对象            |
| **鉴权方式** | 零鉴权                | Token 分级           | 可选 API Key           | 零鉴权                 |
| **数据市场** | A股/期货/宏观/基金    | A股/港股/美股/宏观   | 加密货币               | 全球股票/ETF/外汇      |
| **数据来源** | 爬取公开网站          | 自有数据库           | 交易所 API 直连        | Yahoo Finance          |
| **数据深度** | 看源头能提供什么      | 标准化、深度清洗     | 看交易所提供什么       | 雅虎覆盖范围           |
| **实时性**   | 取决于源头刷新频率    | T+1（部分延迟15min） | 毫秒级（WebSocket）    | 延迟 15 分钟           |
| **稳定性**   | 源头变动可能失效      | 高（自有数据库）     | 高（交易所官方 API）   | 中（雅虎接口偶有变动） |
| **学习曲线** | 低（纯函数调用）      | 中（需注册+查文档）  | 中（需理解交易所概念） | 极低                   |
| **社区规模** | 国内量化圈主流        | 国内机构主流         | GitHub 64k+ Star       | GitHub 15k+ Star       |
