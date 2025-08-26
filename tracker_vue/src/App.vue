<script setup>
 import Button from 'primevue/button';
 import AppNavigation from  './components/navigation';
 import AppFooter from  './components/footer';
 import TransactionTypeTable from './components/TransactionSubTypesTable.vue'
 </script> 
 
 <template>
  <div id="app">
      <AppNavigation />
        <TransactionTypeTable></TransactionTypeTable>
         <Button label="Placeholder"/>
      <AppFooter /> 
  </div>
</template>

