## Step 7: Business Intelligence with Looker Studio

### Objective

This step brings our entire data platform to life. The objective is to build an interactive, user-friendly Business Intelligence (BI) dashboard using **[Looker Studio](https://lookerstudio.google.com/)**. This dashboard will connect directly to our curated Gold Layer in BigQuery and visualize the key business metrics we defined at the start of the project. The result is a self-service analytics tool that empowers stakeholders to explore trends and derive insights without writing a single line of SQL.

### 1. Dashboard Design & Data Source

The dashboard is designed to provide a comprehensive overview of Hacker News activity, from high-level daily metrics to detailed leaderboards.

#### Primary Data Source

The entire dashboard is powered by a single, optimized view in our BigQuery Gold dataset:

**`vw_story_analytics`**: This view is managed by dbt and provides a denormalized table joining story facts with item and user dimensions. Using a single, pre-joined view ensures fast dashboard performance and consistent logic.

#### Global Control

**Date Range Selector:** A global date range control is placed at the top of the dashboard. All charts and tables are filtered based on the selected time period, using the `created_at_date` field.

### 2. Dashboard Components Breakdown

The dashboard is organized into logical sections, each designed to answer specific business questions. All components are powered by the `vw_story_analytics` view.

#### Section 1: Key Performance Indicators (KPIs) - Scorecards

This section provides an at-a-glance summary of platform health for the selected time period.

| KPI Tile                    | Metric Calculation         | Business Question Answered                        |
| :-------------------------- | :------------------------- | :------------------------------------------------ |
| **Total Stories**           | `COUNT_DISTINCT(item_id)`  | "How much new content was created?"               |
| **Active Authors**          | `COUNT_DISTINCT(user_key)` | "How many unique users contributed?"              |
| **Avg. Comments Per Story** | `AVG(total_comments)`      | "What is the average engagement level per story?" |

#### Section 2: Trend & Source Analysis - Charts

These charts visualize activity patterns and identify popular content sources over the selected date range.

| Chart               | Type        | Dimensions        | Metrics                                                 | Purpose                                                                         |
| :------------------ | :---------- | :---------------- | :------------------------------------------------------ | :------------------------------------------------------------------------------ |
| **Activity Trends** | Time Series | `created_at_date` | `COUNT_DISTINCT(item_id)`<br>`COUNT_DISTINCT(user_key)` | Identify trends, seasonality, and spikes in content creation and user activity. |
| **Top 10 Domains**  | Bar Chart   | `story_domain`    | `COUNT(item_id)`                                        | Reveal the most frequently submitted domains and popular sources of content.    |

#### Section 3: Leaderboards - Tables

These tables rank the top-performing content and contributors, providing a deeper dive into what resonates with the community.

| Table              | Dimensions                                                   | Metrics                               | Sorting              | Purpose                                                                                    |
| :----------------- | :----------------------------------------------------------- | :------------------------------------ | :------------------- | :----------------------------------------------------------------------------------------- |
| **Top 10 Stories** | `title`<br>`user_name`                                       | `SUM(score)`<br>`SUM(total_comments)` | `score` (Descending) | Quickly identify the most viral stories to understand what content performs best.          |
| **Top 10 Authors** | `user_name`<br>`author_lifetime_days`<br>`total_posts_count` | `SUM(score)`                          | `score` (Descending) | Create a leaderboard of influential authors and provide context on their community tenure. |

### 3. Final Result

The final dashboard provides a single pane of glass for stakeholders to monitor and analyze Hacker News activity. It is designed to be performant, intuitive, and directly aligned with the key business questions we set out to answer.

![Hacker News Analytics Dashboard Overview](../images/dashboard_overview.png)

---

[← Previous: Step 6 - Gold Layer: dbt Dimensional Modeling](./06-gold-layer.md)

[Next: Step 8 - Dashboard Export & Resource Cleanup →](./08-dashboard-cleanup.md)
