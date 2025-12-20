ER 图（PlantUML）说明

文件：`docs/er_diagram.puml`

说明：此文件包含根据后端 SQLAlchemy 模型（简化版）生成的 ER 图 PlantUML 源代码。它把主要实体（用户、商品、交易、同步与冲突）及其常见外键关系列出，便于在 PPT 中作为架构说明使用。

如何渲染：

1) 使用 PlantUML 在线渲染器：
   - 打开 https://www.plantuml.com/plantuml/ ，把 `er_diagram.puml` 的内容粘贴到编辑器中，点击渲染并下载图片。

2) 在本地使用 plantuml.jar（需要 Java）：

```bash
# 下载 plantuml.jar（若未安装）
wget https://downloads.sourceforge.net/project/plantuml/plantuml.jar -O plantuml.jar
# 渲染为 svg：
java -jar plantuml.jar -tsvg docs/er_diagram.puml
# 渲染为 png：
java -jar plantuml.jar -tpng docs/er_diagram.puml
```

3) 推荐在 PPT 中使用 SVG（矢量图）以保持缩放质量。

注意：
- 当前 puml 是对 models 的简化抽象，未列出所有字段（仅保留主键与关键外键/字段）。如果你需要把每张表的全部字段列出，我可以把更多字段自动提取并生成更详细的 puml 版本。

下一步可选：
- 我可以：
  - A) 生成更详细的 ER 图（包含每个模型的所有列与类型），
  - B) 把 SVG 渲染结果添加到仓库 `docs/er_diagram.svg`（需可用 PlantUML 环境），或
  - C) 把 ER 图内嵌到一个 PPT 段落（PNG/SVG 与一句解说）。
