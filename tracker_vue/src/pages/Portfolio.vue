<template>
  <AppNavigation />
  <div class="portfolio-page">
    <h1>Stock Portfolio</h1>
    <div class="portfolio-insights">
      <div class="insight-card">
        <h3>Total Value</h3>
        <p>$10,000</p>
      </div>
      <div class="insight-card">
        <h3>Total Gain/Loss</h3>
        <p>+5.2%</p>
      </div>
      <div class="insight-card">
        <h3>Today's Gain/Loss</h3>
        <p>+1.8%</p>
      </div>
      <div class="insight-card">
        <h3>Top Performer</h3>
        <p>AAPL</p>
      </div>
    </div>
    <div class="portfolio-table">
      <h2>Your Holdings</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Shares</th>
            <th>Price</th>
            <th>Value</th>
            <th>Change</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>AAPL</td>
            <td>10</td>
            <td>$150</td>
            <td>$1,500</td>
            <td>+2.5%</td>
          </tr>
          <tr>
            <td>GOOGL</td>
            <td>5</td>
            <td>$200</td>
            <td>$1,000</td>
            <td>-1.2%</td>
          </tr>
          <!-- Add more rows as needed -->
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import AppNavigation from '../components/navigation.vue'
</script>

<style scoped>
.portfolio-page {
  padding: 20px;
}

.portfolio-insights {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.insight-card {
  background: #f0f0f0;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  flex: 1;
}

.portfolio-table table {
  width: 100%;
  border-collapse: collapse;
}

.portfolio-table th, .portfolio-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.portfolio-table th {
  background-color: #f2f2f2;
}
</style>
