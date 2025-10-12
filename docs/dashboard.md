## Dashboard Guide: Hacker News Analytics

This document explains the key components and charts of the main BI dashboard.

[![Dashboard Screenshot](images/dashboard_overview.png)](https://lookerstudio.google.com/s/i3d2np2Q1SU)

_Please be aware that historical data collection for this project started on August 23, 2025. As a result, lifetime metrics such as "Author Lifetime Days" are calculated based on activity observed since this date and may not represent the full history of an author on Hacker News._

### 1. Global Controls

- **Date Range Control:** Located at the top right, this control filters the entire dashboard for the selected time period (based on story creation date).

### 2. KPI Tiles (Key Performance Indicators)

These cards provide a high-level, at-a-glance summary of platform activity for the current day.

- **Total Stories:** Total unique stories posted today.
- **Active Authors:** Unique number of authors who posted a story today.
- **Avg Comments / Story:** The average number of comments on stories posted today.
- **Avg. Time to 1st Comment (Mins):** The average time in minutes it takes for a new story to receive its first comment.

### 3. Core Charts

- **Daily Activity Trends (Time Series):** This chart shows the volume of stories and active authors over the selected date range, helping to identify trends and patterns in platform activity.
- **Top 10 Domains (Bar Chart):** Ranks the most frequently submitted domains, revealing the most popular sources of news and content.

### 4. Detailed Tables

- **Top 10 Current Stories:** A leaderboard of the highest-scoring stories within the selected time period.
- **Top 10 Authors:** Ranks authors by the total score of their stories and provides additional context like their posting history (`author_lifetime_days`, `total_posts_count`).
