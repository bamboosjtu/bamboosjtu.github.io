# akshare 包

[AKShare](https://akshare.akfamily.xyz/) 是开源的 Python 财经数据接口库，聚合了东财、新浪、同花顺等公开渠道的数据。它的价值不在"数据质量最高"，而在零门槛覆盖面广——适合作为个人研究的数据底座。本文按**投资研究的逻辑**（而不是按数据源）组织它的接口体系。

## 一、按研究流程组织接口

按"从选股到择时再到风险监控"的实操顺序，接口可以归纳为八类：

```text
定义股票池 → 观察价格估值 → 研究基本面 → 识别公司事件
→ 分析行业环境 → 关注新股 → 观察资金行为 → 阅读研报与情绪
```

### 1. 股票池与主数据（universe）

回答：市场里有哪些股票，这只股票属于什么范围？

- A 股列表 `stock_info_a_code_name`、沪深京各交易所名单 `stock_info_sh_name_code`
- 终止/暂停上市 `stock_info_sz_delist`、曾用名变动 `stock_info_change_name`

### 2. 行情与估值（market）

回答：现在多少钱，过去怎么走，目前贵不贵？

- 市场总貌：`stock_sse_summary`、`stock_szse_summary`
- 行情报价：实时行情 `stock_zh_a_spot_em`、历史日线 `stock_zh_a_hist`、分时逐笔 `stock_intraday_em`
- 估值数据：`stock_value_em`、百度估值指标 `stock_zh_valuation_baidu`
- 交易状态：停复牌 `stock_tfp_em`

### 3. 公司与财务基本面（fundamentals）

回答：公司做什么业务，赚了多少钱，财务质量怎么样？

- 三大报表：资产负债表 `stock_zcfz_em`、利润表 `stock_lrb_em`、现金流量表 `stock_xjll_em`
- 分析指标：杜邦对比 `stock_zh_dupont_comparison_em`、财务指标 `stock_financial_analysis_indicator_em`
- 业务画像：主营介绍 `stock_zyjs_ths`、主营构成 `stock_zygc_em`；另有股东持仓、盈利预测、商誉、ESG

### 4. 公司行为与股权事件（corporate_events）

回答：哪些事件会改变股东权益、股本结构或控制关系？

- 分红派息：`stock_fhps_em`、历史分红 `stock_dividend_cninfo`——**攒股收息研究的核心数据**
- 股本变动：限售解禁 `stock_restricted_release_detail_em`、增发 `stock_qbzf_em`、配股 `stock_pg_em`、回购 `stock_repurchase_em`
- 股权治理：董监高持股变动 `stock_hold_management_detail_em`、股权质押比例 `stock_gpzy_pledge_ratio_em`、一致行动人 `stock_yzxdr_em`

### 5. 行业、概念与市场结构（sector）

回答：市场当前由哪些行业和概念驱动，整体强弱如何？

- 板块行情：行业/概念板块 `stock_board_industry_name_em`、板块指数 `stock_board_concept_hist_em`
- 行业属性：行业 PE `stock_industry_pe_ratio_cninfo`、板块成分 `stock_board_concept_cons_em`
- 市场宽度：创新高新低统计 `stock_a_high_low_statistics`、破净统计 `stock_a_below_net_asset_statistics`

### 6. 一级市场 IPO（primary_market)

审核流程（`stock_register_all_em`）、申报信息、发行详情（`stock_ipo_info`）、申购中签（`stock_xgsglb_em`）、首日表现。

### 7. 资金与交易行为（flows_events）

回答：哪些资金正在买卖，交易行为有没有异常？

- 资金流：个股/行业资金流排名 `stock_individual_fund_flow_rank`、沪深港通持股 `stock_hsgt_hold_stock_em`
- 博弈行为：龙虎榜 `stock_lhb_detail_em`、筹码分布 `stock_cyq_em`
- 交易异动：盘口异动 `stock_changes_em`、大宗交易明细 `stock_dzjy_mrmx`

### 8. 研报、公告与市场情绪（research_sentiment）

回答：市场如何理解公司，关注度和情绪怎样？

- 定性分析：个股研报 `stock_research_report_em`、分析师排名 `stock_analyst_rank_em`
- 资讯评价：个股新闻 `stock_news_em`、千股千评 `stock_comment_em`、机构调研 `stock_jgdy_tj_em`
- 市场情绪：涨跌投票 `stock_zh_vote_baidu`、热门关键词/热度 `stock_hot_keyword_em`、赚钱效应 `stock_market_activity_legu`

## 二、使用注意

一个容易踩的坑：**复权口径**。回测分红再投资策略应使用不复权价格加独立分红事件；若改用前复权价格，必须防止把现金分红重复计入收益。

- **接口易变**：上游页面改版会导致接口失效，升级 akshare 后关键接口要重新验证；
- **风控面共享**：高频调用东财系接口会触发限流，重要管线应有备份源与退避逻辑；
- **建立体检习惯**：定期用固定脚本检查核心接口的可用性与字段一致性（"健康快照 + 差异报告"），不要假设昨天的结果今天仍然成立。
