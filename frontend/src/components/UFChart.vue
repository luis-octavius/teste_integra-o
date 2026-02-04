<template>
  <div class="uf-chart-container">
    <canvas ref="ufChartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  }
})

const ufChartCanvas = ref(null)
let chartInstance = null

const renderChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
  }

  if (!props.data || props.data.length === 0) {
    return;
  }

  const ctx = ufChartCanvas.value.getContext('2d')
  const labels = props.data.map(item => item.uf)
  const values = props.data.map(item => parseFloat(item.total))

  chartInstance = new Chart(ctx, {
    type: 'bar', // ou 'pie', 'doughnut'
    data: {
      labels: labels,
      datasets: [{
        label: 'Total de Despesas por UF',
        data: values,
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(199, 199, 199, 0.6)',
          'rgba(83, 102, 255, 0.6)',
          'rgba(255, 99, 71, 0.6)',
          'rgba(124, 252, 0, 0.6)'
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(199, 199, 199, 1)',
          'rgba(83, 102, 255, 1)',
          'rgba(255, 99, 71, 1)',
          'rgba(124, 252, 0, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Total de Despesas (R$)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'UF'
          }
        }
      },
      plugins: {
        legend: {
          display: false // Não mostrar legenda para um único dataset
        },
        title: {
          display: false,
          text: 'Distribuição de Despesas por UF'
        }
      }
    }
  })
}

onMounted(() => {
  renderChart()
})

watch(() => props.data, () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.uf-chart-container {
  position: relative;
  height: 400px; /* Altura fixa para o gráfico */
  width: 100%;
  margin-top: 2rem;
}
</style>