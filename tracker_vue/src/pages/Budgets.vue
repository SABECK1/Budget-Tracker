<template>
  <div class="budgets-page">
    <div class="container">
      <div class="row">
        <div class="col-12">
          <h1 class="mb-4">Budgets</h1>
          
          <!-- Add Budget Button -->
          <div class="mb-4">
            <button 
              class="btn btn-primary" 
              @click="showAddBudgetModal = true"
            >
              <i class="bi bi-plus-circle"></i> Add Budget
            </button>
          </div>

          <!-- Budgets List -->
          <div class="row">
            <div 
              v-for="budget in budgets" 
              :key="budget.id" 
              class="col-md-6 col-lg-4 mb-4"
            >
              <div class="card h-100">
                <div class="card-body">
                  <h5 class="card-title">{{ budget.name }}</h5>
                  <div class="budget-info mb-3">
                    <div class="row">
                      <div class="col-6">
                        <small class="text-muted">Period</small>
                        <div>{{ formatPeriod(budget.period) }}</div>
                      </div>
                      <div class="col-6">
                        <small class="text-muted">Limit</small>
                        <div>{{ formatCurrency(budget.limit_amount) }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Pie Chart -->
                  <div class="budget-chart mb-3">
                    <canvas 
                      :id="'budget-chart-' + budget.id" 
                      width="200" 
                      height="200"
                    ></canvas>
                  </div>
                  
                  <!-- Budget Details -->
                  <div class="budget-details">
                    <div class="row text-center">
                      <div class="col-4">
                        <div class="spent">{{ formatCurrency(budget.spent_amount) }}</div>
                        <small class="text-muted">Spent</small>
                      </div>
                      <div class="col-4">
                        <div class="remaining">{{ formatCurrency(budget.remaining_amount) }}</div>
                        <small class="text-muted">Remaining</small>
                      </div>
                      <div class="col-4">
                        <div class="percentage">{{ Math.round(budget.spent_percentage) }}%</div>
                        <small class="text-muted">Used</small>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="card-footer bg-transparent border-top-0">
                  <div class="row">
                    <div class="col-6">
                      <small class="text-muted">Period: {{ formatPeriodRange(budget) }}</small>
                    </div>
                    <div class="col-6 text-end">
                      <button 
                        class="btn btn-sm btn-outline-primary me-2"
                        @click="editBudget(budget)"
                      >
                        Edit
                      </button>
                      <button 
                        class="btn btn-sm btn-outline-danger"
                        @click="deleteBudget(budget.id)"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- No Budgets Message -->
          <div v-if="budgets.length === 0" class="text-center text-muted py-5">
            <i class="bi bi-pie-chart" style="font-size: 3rem;"></i>
            <h5 class="mt-3">No budgets yet</h5>
            <p>Create your first budget to start tracking your spending</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Budget Modal -->
    <div 
      class="modal fade" 
      :class="{ 'show': showAddBudgetModal }" 
      :style="{ display: showAddBudgetModal ? 'block' : 'none' }"
      tabindex="-1"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editingBudget ? 'Edit Budget' : 'Add Budget' }}</h5>
            <button type="button" class="btn-close" @click="showAddBudgetModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveBudget">
              <div class="mb-3">
                <label for="budgetName" class="form-label">Budget Name</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="budgetName"
                  v-model="form.name"
                  required
                >
              </div>
              
              <div class="mb-3">
                <label for="budgetLimit" class="form-label">Limit Amount</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="budgetLimit"
                  v-model.number="form.limit_amount"
                  step="0.01"
                  required
                >
              </div>
              
              <div class="mb-3">
                <label for="budgetPeriod" class="form-label">Period</label>
                <select class="form-select" id="budgetPeriod" v-model="form.period" @change="handlePeriodChange">
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              
              <div v-if="form.period === 'custom'" class="mb-3">
                <label for="customPeriodDays" class="form-label">Custom Period (days)</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="customPeriodDays"
                  v-model.number="form.custom_period_days"
                  min="1"
                  required
                >
              </div>
              
              <div class="mb-3">
                <label class="form-label">Transaction Types</label>
                <div v-if="transactionTypes.length === 0" class="text-muted">No transaction types available</div>
                <div v-else>
                  <div 
                    v-for="type in transactionTypes" 
                    :key="type.id"
                    class="form-check"
                  >
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      :id="'type-' + type.id"
                      :value="type.id"
                      v-model="form.transaction_types"
                    >
                    <label class="form-check-label" :for="'type-' + type.id">
                      {{ type.name }}
                    </label>
                  </div>
                </div>
              </div>
              
              <div class="mb-3">
                <label class="form-label">Transaction Subtypes</label>
                <div v-if="transactionSubtypes.length === 0" class="text-muted">No transaction subtypes available</div>
                <div v-else>
                  <div 
                    v-for="subtype in transactionSubtypes" 
                    :key="subtype.id"
                    class="form-check"
                  >
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      :id="'subtype-' + subtype.id"
                      :value="subtype.id"
                      v-model="form.transaction_subtypes"
                    >
                    <label class="form-check-label" :for="'subtype-' + subtype.id">
                      {{ subtype.transaction_type_name }} - {{ subtype.name }}
                    </label>
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showAddBudgetModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="saveBudget">
              {{ editingBudget ? 'Update Budget' : 'Create Budget' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Overlay for modal -->
    <div 
      v-if="showAddBudgetModal" 
      class="modal-backdrop fade show"
      @click="showAddBudgetModal = false"
    ></div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Budgets',
  data() {
    return {
      budgets: [],
      transactionTypes: [],
      transactionSubtypes: [],
      showAddBudgetModal: false,
      editingBudget: null,
      form: {
        name: '',
        limit_amount: 0,
        period: 'monthly',
        custom_period_days: null,
        transaction_types: [],
        transaction_subtypes: []
      }
    }
  },
  mounted() {
    this.fetchBudgets()
    this.fetchTransactionTypes()
    this.fetchTransactionSubtypes()
  },
  methods: {
    async fetchBudgets() {
      try {
        const response = await axios.get('/api/budgets/')
        this.budgets = response.data
        this.$nextTick(() => {
          this.budgets.forEach(budget => this.renderChart(budget))
        })
      } catch (error) {
        console.error('Error fetching budgets:', error)
      }
    },
    
    async fetchTransactionTypes() {
      try {
        const response = await axios.get('/api/transaction-types/')
        this.transactionTypes = response.data
      } catch (error) {
        console.error('Error fetching transaction types:', error)
      }
    },
    
    async fetchTransactionSubtypes() {
      try {
        const response = await axios.get('/api/transaction-subtypes/')
        this.transactionSubtypes = response.data
      } catch (error) {
        console.error('Error fetching transaction subtypes:', error)
      }
    },
    
    renderChart(budget) {
      const canvasId = `budget-chart-${budget.id}`
      const canvas = document.getElementById(canvasId)
      if (!canvas) return
      
      const ctx = canvas.getContext('2d')
      const spentPercentage = budget.spent_percentage
      const remainingPercentage = 100 - spentPercentage
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // Draw pie chart
      const centerX = canvas.width / 2
      const centerY = canvas.height / 2
      const radius = Math.min(centerX, centerY) - 10
      
      // Draw spent portion
      if (spentPercentage > 0) {
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + (spentPercentage / 100) * 2 * Math.PI)
        ctx.fillStyle = '#dc3545' // Red for spent
        ctx.fill()
      }
      
      // Draw remaining portion
      if (remainingPercentage > 0) {
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, radius, -Math.PI / 2 + (spentPercentage / 100) * 2 * Math.PI, -Math.PI / 2 + 2 * Math.PI)
        ctx.fillStyle = '#28a745' // Green for remaining
        ctx.fill()
      }
      
      // Draw center text
      ctx.fillStyle = '#000'
      ctx.font = 'bold 16px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(`${Math.round(spentPercentage)}%`, centerX, centerY)
    },
    
    formatCurrency(amount) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(amount)
    },
    
    formatPeriod(period) {
      const periodMap = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'yearly': 'Yearly',
        'custom': 'Custom'
      }
      return periodMap[period] || period
    },
    
    formatPeriodRange(budget) {
      const startDate = new Date(budget.period_start)
      const endDate = new Date(budget.period_end)
      return `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`
    },
    
    handlePeriodChange() {
      if (this.form.period !== 'custom') {
        this.form.custom_period_days = null
      }
    },
    
    editBudget(budget) {
      this.editingBudget = budget
      this.form = {
        name: budget.name,
        limit_amount: budget.limit_amount,
        period: budget.period,
        custom_period_days: budget.custom_period_days,
        transaction_types: budget.transaction_types.map(t => t.id),
        transaction_subtypes: budget.transaction_subtypes.map(s => s.id)
      }
      this.showAddBudgetModal = true
    },
    
    async saveBudget() {
      try {
        const budgetData = {
          ...this.form,
          transaction_types: this.form.transaction_types,
          transaction_subtypes: this.form.transaction_subtypes
        }
        
        if (this.editingBudget) {
          await axios.patch(`/api/budgets/${this.editingBudget.id}/`, budgetData)
        } else {
          await axios.post('/api/budgets/', budgetData)
        }
        
        this.showAddBudgetModal = false
        this.resetForm()
        this.fetchBudgets()
      } catch (error) {
        console.error('Error saving budget:', error)
      }
    },
    
    async deleteBudget(id) {
      if (confirm('Are you sure you want to delete this budget?')) {
        try {
          await axios.delete(`/api/budgets/${id}/`)
          this.fetchBudgets()
        } catch (error) {
          console.error('Error deleting budget:', error)
        }
      }
    },
    
    resetForm() {
      this.form = {
        name: '',
        limit_amount: 0,
        period: 'monthly',
        custom_period_days: null,
        transaction_types: [],
        transaction_subtypes: []
      }
      this.editingBudget = null
    }
  }
}
</script>

<style scoped>
.budgets-page {
  padding: 2rem 0;
}

.budget-chart {
  display: flex;
  justify-content: center;
  align-items: center;
}

.spent {
  font-weight: bold;
  color: #dc3545;
}

.remaining {
  font-weight: bold;
  color: #28a745;
}

.percentage {
  font-weight: bold;
  color: #007bff;
}

.budget-info small, .budget-details small {
  font-size: 0.8rem;
}

.card {
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.modal {
  z-index: 1050;
}

.modal-backdrop {
  z-index: 1040;
}
</style>