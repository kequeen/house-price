# 官方解析样本

这些文件是2026-10-03直接下载的官方HTML，用于离线回归测试，不会作为演示数据写入运行数据库。

| 文件 | 官方来源 |
|---|---|
| nbs.html | https://www.stats.gov.cn/sj/zxfb/202602/t20260213_1962617.html |
| sjz.html | https://zjj.sjz.gov.cn/plus/list.php?tid=192&y=2026-06 |
| bj.html | https://zjw.beijing.gov.cn/bjjs/fdcjy/wqht/fcsjtj/index.shtml |

国家统计局页面同时包含桌面与移动版重复表格。测试确认重复表一致才能入库；分档表不会被当成总指数表。
