<template>
    <div class="estatisticas-container">
        <h1 class="estatisticas-title">Estatísticas Gerais</h1>

        <LoadingSpinner v-if="store.loading" size="large" />
        <ErrorAlert
            v-else-if="store.error"
            :message="store.error"
            @dismiss="store.clearError"
        />

        <div v-else-if="store.estatisticas" class="estatisticas-content">
            <div class="stat-card">
                <h3>Total de Operadoras</h3>
                <p>{{ store.estatisticas.total_operadoras }}</p>
            </div>
            <div class="stat-card">
                <h3>Total de Despesas</h3>
                <p>
                    R$
                    {{
                        parseFloat(
                            store.estatisticas.total_despesas,
                        ).toLocaleString("pt-BR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                        })
                    }}
                </p>
            </div>
            <div class="stat-card">
                <h3>Média de Despesas</h3>
                <p>
                    R$
                    {{
                        parseFloat(
                            store.estatisticas.media_despesas,
                        ).toLocaleString("pt-BR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                        })
                    }}
                </p>
            </div>
            <div class="stat-card">
                <h3>Operadoras Ativas</h3>
                <p>{{ store.estatisticas.total_operadoras_ativas }}</p>
            </div>
            <div
                class="stat-card"
                v-if="
                    store.estatisticas.top_operadoras &&
                    store.estatisticas.top_operadoras.length > 0
                "
            >
                <h3>Operadora com Maior Despesa</h3>
                <p>
                    {{
                        store.estatisticas.top_operadoras[0].razao_social ||
                        "N/A"
                    }}
                    (R$
                    {{
                        parseFloat(
                            store.estatisticas.top_operadoras[0].total_despesas,
                        ).toLocaleString("pt-BR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                        }) || "0.00"
                    }})
                </p>
            </div>

            <!-- UF Chart -->
            <div class="chart-card">
                <h3>Despesas por UF</h3>
                <UFChart :data="ufChartData" />
            </div>
        </div>
        <p v-else>Nenhum dado de estatísticas disponível.</p>
    </div>
</template>

<script setup>
import { onMounted, computed } from "vue";
import { useOperadorasStore } from "@/stores/operadorasStore";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import ErrorAlert from "@/components/ErrorAlert.vue";
import UFChart from "@/components/UFChart.vue";

const store = useOperadorasStore();

const ufChartData = computed(() => {
    if (store.estatisticas && store.estatisticas.distribuicao_uf) {
        return store.estatisticas.distribuicao_uf;
    }
    return [];
});

onMounted(() => {
    store.fetchEstatisticas();
});
</script>

<style scoped>
.estatisticas-container {
    padding: 2rem;
    background-color: #f9f9f9;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.estatisticas-title {
    color: #2c3e50;
    margin-bottom: 2rem;
    text-align: center;
    font-size: 2.5rem;
}

.estatisticas-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
}

.stat-card {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    text-align: center;
    transition: transform 0.2s ease-in-out;
}

.stat-card:hover {
    transform: translateY(-5px);
}

.stat-card h3 {
    color: #34495e;
    font-size: 1.2rem;
    margin-bottom: 0.8rem;
}

.stat-card p {
    color: #2c3e50;
    font-size: 1.8rem;
    font-weight: bold;
}

.chart-card {
    grid-column: 1 / -1; /* Take full width */
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.chart-card h3 {
    text-align: center;
    color: #34495e;
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
}
</style>
