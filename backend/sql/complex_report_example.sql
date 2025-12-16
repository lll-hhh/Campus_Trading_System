-- 复杂报表示例：最近30天多表汇总
-- 目标：按分类统计成交额、订单数、平均客单价，并展示前5热销商品，同时标注是否存在冲突记录
-- 涉及：orders / order_items / items / users / conflict_records / daily_stats

WITH recent_orders AS (
    SELECT o.id, o.user_id, o.total_amount, o.status, o.created_at
    FROM orders o
    WHERE o.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
),
category_sales AS (
    SELECT i.category,
           COUNT(DISTINCT ro.id)                          AS order_count,
           SUM(oi.quantity * oi.unit_price)               AS gross_amount,
           AVG(oi.quantity * oi.unit_price)               AS avg_order_value,
           SUM(CASE WHEN cr.id IS NOT NULL THEN 1 ELSE 0 END) AS conflict_hits
    FROM recent_orders ro
    JOIN order_items oi ON oi.order_id = ro.id
    JOIN items i ON i.id = oi.item_id
    LEFT JOIN conflict_records cr
           ON cr.table_name = 'orders'
          AND cr.record_id = ro.id
    GROUP BY i.category
),
item_rank AS (
    SELECT i.id,
           i.title,
           i.category,
           SUM(oi.quantity)        AS qty_sold,
           SUM(oi.quantity*oi.unit_price) AS revenue,
           ROW_NUMBER() OVER (PARTITION BY i.category ORDER BY SUM(oi.quantity*oi.unit_price) DESC) AS rn
    FROM recent_orders ro
    JOIN order_items oi ON oi.order_id = ro.id
    JOIN items i ON i.id = oi.item_id
    GROUP BY i.id, i.title, i.category
)
SELECT cs.category,
       cs.order_count,
       cs.gross_amount,
       cs.avg_order_value,
       cs.conflict_hits,
       ir.title            AS top_item,
       ir.revenue          AS top_item_revenue,
       ds.sync_conflict_count AS conflicts_today
FROM category_sales cs
LEFT JOIN item_rank ir
       ON ir.category = cs.category AND ir.rn = 1
LEFT JOIN daily_stats ds
       ON ds.stat_date = CURRENT_DATE()
ORDER BY cs.gross_amount DESC;
