<template>
    <div class="operadoras-table">
        <!-- Filtros -->
        <div class="table-filters">
            <div class="filter-group">
                <label>Buscar:</label>
                <input
                    v-model="localFiltroRazaoSocial"
                    type="text"
                    placeholder="Razão social..."
                    @input="onFiltroChange"
                />
            </div>

            <div class="filter-group">
                <label>UF:</label>
                <select v-model="localFiltroUF" @change="onFiltroChange">
                    <option value="">Todos</option>
                    <option v-for="uf in ufsUnicas" :key="uf" :value="uf">
                        {{ uf }}
                    </option>
                </select>
            </div>

            <div class="filter-group">
                <label>Modalidade:</label>
                <input
                    v-model="localFiltroModalidade"
                    type="text"
                    placeholder="Modalidade..."
                    @input="onFiltroChange"
                />
            </div>
        </div>

        <!-- Tabela -->
        <div class="table-container" ref="tableContainer" @scroll="onScroll">
            <table class="table">
                <thead class="table-header">
                    <tr>
                        <th @click="sortBy('razao_social')" class="sortable">
                            Razão Social
                            <span
                                v-if="sortField === 'razao_social'"
                                class="sort-icon"
                            >
                                {{ sortOrder === "asc" ? "↑" : "↓" }}
                            </span>
                        </th>
                        <th>CNPJ</th>
                        <th @click="sortBy('uf')" class="sortable">
                            UF
                            <span v-if="sortField === 'uf'" class="sort-icon">
                                {{ sortOrder === "asc" ? "↑" : "↓" }}
                            </span>
                        </th>
                        <th>Modalidade</th>
                        <th>Cidade</th>
                        <th>Ações</th>
                    </tr>
                </thead>

                <tbody class="table-body">
                    <!-- Linhas visíveis apenas -->
                    <tr
                        v-for="operadora in linhasVisiveis"
                        :key="operadora.cnpj"
                        :class="{ selected: operadora.cnpj === selectedId }"
                        @click="selectOperadora(operadora)"
                    >
                        <td>{{ operadora.razao_social }}</td>
                        <td>{{ formatCNPJ(operadora.cnpj) }}</td>
                        <td>
                            <span
                                class="uf-badge"
                                :style="getUFStyle(operadora.uf)"
                            >
                                {{ operadora.uf }}
                            </span>
                        </td>
                        <td>{{ operadora.modalidade || "-" }}</td>
                        <td>{{ operadora.cidade || "-" }}</td>
                        <td>
                            <button
                                class="btn-detalhes"
                                @click.stop="verDetalhes(operadora)"
                            >
                                Detalhes
                            </button>
                        </td>
                    </tr>

                    <!-- Placeholder para altura total -->
                    <tr
                        v-if="operadoras.length > linhasVisiveis.length"
                        style="height: 0"
                    >
                        <td :colspan="6" style="padding: 0; border: none">
                            <div
                                :style="{
                                    height: `${alturaTotal - alturaVisivel}px`,
                                }"
                            ></div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Controles de paginação -->
        <div class="table-pagination">
            <div class="pagination-info">
                Mostrando {{ startIndex + 1 }} a
                {{ Math.min(endIndex, operadoras.length) }} de
                {{ operadoras.length }} operadoras
            </div>

            <div class="pagination-controls">
                <button
                    :disabled="!hasPrevPage"
                    @click="goToPage(filtros.page - 1)"
                    class="pagination-btn"
                >
                    ← Anterior
                </button>

                <div class="page-numbers">
                    <button
                        v-for="page in paginasVisiveis"
                        :key="page"
                        @click="goToPage(page)"
                        :class="{ active: page === filtros.page }"
                        class="page-btn"
                    >
                        {{ page }}
                    </button>
                </div>

                <button
                    :disabled="!hasNextPage"
                    @click="goToPage(filtros.page + 1)"
                    class="pagination-btn"
                >
                    Próxima →
                </button>
            </div>
        </div>

        <div v-if="loading" class="table-state loading-state">
            <LoadingSpinner />
            <p>Carregando operadoras...</p>
        </div>

        <div v-else-if="error" class="table-state error-state">
            <p>❌ {{ error }}</p>
            <button @click="recarregar" class="btn-retry">
                Tentar novamente
            </button>
        </div>

        <div
            v-else-if="operadoras.length === 0"
            class="table-state empty-state"
        >
            <p>📭 Nenhuma operadora encontrada</p>
            <button @click="limparFiltros" class="btn-clear-filters">
                Limpar filtros
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useDebounceFn } from "@/composables/useDebounce";
import LoadingSpinner from "./LoadingSpinner.vue";
import ErrorAlert from "./ErrorAlert.vue"; // Adicionei o import para ErrorAlert

const props = defineProps({
    operadoras: {
        type: Array,
        required: true,
        default: () => [],
    },
    loading: {
        type: Boolean,
        default: false,
    },
    error: {
        type: String,
        default: null,
    },
    filtros: {
        type: Object,
        required: true,
        default: () => ({
            page: 1,
            limit: 10,
            razao_social: "",
            uf: "",
            modalidade: "",
        }),
    },
    totalPages: {
        type: Number,
        default: 1,
    },
    totalItems: {
        type: Number,
        default: 0,
    },
});

const emit = defineEmits([
    "update-filters",
    "change-page",
    "select-operadora",
    "view-details",
]);

const router = useRouter();
const tableContainer = ref(null);

// State declarations
const localFiltroRazaoSocial = ref(props.filtros.razao_social);
const localFiltroUF = ref(props.filtros.uf);
const localFiltroModalidade = ref(props.filtros.modalidade);

const sortField = ref("razao_social");
const sortOrder = ref("asc");

const startIndex = ref(0);
const alturaLinha = 50; // px
const linhasBuffer = 5;
const selectedId = ref(null);

// Computed properties
const ufsUnicas = computed(() => {
    const ufs = new Set();
    props.operadoras.forEach((op) => {
        if (op.uf) ufs.add(op.uf);
    });
    return Array.from(ufs).sort();
});

const linhasVisiveisCount = computed(() => {
    if (!tableContainer.value) return 20;
    const altura = tableContainer.value.clientHeight;
    return Math.ceil(altura / alturaLinha);
});

const alturaVisivel = computed(() => linhasVisiveisCount.value * alturaLinha);
const alturaTotal = computed(() => props.operadoras.length * alturaLinha);

const endIndex = computed(() =>
    Math.min(
        startIndex.value + linhasVisiveisCount.value,
        props.operadoras.length,
    ),
);

const linhasVisiveis = computed(() => {
    let sorted = [...props.operadoras];

    // Ordenar
    if (sortField.value) {
        sorted.sort((a, b) => {
            let aVal = a[sortField.value] || "";
            let bVal = b[sortField.value] || "";

            if (typeof aVal === "string") {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (aVal < bVal) return sortOrder.value === "asc" ? -1 : 1;
            if (aVal > bVal) return sortOrder.value === "asc" ? 1 : -1;
            return 0;
        });
    }

    // Virtual scrolling: apenas linhas visíveis
    const start = Math.max(0, startIndex.value - linhasBuffer);
    const end = startIndex.value + linhasVisiveisCount.value + linhasBuffer;
    return sorted.slice(start, end);
});

const hasNextPage = computed(() => props.filtros.page < props.totalPages);
const hasPrevPage = computed(() => props.filtros.page > 1);

const paginasVisiveis = computed(() => {
    const current = props.filtros.page;
    const total = props.totalPages;
    const range = 3; // páginas mostradas ao redor da atual

    let start = Math.max(1, current - range);
    let end = Math.min(total, current + range);

    // Ajustar se estiver perto do início/fim
    if (current <= range) {
        end = Math.min(total, range * 2 + 1);
    }
    if (current >= total - range) {
        start = Math.max(1, total - range * 2);
    }

    const pages = [];
    for (let i = start; i <= end; i++) {
        pages.push(i);
    }
    return pages;
});

// Funções
const onFiltroChange = useDebounceFn(() => {
    emit("update-filters", {
        razao_social: localFiltroRazaoSocial.value,
        uf: localFiltroUF.value,
        modalidade: localFiltroModalidade.value,
        page: 1, // Resetar para primeira página
    });
}, 500);

function sortBy(field) {
    if (sortField.value === field) {
        sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
    } else {
        sortField.value = field;
        sortOrder.value = "asc";
    }
}

function onScroll() {
    if (!tableContainer.value) return;

    const scrollTop = tableContainer.value.scrollTop;
    startIndex.value = Math.floor(scrollTop / alturaLinha);
}

function goToPage(page) {
    if (page >= 1 && page <= props.totalPages) {
        emit("change-page", page);
    }
}

function selectOperadora(operadora) {
    selectedId.value = operadora.cnpj;
    emit("select-operadora", operadora);
}

function verDetalhes(operadora) {
    emit("view-details", operadora);
}

function formatCNPJ(cnpj) {
    if (!cnpj) return "";
    const clean = cnpj.replace(/\D/g, "");
    return clean.replace(
        /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
        "$1.$2.$3/$4-$5",
    );
}

function getUFStyle(uf) {
    const cores = {
        SP: "#3498db",
        RJ: "#e74c3c",
        MG: "#2ecc71",
        RS: "#f39c12",
        PR: "#9b59b6",
        SC: "#1abc9c",
        BA: "#d35400",
        DF: "#34495e",
    };

    return {
        backgroundColor: cores[uf] || "#95a5a6",
        color: "white",
    };
}

function recarregar() {
    emit("update-filters", { ...props.filtros });
}

function limparFiltros() {
    localFiltroRazaoSocial.value = "";
    localFiltroUF.value = "";
    localFiltroModalidade.value = "";
    emit("update-filters", {
        razao_social: "",
        uf: "",
        modalidade: "",
        page: 1,
    });
}

// Watch
watch(
    () => props.filtros.razao_social,
    (val) => {
        localFiltroRazaoSocial.value = val;
    },
);

watch(
    () => props.filtros.uf,
    (val) => {
        localFiltroUF.value = val;
    },
);

watch(
    () => props.filtros.modalidade,
    (val) => {
        localFiltroModalidade.value = val;
    },
);

// Lifecycle
onMounted(() => {
    if (tableContainer.value) {
        tableContainer.value.addEventListener("scroll", onScroll);
    }
});

onUnmounted(() => {
    if (tableContainer.value) {
        tableContainer.value.removeEventListener("scroll", onScroll);
    }
});
</script>

<style scoped>
.operadoras-table {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.table-filters {
    padding: 1rem;
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.filter-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.filter-group label {
    font-weight: 600;
    color: #495057;
}

.filter-group input,
.filter-group select {
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    min-width: 150px;
}

.table-container {
    max-height: 600px;
    overflow-y: auto;
}

.table {
    width: 100%;
    border-collapse: collapse;
}

.table-header {
    background: #2c3e50;
    color: white;
    position: sticky;
    top: 0;
    z-index: 10;
}

.table-header th {
    padding: 1rem;
    text-align: left;
    font-weight: 600;
    cursor: default;
}

.sortable {
    cursor: pointer;
    user-select: none;
}

.sortable:hover {
    background: #34495e;
}

.sort-icon {
    margin-left: 0.5rem;
    font-weight: bold;
}

.table-body tr {
    border-bottom: 1px solid #dee2e6;
    transition: background-color 0.2s;
}

.table-body tr:hover {
    background-color: #f8f9fa;
}

.table-body tr.selected {
    background-color: #e3f2fd;
}

.table-body td {
    padding: 1rem;
}

.uf-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
}

.btn-detalhes {
    padding: 0.5rem 1rem;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.btn-detalhes:hover {
    background: #2980b9;
}

.table-pagination {
    padding: 1rem;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.pagination-info {
    color: #6c757d;
}

.pagination-controls {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.pagination-btn {
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.page-numbers {
    display: flex;
    gap: 0.25rem;
}

.page-btn {
    min-width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.page-btn:hover {
    background: #f8f9fa;
}

.page-btn.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.table-state {
    padding: 3rem;
    text-align: center;
    color: #6c757d;
}

.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
}

.error-state {
    color: #e74c3c;
}

.empty-state {
    color: #95a5a6;
}

.btn-retry,
.btn-clear-filters {
    margin-top: 1rem;
    padding: 0.5rem 1.5rem;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.btn-retry:hover,
.btn-clear-filters:hover {
    background: #2980b9;
}
</style>
