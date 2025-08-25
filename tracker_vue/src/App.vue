 <template>
  <div id="app">
      <AppNavigation />
         <!-- <img alt="Vue logo" src="./assets/logo.png"> -->
      <AppFooter /> 
  </div>
</template>
<script>
 import AppNavigation from  './components/navigation';
 import AppFooter from  './components/footer';
  export default {
    name: 'app',
    components: {
      AppNavigation,
      AppFooter,
    }
  }

 </script>
<style scoped>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
</style>
